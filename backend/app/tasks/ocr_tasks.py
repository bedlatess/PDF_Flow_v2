"""
OCR Processing Celery Tasks
处理 OCR 识别相关的异步任务
"""
import os
import tempfile
from typing import Optional, List
from celery import Task
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import logging

from app.celery_worker import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRTask(Task):
    """OCR 任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"OCR Task {task_id} failed: {exc}")


@celery_app.task(base=OCRTask, bind=True, max_retries=3)
def extract_text_task(
    self,
    file_path: str,
    language: str = "eng",
    pages: Optional[List[int]] = None,
    provider_config: Optional[dict] = None,
) -> dict:
    """
    从 PDF 或图片中提取文字（OCR）

    Args:
        file_path: 文件路径
        language: OCR 语言 (eng, chi_sim, etc.)
        pages: 要处理的页面列表，None 表示所有页面

    Returns:
        dict: 包含 success, text, page_texts, confidence
    """
    try:
        provider_config = provider_config or {}
        tesseract_path = str(provider_config.get("tesseract_path") or settings.TESSERACT_PATH or "").strip()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if not language:
            language = str(provider_config.get("default_language") or "eng")
        logger.info(f"Starting OCR for: {file_path} (language: {language})")

        # 判断文件类型
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".pdf":
            # PDF 文件：先转为图片
            images = convert_from_path(file_path, dpi=300)

            # 如果指定了页面，只处理这些页面
            if pages:
                images = [images[p - 1] for p in pages if 0 < p <= len(images)]
        else:
            # 图片文件：直接读取
            images = [Image.open(file_path)]

        # 对每一页进行 OCR
        page_texts = []
        total_confidence = 0

        for idx, image in enumerate(images):
            # 提取文本
            text = pytesseract.image_to_string(image, lang=language)

            # 获取详细信息（包括置信度）
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)

            # 计算平均置信度
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            page_texts.append({
                "page": idx + 1,
                "text": text.strip(),
                "confidence": round(avg_confidence, 2)
            })

            total_confidence += avg_confidence

        # 合并所有文本
        full_text = "\n\n".join([pt["text"] for pt in page_texts])
        avg_confidence = total_confidence / len(page_texts) if page_texts else 0

        logger.info(f"OCR completed: {len(page_texts)} pages, avg confidence: {avg_confidence:.2f}%")

        return {
            "success": True,
            "text": full_text,
            "page_texts": page_texts,
            "page_count": len(page_texts),
            "average_confidence": round(avg_confidence, 2),
            "language": language
        }

    except Exception as exc:
        logger.error(f"OCR extraction failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=OCRTask, bind=True, max_retries=3)
def batch_ocr_task(self, file_paths: List[str], language: str = "eng") -> dict:
    """
    批量 OCR 处理

    Args:
        file_paths: 文件路径列表
        language: OCR 语言

    Returns:
        dict: 包含每个文件的 OCR 结果
    """
    try:
        logger.info(f"Starting batch OCR for {len(file_paths)} files")

        results = []
        for file_path in file_paths:
            try:
                result = extract_text_task(file_path, language)
                results.append({
                    "file": os.path.basename(file_path),
                    "result": result
                })
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append({
                    "file": os.path.basename(file_path),
                    "error": str(e)
                })

        success_count = sum(1 for r in results if "result" in r and r["result"].get("success"))

        logger.info(f"Batch OCR completed: {success_count}/{len(file_paths)} successful")

        return {
            "success": True,
            "total": len(file_paths),
            "successful": success_count,
            "results": results
        }

    except Exception as exc:
        logger.error(f"Batch OCR failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
