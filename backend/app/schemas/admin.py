"""Schemas for hidden admin console APIs."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SiteSettingBase(BaseModel):
    value: str = ""
    value_type: str = Field(default="text", max_length=40)
    group: str = Field(default="general", max_length=80)
    label: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    is_public: bool = True


class SiteSettingUpdate(SiteSettingBase):
    pass


class SiteSettingResponse(SiteSettingBase):
    id: int
    key: str
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureFlagBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    enabled: bool = True
    requires_login: bool = False
    requires_pro: bool = False
    maintenance_message: Optional[str] = None


class FeatureFlagUpdate(FeatureFlagBase):
    pass


class FeatureFlagResponse(FeatureFlagBase):
    id: int
    key: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentBlockBase(BaseModel):
    locale: str = Field(default="zh", max_length=12)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""
    description: Optional[str] = None
    is_public: bool = True


class ContentBlockUpdate(ContentBlockBase):
    pass


class ContentBlockResponse(ContentBlockBase):
    id: int
    key: str
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminAuditLogResponse(BaseModel):
    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_key: str
    status: str
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class AdminUserUpdate(BaseModel):
    role: Optional[str] = Field(default=None, max_length=40)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class AdminJobResponse(BaseModel):
    id: int
    job_id: str
    user_id: int
    user_email: Optional[str]
    job_type: str
    status: str
    progress: int
    input_file_name: str
    input_file_size: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AdminOverviewResponse(BaseModel):
    settings_count: int
    feature_flags_count: int
    content_blocks_count: int
    users_count: int
    active_users_count: int
    admin_users_count: int
    jobs_count: int
    failed_jobs_count: int
    recent_audit_logs: list[AdminAuditLogResponse]
