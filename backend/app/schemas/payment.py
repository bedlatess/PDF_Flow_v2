"""
Pydantic schemas for payment and subscription
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CheckoutSessionCreate(BaseModel):
    """创建结账会话的请求。旧字段名保留给当前前端兼容。"""
    plan: str = Field(..., description="订阅计划: pro_monthly/pro_yearly，兼容 monthly/yearly")
    success_url: str = Field(..., description="支付成功后的回调URL")
    cancel_url: str = Field(..., description="取消支付后的回调URL")
    provider: str = Field(default="stripe", description="支付通道")


class CheckoutSessionResponse(BaseModel):
    """结账会话响应。兼容旧 checkout_url/session_id，同时暴露新订单字段。"""
    checkout_url: str = Field(..., description="托管结账页面URL")
    session_id: str = Field(..., description="兼容旧前端的订单ID")
    provider: str = Field(default="stripe")
    order_id: str
    merchant_order_id: str
    qr_code_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class PaymentCaptureResponse(BaseModel):
    provider: str
    order_id: str
    merchant_order_id: str
    status: str
    current_period_end: Optional[datetime] = None


class PaymentProviderOption(BaseModel):
    key: str
    enabled: bool
    display_name: str
    settlement: str
    supports_subscription: bool
    supports_one_time: bool


class PaymentProviderList(BaseModel):
    providers: list[PaymentProviderOption]


class SubscriptionResponse(BaseModel):
    """订阅信息响应"""
    has_subscription: bool
    status: Optional[str] = None  # active, past_due, canceled, etc.
    plan: Optional[str] = None  # price_id
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class WebhookEvent(BaseModel):
    """Stripe Webhook事件"""
    type: str
    data: dict
