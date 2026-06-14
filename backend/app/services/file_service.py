"""
File Processing Service
文件处理业务逻辑层
"""
import os
import time
import uuid
from typing import Optional, List, Dict
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from redis import Redis
import json
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.utils.file_utils import FileManager, FileValidator
from app.tasks.pdf_tasks import (
    merge_pdfs_task,
    split_pdf_task,
    compress_pdf_task,
    rotate_pdf_task,
    convert_images_to_pdf_task,
    convert_pdf_to_images_task,
)
from app.domains.service_provider.config_store import get_service_provider_runtime_config
from app.domains.jobs.service import (
    build_pending_job_status,
    job_lifecycle,
    job_status_reader,
    merge_celery_state_into_status,
)
from app.domains.jobs.types import is_terminal_job_status
from app.tasks.ocr_tasks import extract_text_task
from app.services.file_retention_service import file_retention_service

logger = logging.getLogger(__name__)


class FileProcessingService:
    """文件处理服务"""

    def __init__(self):
        self.file_manager = FileManager()
        self.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._db_session_factory = None
        self.file_ttl = 3600  # 文件在 Redis 中的 TTL（1小时）

    def _generate_file_id(self) -> str:
        """生成唯一的文件 ID"""
        return f"file_{uuid.uuid4().hex[:12]}"

    def _generate_job_id(self) -> str:
        """生成唯一的任务 ID"""
        return f"job_{uuid.uuid4().hex[:12]}"

    def _service_provider_runtime_config(self, service_key: str, provider_key: str) -> dict | None:
        try:
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                return get_service_provider_runtime_config(db, service_key, provider_key)
            finally:
                db.close()
        except Exception as exc:
            logger.warning(
                "Service provider config fallback for %s/%s: %s",
                service_key,
                provider_key,
                exc,
            )
            return None

    async def upload_file(
        self,
        file: UploadFile,
        user_tier: str = "free"
    ) -> Dict:
        """
        上传文件

        Args:
            file: 上传的文件
            user_tier: 用户等级 (free, pro, enterprise)

        Returns:
            文件信息字典
        """
        # 验证文件
        file_retention_service.cleanup_if_due()
        max_size = FileValidator.MAX_FILE_SIZE.get(user_tier, FileValidator.MAX_FILE_SIZE["free"])
        is_valid, error_msg = await FileValidator.validate_file(file, max_size)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 生成文件 ID
        file_id = self._generate_file_id()

        # 创建临时目录
        temp_dir = self.file_manager.create_temp_dir(prefix=f"{file_id}_")

        # 保存文件
        file_path = temp_dir / file.filename
        await self.file_manager.save_upload_file(file, file_path)

        # 获取文件信息
        file_info = self.file_manager.get_file_info(file_path)

        # 存储文件元数据到 Redis
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "filepath": str(file_path),
            "size": file_info["size"],
            "mime_type": file.content_type,
            "upload_time": time.time(),
            "user_tier": user_tier
        }

        # 保存到 Redis（带 TTL）
        self.redis_client.setex(
            f"file:{file_id}",
            self.file_ttl,
            json.dumps(file_metadata)
        )

        logger.info(f"File uploaded: {file_id} - {file.filename}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": file_info["size"],
            "mime_type": file.content_type,
            "upload_time": file_metadata["upload_time"]
        }

    def _get_file_path(self, file_id: str) -> Path:
        """Return an uploaded file path from Redis metadata."""
        metadata = self._get_file_metadata(file_id)
        file_path = Path(metadata["filepath"])

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File no longer exists: {file_id}"
            )

        return file_path

    def _get_file_metadata(self, file_id: str) -> Dict:
        """Return uploaded file metadata from Redis without changing its shape."""
        file_data = self.redis_client.get(f"file:{file_id}")

        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}"
            )

        return json.loads(file_data)

    def _get_path_from_metadata(self, file_id: str, metadata: Dict) -> Path:
        """Return a validated uploaded path from an already-loaded metadata record."""
        file_path = Path(metadata["filepath"])
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File no longer exists: {file_id}"
            )
        return file_path

    def _save_job_status(self, job_id: str, status_data: Dict):
        """保存任务状态到 Redis"""
        self.redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps(status_data)
        )

    def _create_pending_processing_job(
        self,
        *,
        job_id: str,
        job_type: str,
        file_metadata: Dict | List[Dict],
        db: Session | None = None,
    ) -> None:
        """Best-effort durable job creation while Redis remains active state."""
        metadata_items = file_metadata if isinstance(file_metadata, list) else [file_metadata]
        names = [
            str(item.get("filename") or Path(str(item.get("filepath") or "")).name or "input")
            for item in metadata_items
        ]
        total_size = sum(int(item.get("size") or 0) for item in metadata_items)
        input_file_name = names[0] if len(names) == 1 else ", ".join(names[:3])
        if len(names) > 3:
            input_file_name = f"{input_file_name}, +{len(names) - 3} more"

        job_lifecycle.create_pending(
            job_id=job_id,
            user_id=None,
            job_type=job_type,
            input_file_name=input_file_name,
            input_file_size=total_size,
            db=db,
        )

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """获取任务状态

        优先读取 Redis 中的初始记录，再用 Celery AsyncResult 补充真实执行状态。
        Celery 完成后会把 task 返回值（含 output_path / output_files）写入结果后端，
        据此把状态更新为 completed 并回填结果，前端轮询才能看到完成。
        """
        job_data = self.redis_client.get(f"job:{job_id}")
        if not job_data:
            return self._get_durable_job_status(job_id)

        status_data = json.loads(job_data)

        # 若 Redis 中已是终态（completed/failed），直接信任，不再被 Celery 覆盖
        # （Celery 结果可能已过期，AsyncResult 会退回 PENDING，不能据此降级）
        if is_terminal_job_status(status_data.get("status")):
            return status_data

        # 否则结合 Celery 执行状态
        try:
            from celery.result import AsyncResult
            from app.celery_worker import celery_app

            async_result = AsyncResult(job_id, app=celery_app)
            celery_state = async_result.state  # PENDING / STARTED / SUCCESS / FAILURE / RETRY

            status_data = merge_celery_state_into_status(
                status_data,
                celery_state=celery_state,
                celery_result=async_result.result,
            )
        except Exception as e:  # Celery 不可用时降级为 Redis 原始记录
            logger.warning(f"Celery status lookup failed for {job_id}: {e}")

        return status_data

    def _get_durable_job_status(self, job_id: str) -> Optional[Dict]:
        """Fallback to DB durable status only when Redis active state is absent."""
        return job_status_reader.route_status(
            job_id,
            session_factory=self._db_session_factory,
        )

    def cancel_job(self, job_id: str) -> Dict:
        """Cancel a queued or running processing job.

        Redis remains the source of truth for currently active jobs. Celery
        revocation is best-effort because the worker may be unavailable in
        local or test environments.
        """
        status_data = self.get_job_status(job_id)
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )

        job_status = status_data.get("status")
        if job_status == "cancelled":
            return status_data
        if job_status in ("completed", "failed"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Job cannot be cancelled after status: {job_status}"
            )

        try:
            from celery.result import AsyncResult
            from app.celery_worker import celery_app

            AsyncResult(job_id, app=celery_app).revoke(terminate=True)
        except Exception as e:
            logger.warning(f"Celery revoke failed for {job_id}: {e}")

        now = time.time()
        status_data.update({
            "status": "cancelled",
            "progress": status_data.get("progress") or 0,
            "updated_at": now,
            "error": "Job cancelled by user",
        })
        self._save_job_status(job_id, status_data)
        return status_data

    def get_download_path(self, job_id: str) -> Path:
        """获取已完成任务的可下载文件路径

        - 单文件结果（merge/compress/rotate/images-to-pdf）：直接返回 output_path
        - 多文件结果（split/pdf-to-images）：打包为 zip 返回
        - OCR：将提取文本写入 .txt 返回

        Raises:
            HTTPException: 任务不存在 / 未完成 / 无可下载产物
        """
        file_retention_service.cleanup_if_due()
        status_data = self.get_job_status(job_id)
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )

        job_status = status_data.get("status")
        if job_status == "failed":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=status_data.get("error", "Job failed")
            )
        if job_status != "completed":
            # 425 Too Early：任务仍在处理中
            raise HTTPException(
                status_code=425,
                detail=f"Job not completed yet (status: {job_status})"
            )

        result = status_data.get("result") or {}

        # 单文件
        output_path = result.get("output_path")
        if output_path and os.path.exists(output_path):
            return Path(output_path)

        # 多文件 -> 打包 zip
        output_files = result.get("output_files")
        if output_files:
            existing = [f for f in output_files if os.path.exists(f)]
            if existing:
                import zipfile
                zip_dir = self.file_manager.create_temp_dir(prefix="download_")
                zip_path = zip_dir / f"{job_id}.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in existing:
                        zf.write(f, arcname=os.path.basename(f))
                return zip_path

        # OCR 文本结果
        if "text" in result:
            txt_dir = self.file_manager.create_temp_dir(prefix="download_")
            txt_path = txt_dir / f"{job_id}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(result.get("text", ""))
            return txt_path

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No downloadable output for this job"
        )

    async def merge_pdfs(
        self,
        file_ids: List[str],
        output_filename: Optional[str] = None,
        db: Session | None = None,
    ) -> Dict:
        """合并 PDF 文件"""
        # 获取所有文件路径
        file_metadata = [self._get_file_metadata(fid) for fid in file_ids]
        file_paths = [
            str(self._get_path_from_metadata(file_id, metadata))
            for file_id, metadata in zip(file_ids, file_metadata)
        ]

        # 创建输出目录
        output_dir = self.file_manager.create_temp_dir(prefix="merge_")
        output_path = output_dir / (output_filename or "merged.pdf")

        # 创建任务 ID
        job_id = self._generate_job_id()

        # 保存初始任务状态
        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="merge_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交 Celery 任务
        task = merge_pdfs_task.apply_async(
            args=[file_paths, str(output_path)],
            task_id=job_id
        )

        logger.info(f"Merge job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "PDF merge job queued"
        }

    async def split_pdf(
        self,
        file_id: str,
        page_ranges: List[List[int]],
        db: Session | None = None,
    ) -> Dict:
        """拆分 PDF 文件"""
        file_metadata = self._get_file_metadata(file_id)
        file_path = str(self._get_path_from_metadata(file_id, file_metadata))

        # 转换页面范围格式
        ranges_tuples = [(r[0], r[1]) for r in page_ranges]

        # 创建输出目录
        output_dir = self.file_manager.create_temp_dir(prefix="split_")

        # 创建任务
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="split_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交任务
        task = split_pdf_task.apply_async(
            args=[file_path, ranges_tuples, str(output_dir)],
            task_id=job_id
        )

        logger.info(f"Split job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "PDF split job queued"
        }

    async def compress_pdf(self, file_id: str, quality: str = "medium", db: Session | None = None) -> Dict:
        """Compress a PDF file."""
        file_metadata = self._get_file_metadata(file_id)
        file_path_obj = Path(file_metadata["filepath"])
        if not file_path_obj.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File no longer exists: {file_id}"
            )
        file_path = str(file_path_obj)

        # Create output path.
        output_dir = self.file_manager.create_temp_dir(prefix="compress_")
        output_path = output_dir / "compressed.pdf"

        # Create the legacy Redis/Celery job and optional durable DB record.
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="compress_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # Submit the existing Celery task.
        task = compress_pdf_task.apply_async(
            args=[file_path, str(output_path), quality],
            task_id=job_id
        )

        logger.info(f"Compress job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "PDF compression job queued"
        }

    async def rotate_pdf(
        self,
        file_id: str,
        rotation: int,
        db: Session | None = None,
    ) -> Dict:
        """旋转 PDF 页面"""
        file_metadata = self._get_file_metadata(file_id)
        file_path = str(self._get_path_from_metadata(file_id, file_metadata))

        # 创建输出路径
        output_dir = self.file_manager.create_temp_dir(prefix="rotate_")
        output_path = output_dir / "rotated.pdf"

        # 创建任务
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="rotate_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交任务
        task = rotate_pdf_task.apply_async(
            args=[file_path, str(output_path), rotation],
            task_id=job_id
        )

        logger.info(f"Rotate job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "PDF rotation job queued"
        }

    async def images_to_pdf(
        self,
        file_ids: List[str],
        output_filename: Optional[str] = None,
        db: Session | None = None,
    ) -> Dict:
        """图片转 PDF"""
        file_metadata = [self._get_file_metadata(fid) for fid in file_ids]
        file_paths = [
            str(self._get_path_from_metadata(file_id, metadata))
            for file_id, metadata in zip(file_ids, file_metadata)
        ]

        # 创建输出路径
        output_dir = self.file_manager.create_temp_dir(prefix="img2pdf_")
        output_path = output_dir / (output_filename or "converted.pdf")

        # 创建任务
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="image_to_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交任务
        task = convert_images_to_pdf_task.apply_async(
            args=[file_paths, str(output_path)],
            task_id=job_id
        )

        logger.info(f"Images to PDF job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Image to PDF conversion job queued"
        }

    async def pdf_to_images(
        self,
        file_id: str,
        format: str = "png",
        db: Session | None = None,
    ) -> Dict:
        """PDF 转图片"""
        file_metadata = self._get_file_metadata(file_id)
        file_path = str(self._get_path_from_metadata(file_id, file_metadata))

        # 创建输出目录
        output_dir = self.file_manager.create_temp_dir(prefix="pdf2img_")

        # 创建任务
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="pdf_to_image",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交任务
        task = convert_pdf_to_images_task.apply_async(
            args=[file_path, str(output_dir), format],
            task_id=job_id
        )

        logger.info(f"PDF to images job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "PDF to images conversion job queued"
        }

    async def extract_text_ocr(
        self,
        file_id: str,
        language: str = "eng",
        db: Session | None = None,
    ) -> Dict:
        """OCR 文本提取"""
        file_metadata = self._get_file_metadata(file_id)
        file_path = str(self._get_path_from_metadata(file_id, file_metadata))
        runtime_config = self._service_provider_runtime_config("ocr", "local_tesseract")
        public_config = runtime_config.get("public_config") if runtime_config else {}
        requested_language = language or public_config.get("default_language") or "eng"
        languages = [
            item.strip()
            for item in str(public_config.get("languages") or "").split(",")
            if item.strip()
        ]
        if languages and requested_language not in languages:
            requested_language = str(public_config.get("default_language") or languages[0])

        # 创建任务
        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="ocr_pdf",
            file_metadata=file_metadata,
            db=db,
        )

        # 提交任务
        task = extract_text_task.apply_async(
            args=[file_path, requested_language, None, public_config or None],
            task_id=job_id
        )

        logger.info(f"OCR job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "OCR job queued"
        }

    async def office_to_pdf(self, file: UploadFile, db: Session | None = None) -> Dict:
        """Office to PDF conversion"""
        from app.utils.file_utils import save_upload_file
        from app.tasks.office_tasks import office_to_pdf_task

        input_path = await save_upload_file(file)
        output_filename = os.path.splitext(file.filename)[0] + ".pdf"
        output_path = os.path.join(os.path.dirname(input_path), output_filename)
        runtime_config = self._service_provider_runtime_config("office", "local_libreoffice")
        public_config = runtime_config.get("public_config") if runtime_config else {}

        job_id = self._generate_job_id()

        self._save_job_status(job_id, build_pending_job_status(job_id))
        self._create_pending_processing_job(
            job_id=job_id,
            job_type="office_to_pdf",
            file_metadata={
                "filename": file.filename or os.path.basename(input_path),
                "filepath": input_path,
                "size": os.path.getsize(input_path) if os.path.exists(input_path) else 0,
            },
            db=db,
        )

        office_to_pdf_task.apply_async(
            args=[input_path, output_path, public_config or None],
            task_id=job_id
        )

        logger.info(f"Office to PDF job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Office to PDF job queued"
        }


# 全局服务实例
file_processing_service = FileProcessingService()
