"""
Office to PDF Conversion Celery Tasks
处理 Office 文件转 PDF 的异步任务
"""
import os
import tempfile
from typing import Optional
from celery import Task
import logging
from pathlib import Path

from app.celery_worker import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


def _office_binary(provider_config: Optional[dict] = None) -> str:
    return str((provider_config or {}).get("binary_path") or "libreoffice").strip() or "libreoffice"


def _office_timeout(provider_config: Optional[dict] = None) -> int:
    try:
        return max(1, int((provider_config or {}).get("timeout_seconds") or 60))
    except (TypeError, ValueError):
        return 60


class OfficeTask(Task):
    """Office 转换任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"Office Task {task_id} failed: {exc}")


@celery_app.task(base=OfficeTask, bind=True, max_retries=3)
def docx_to_pdf_task(
    self,
    input_path: str,
    output_path: Optional[str] = None,
    provider_config: Optional[dict] = None,
) -> dict:
    """
    将 Word 文档转换为 PDF

    注意：需要安装 LibreOffice 或使用云服务API
    本实现使用 LibreOffice 命令行工具

    Args:
        input_path: 输入 DOCX 文件路径
        output_path: 输出 PDF 文件路径（可选）

    Returns:
        dict: 包含 success, output_path, error
    """
    try:
        logger.info(f"Starting DOCX to PDF conversion: {input_path}")

        # 验证输入文件
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 确定输出路径
        if output_path is None:
            output_dir = os.path.dirname(input_path)
            output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
            output_path = os.path.join(output_dir, output_filename)

        # 使用 LibreOffice 转换
        # 需要系统安装: apt-get install libreoffice
        import subprocess

        output_dir = os.path.dirname(output_path)

        # LibreOffice 命令
        cmd = [
            _office_binary(provider_config),
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_office_timeout(provider_config)
        )

        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        # LibreOffice 输出文件名可能不同，需要重命名
        generated_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        generated_path = os.path.join(output_dir, generated_filename)

        if generated_path != output_path and os.path.exists(generated_path):
            os.rename(generated_path, output_path)

        if not os.path.exists(output_path):
            raise Exception("PDF file not generated")

        file_size = os.path.getsize(output_path)

        logger.info(f"DOCX to PDF conversion completed: {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "output_path": output_path,
            "file_size": file_size,
            "error": None
        }

    except Exception as e:
        logger.error(f"DOCX to PDF conversion failed: {str(e)}")

        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)

        return {
            "success": False,
            "output_path": None,
            "file_size": 0,
            "error": str(e)
        }


@celery_app.task(base=OfficeTask, bind=True, max_retries=3)
def xlsx_to_pdf_task(
    self,
    input_path: str,
    output_path: Optional[str] = None,
    provider_config: Optional[dict] = None,
) -> dict:
    """
    将 Excel 表格转换为 PDF

    Args:
        input_path: 输入 XLSX 文件路径
        output_path: 输出 PDF 文件路径（可选）

    Returns:
        dict: 包含 success, output_path, error
    """
    try:
        logger.info(f"Starting XLSX to PDF conversion: {input_path}")

        # 验证输入文件
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 确定输出路径
        if output_path is None:
            output_dir = os.path.dirname(input_path)
            output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
            output_path = os.path.join(output_dir, output_filename)

        # 使用 LibreOffice 转换
        import subprocess

        output_dir = os.path.dirname(output_path)

        cmd = [
            _office_binary(provider_config),
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_office_timeout(provider_config)
        )

        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        # 处理输出文件名
        generated_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        generated_path = os.path.join(output_dir, generated_filename)

        if generated_path != output_path and os.path.exists(generated_path):
            os.rename(generated_path, output_path)

        if not os.path.exists(output_path):
            raise Exception("PDF file not generated")

        file_size = os.path.getsize(output_path)

        logger.info(f"XLSX to PDF conversion completed: {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "output_path": output_path,
            "file_size": file_size,
            "error": None
        }

    except Exception as e:
        logger.error(f"XLSX to PDF conversion failed: {str(e)}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)

        return {
            "success": False,
            "output_path": None,
            "file_size": 0,
            "error": str(e)
        }


@celery_app.task(base=OfficeTask, bind=True, max_retries=3)
def pptx_to_pdf_task(
    self,
    input_path: str,
    output_path: Optional[str] = None,
    provider_config: Optional[dict] = None,
) -> dict:
    """
    将 PowerPoint 演示文稿转换为 PDF

    Args:
        input_path: 输入 PPTX 文件路径
        output_path: 输出 PDF 文件路径（可选）

    Returns:
        dict: 包含 success, output_path, error
    """
    try:
        logger.info(f"Starting PPTX to PDF conversion: {input_path}")

        # 验证输入文件
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 确定输出路径
        if output_path is None:
            output_dir = os.path.dirname(input_path)
            output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
            output_path = os.path.join(output_dir, output_filename)

        # 使用 LibreOffice 转换
        import subprocess

        output_dir = os.path.dirname(output_path)

        cmd = [
            _office_binary(provider_config),
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_office_timeout(provider_config)
        )

        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        # 处理输出文件名
        generated_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        generated_path = os.path.join(output_dir, generated_filename)

        if generated_path != output_path and os.path.exists(generated_path):
            os.rename(generated_path, output_path)

        if not os.path.exists(output_path):
            raise Exception("PDF file not generated")

        file_size = os.path.getsize(output_path)

        logger.info(f"PPTX to PDF conversion completed: {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "output_path": output_path,
            "file_size": file_size,
            "error": None
        }

    except Exception as e:
        logger.error(f"PPTX to PDF conversion failed: {str(e)}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)

        return {
            "success": False,
            "output_path": None,
            "file_size": 0,
            "error": str(e)
        }


@celery_app.task(base=OfficeTask, bind=True, max_retries=3)
def office_to_pdf_task(
    self,
    input_path: str,
    output_path: Optional[str] = None,
    provider_config: Optional[dict] = None,
) -> dict:
    """
    通用 Office 文件转 PDF（自动检测文件类型）

    Args:
        input_path: 输入文件路径
        output_path: 输出 PDF 文件路径（可选）

    Returns:
        dict: 包含 success, output_path, error
    """
    try:
        # 检测文件类型
        file_ext = os.path.splitext(input_path)[1].lower()

        if file_ext in ['.docx', '.doc']:
            return docx_to_pdf_task(input_path, output_path, provider_config)
        elif file_ext in ['.xlsx', '.xls']:
            return xlsx_to_pdf_task(input_path, output_path, provider_config)
        elif file_ext in ['.pptx', '.ppt']:
            return pptx_to_pdf_task(input_path, output_path, provider_config)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    except Exception as e:
        logger.error(f"Office to PDF conversion failed: {str(e)}")
        return {
            "success": False,
            "output_path": None,
            "file_size": 0,
            "error": str(e)
        }
