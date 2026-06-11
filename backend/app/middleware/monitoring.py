"""
FastAPI middleware for monitoring and analytics
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.error_log_service import log_api_error
from app.services.monitoring_service import get_monitoring_service


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track requests and performance"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)

        # Track page view for authenticated users
        if user_id:
            monitoring = get_monitoring_service()
            monitoring.track_page_view(
                user_id=str(user_id),
                page=request.url.path,
                properties={
                    'method': request.method,
                    'user_agent': request.headers.get('user-agent')
                }
            )

        try:
            # Process request
            response = await call_next(request)

            # Track performance
            duration_ms = (time.time() - start_time) * 1000
            monitoring = get_monitoring_service()
            monitoring.track_performance(
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                success=response.status_code < 400,
                metadata={
                    'status_code': response.status_code,
                    'user_id': user_id
                }
            )

            if response.status_code >= 500:
                log_api_error(
                    request=request,
                    status_code=response.status_code,
                    error_message=f"HTTP {response.status_code}",
                )

            return response

        except Exception as e:
            # Track error
            duration_ms = (time.time() - start_time) * 1000
            monitoring = get_monitoring_service()

            monitoring.capture_exception(
                error=e,
                context={
                    'path': request.url.path,
                    'method': request.method,
                    'duration_ms': duration_ms
                },
                user={'id': user_id} if user_id else None
            )

            log_api_error(
                request=request,
                status_code=500,
                error=e,
            )

            # Re-raise to let FastAPI handle it
            raise
