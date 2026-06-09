"""
File Handling Utilities
文件处理工具函数
"""
import os
import hashlib
import magic
import tempfile
from typing import Optional, List
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import logging
from app.core.config import settings

# Import PDF text extraction
try:
    from app.utils.pdf_text_extractor import extract_text_from_pdf
except ImportError:
    extract_text_from_pdf = None

logger = logging.getLogger(__name__)


class FileValidator:
    """文件验证器 - 使用魔术数字进行文件类型检测"""

    # 允许的文件类型（MIME types）
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/tiff",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",  # .xls
        "application/msword",  # .doc
    }

    # 文件大小限制（字节）
    MAX_FILE_SIZE = {
        "free": 20 * 1024 * 1024,  # 20MB for free tier
        "pro": 500 * 1024 * 1024,  # 500MB for pro tier
        "enterprise": 2 * 1024 * 1024 * 1024,  # 2GB for enterprise
    }

    @staticmethod
    async def validate_file(
        file: UploadFile,
        max_size: int,
        allowed_types: Optional[set] = None
    ) -> tuple[bool, Optional[str]]:
        """
        验证上传的文件

        Args:
            file: 上传的文件对象
            max_size: 最大文件大小（字节）
            allowed_types: 允许的 MIME 类型集合

        Returns:
            (is_valid, error_message)
        """
        if allowed_types is None:
            allowed_types = FileValidator.ALLOWED_MIME_TYPES

        # 读取文件头部（用于魔术数字检测）
        header = await file.read(2048)
        await file.seek(0)  # 重置文件指针

        # 1. 检测真实文件类型（基于魔术数字）
        try:
            mime_type = magic.from_buffer(header, mime=True)
        except Exception as e:
            logger.error(f"Failed to detect MIME type: {e}")
            return False, "Failed to detect file type"

        # 2. 验证文件类型
        if mime_type not in allowed_types:
            return False, f"File type not allowed: {mime_type}"

        # 3. 验证文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        await file.seek(0)  # 重置文件指针

        if file_size > max_size:
            return False, f"File too large: {file_size} bytes (max: {max_size})"

        if file_size == 0:
            return False, "Empty file"

        return True, None

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """计算文件的哈希值"""
        hash_func = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()


class FileManager:
    """文件管理器 - 处理文件的存储和清理"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化文件管理器

        Args:
            base_dir: 基础存储目录，None 则使用系统临时目录
        """
        if base_dir:
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Use the configured upload directory so backend and worker share files
            # through the mounted Docker volume (`/tmp/pdf-flow/...`).
            self.base_dir = Path(settings.UPLOAD_DIR)
            self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileManager initialized with base_dir: {self.base_dir}")

    def create_temp_dir(self, prefix: str = "upload_") -> Path:
        """创建临时目录"""
        temp_dir = self.base_dir / f"{prefix}{os.urandom(8).hex()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    async def save_upload_file(
        self,
        file: UploadFile,
        destination: Path,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> Path:
        """
        保存上传的文件

        Args:
            file: 上传的文件对象
            destination: 目标路径
            chunk_size: 分块大小

        Returns:
            保存后的文件路径
        """
        try:
            # 确保目标目录存在
            destination.parent.mkdir(parents=True, exist_ok=True)

            # 分块写入文件
            with open(destination, "wb") as f:
                while chunk := await file.read(chunk_size):
                    f.write(chunk)

            logger.info(f"File saved: {destination}")
            return destination

        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            # 清理部分写入的文件
            if destination.exists():
                destination.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    def cleanup_directory(self, directory: Path):
        """清理目录及其所有内容"""
        try:
            if directory.exists() and directory.is_dir():
                for item in directory.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        self.cleanup_directory(item)
                directory.rmdir()
                logger.info(f"Cleaned up directory: {directory}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {directory}: {e}")

    def cleanup_file(self, file_path: Path):
        """清理单个文件"""
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")

    def get_file_info(self, file_path: Path) -> dict:
        """获取文件信息"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()

        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": file_path.suffix,
        }


# 全局文件管理器实例
file_manager = FileManager()


async def save_upload_file(file: UploadFile, destination: Optional[Path] = None) -> str:
    """
    Compatibility wrapper for legacy call sites.

    If destination is omitted, create a temp directory and preserve the original filename.
    Returns the saved file path as a string.
    """
    if destination is None:
        temp_dir = file_manager.create_temp_dir(prefix="office_")
        destination = temp_dir / file.filename

    saved_path = await file_manager.save_upload_file(file, destination)
    return str(saved_path)
