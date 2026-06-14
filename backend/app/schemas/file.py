"""
File Processing Schemas
文件处理相关的数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum


class FileType(str, Enum):
    """文件类型枚举"""
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityLevel(str, Enum):
    """质量级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImageFormat(str, Enum):
    """图片格式枚举"""
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="MIME 类型")
    upload_time: float = Field(..., description="上传时间戳")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "a1b2c3d4e5f6",
                "filename": "document.pdf",
                "size": 1048576,
                "mime_type": "application/pdf",
                "upload_time": 1234567890.123
            }
        }
    )

class PDFMergeRequest(BaseModel):
    """PDF 合并请求"""
    file_ids: List[str] = Field(..., min_length=2, description="要合并的文件 ID 列表")
    output_filename: Optional[str] = Field(None, description="输出文件名")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_ids": ["file1_id", "file2_id", "file3_id"],
                "output_filename": "merged.pdf"
            }
        }
    )


class PDFSplitRequest(BaseModel):
    """PDF 拆分请求"""
    file_id: str = Field(..., description="PDF 文件 ID")
    page_ranges: List[List[int]] = Field(
        ...,
        description="页面范围列表，例如 [[1,3], [5,7]] 表示提取 1-3 页和 5-7 页"
    )

    @field_validator("page_ranges")
    @classmethod
    def validate_page_ranges(cls, v):
        for range_item in v:
            if len(range_item) != 2:
                raise ValueError("Each range must have exactly 2 elements [start, end]")
            if range_item[0] > range_item[1]:
                raise ValueError("Start page must be <= end page")
            if range_item[0] < 1:
                raise ValueError("Page numbers must start from 1")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "page_ranges": [[1, 3], [5, 7]]
            }
        }
    )


class PDFCompressRequest(BaseModel):
    """PDF 压缩请求"""
    file_id: str = Field(..., description="PDF 文件 ID")
    quality: QualityLevel = Field(QualityLevel.MEDIUM, description="压缩质量级别")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "quality": "medium"
            }
        }
    )


class PDFRotateRequest(BaseModel):
    """PDF 旋转请求"""
    file_id: str = Field(..., description="PDF 文件 ID")
    rotation: int = Field(..., description="旋转角度（90, 180, 270）")
    pages: Optional[List[int]] = Field(None, description="要旋转的页面，None 表示所有页面")

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, v):
        if v not in [90, 180, 270]:
            raise ValueError("Rotation must be 90, 180, or 270 degrees")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "rotation": 90,
                "pages": [1, 3, 5]
            }
        }
    )


class ImageToPDFRequest(BaseModel):
    """图片转 PDF 请求"""
    file_ids: List[str] = Field(..., min_length=1, description="图片文件 ID 列表")
    output_filename: Optional[str] = Field("converted.pdf", description="输出文件名")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_ids": ["img1_id", "img2_id"],
                "output_filename": "images.pdf"
            }
        }
    )


class PDFToImageRequest(BaseModel):
    """PDF 转图片请求"""
    file_id: str = Field(..., description="PDF 文件 ID")
    format: ImageFormat = Field(ImageFormat.PNG, description="输出图片格式")
    pages: Optional[List[int]] = Field(None, description="要转换的页面，None 表示所有页面")
    dpi: int = Field(300, ge=72, le=600, description="输出 DPI")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "format": "png",
                "pages": [1, 2, 3],
                "dpi": 300
            }
        }
    )


class OCRRequest(BaseModel):
    """OCR 识别请求"""
    file_id: str = Field(..., description="文件 ID（PDF 或图片）")
    language: str = Field("eng", description="OCR 语言（eng, chi_sim, etc.）")
    pages: Optional[List[int]] = Field(None, description="要识别的页面，None 表示所有页面")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "language": "eng",
                "pages": [1, 2]
            }
        }
    )


class HTMLToPDFRequest(BaseModel):
    """HTML to PDF conversion request."""

    mode: str = Field("url", description="Input mode: url or html")
    url: Optional[str] = Field(None, max_length=2048, description="Public http/https URL")
    html: Optional[str] = Field(None, description="Raw HTML content")
    page_size: str = Field("A4", description="Page size: A4, Letter, or Legal")
    orientation: str = Field("portrait", description="Page orientation: portrait or landscape")
    margin: str = Field("normal", description="Margin preset: none, narrow, normal, or wide")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value):
        if value not in {"url", "html"}:
            raise ValueError("mode must be url or html")
        return value

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, value):
        if value not in {"A4", "Letter", "Legal"}:
            raise ValueError("page_size must be A4, Letter, or Legal")
        return value

    @field_validator("orientation")
    @classmethod
    def validate_orientation(cls, value):
        if value not in {"portrait", "landscape"}:
            raise ValueError("orientation must be portrait or landscape")
        return value

    @field_validator("margin")
    @classmethod
    def validate_margin(cls, value):
        if value not in {"none", "narrow", "normal", "wide"}:
            raise ValueError("margin must be none, narrow, normal, or wide")
        return value


class ProcessingJobResponse(BaseModel):
    """处理任务响应"""
    job_id: str = Field(..., description="任务 ID")
    status: ProcessingStatus = Field(..., description="任务状态")
    message: Optional[str] = Field(None, description="状态消息")
    progress: Optional[float] = Field(None, ge=0, le=100, description="进度百分比")
    result_url: Optional[str] = Field(None, description="结果下载链接")
    error: Optional[str] = Field(None, description="错误信息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_abc123",
                "status": "processing",
                "message": "Processing PDF...",
                "progress": 45.5,
                "result_url": None,
                "error": None
            }
        }
    )


class ProcessingJobStatusResponse(BaseModel):
    """处理任务状态查询响应"""
    job_id: str
    status: ProcessingStatus
    created_at: float
    updated_at: float
    progress: Optional[float] = None
    result: Optional[dict] = None
    error: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_abc123",
                "status": "completed",
                "created_at": 1234567890.123,
                "updated_at": 1234567895.456,
                "progress": 100,
                "result": {
                    "output_files": ["result.pdf"],
                    "file_size": 1048576
                },
                "error": None
            }
        }
    )


class ProcessingJobHistoryItem(BaseModel):
    """Account-owned processing job history row."""

    job_id: str
    job_type: str
    status: ProcessingStatus
    progress: int = Field(0, ge=0, le=100)
    input_file_name: str
    input_file_size: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_state: str
    download_available: bool
    error_message: Optional[str] = None


class ProcessingJobHistoryListResponse(BaseModel):
    """Paginated account-owned processing job history."""

    items: List[ProcessingJobHistoryItem]
    total: int
    limit: int
    offset: int
