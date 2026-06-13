"""
Monitoring and analytics integration
Sentry for error tracking, PostHog for user analytics
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime


class MonitoringService:
    """Centralized monitoring and analytics service"""

    def __init__(self):
        self.sentry_enabled = False
        self.posthog_enabled = False
        self._init_sentry()
        self._init_posthog()

    def _init_sentry(self):
        """Initialize Sentry for error tracking"""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from app.core.config import settings

            if settings.SENTRY_DSN:
                sentry_sdk.init(
                    dsn=settings.SENTRY_DSN,
                    environment=settings.ENVIRONMENT,
                    release=f"{settings.PROJECT_NAME}@{settings.VERSION}",
                    traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
                    profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
                    integrations=[
                        FastApiIntegration(),
                        SqlalchemyIntegration(),
                    ],
                    # Filter out sensitive data
                    before_send=self._sentry_before_send,
                )
                self.sentry_enabled = True
                print(f"Sentry initialized (env: {settings.ENVIRONMENT})")
        except ImportError:
            print("Sentry SDK not installed")
        except Exception as e:
            print(f"Failed to initialize Sentry: {e}")

    def _init_posthog(self):
        """Initialize PostHog for user analytics"""
        try:
            from posthog import Posthog
            from app.core.config import settings

            if settings.POSTHOG_API_KEY:
                self.posthog = Posthog(
                    project_api_key=settings.POSTHOG_API_KEY,
                    host='https://app.posthog.com'
                )
                self.posthog_enabled = True
                print("PostHog initialized")
        except ImportError:
            print("PostHog SDK not installed")
        except Exception as e:
            print(f"Failed to initialize PostHog: {e}")

    def _sentry_before_send(self, event, hint):
        """Filter sensitive data before sending to Sentry"""
        # Remove authorization headers
        if 'request' in event and 'headers' in event['request']:
            headers = event['request']['headers']
            if 'Authorization' in headers:
                headers['Authorization'] = '[Filtered]'
            if 'Cookie' in headers:
                headers['Cookie'] = '[Filtered]'

        # Remove sensitive POST data
        if 'request' in event and 'data' in event['request']:
            data = event['request']['data']
            sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credit_card']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '[Filtered]'

        return event

    # ============================================================================
    # Error Tracking (Sentry)
    # ============================================================================

    def capture_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[Dict[str, Any]] = None
    ):
        """Capture an exception with context"""
        if not self.sentry_enabled:
            return

        try:
            import sentry_sdk

            # Set user context
            if user:
                sentry_sdk.set_user({
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "username": user.get("username"),
                })

            # Set additional context
            if context:
                sentry_sdk.set_context("additional", context)

            # Capture the exception
            sentry_sdk.capture_exception(error)

        except Exception as e:
            print(f"Failed to capture exception in Sentry: {e}")

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None
    ):
        """Capture a message/log with context"""
        if not self.sentry_enabled:
            return

        try:
            import sentry_sdk

            if context:
                sentry_sdk.set_context("additional", context)

            sentry_sdk.capture_message(message, level=level)

        except Exception as e:
            print(f"Failed to capture message in Sentry: {e}")

    # ============================================================================
    # User Analytics (PostHog)
    # ============================================================================

    def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Track a user event"""
        if not self.posthog_enabled:
            return

        try:
            self.posthog.capture(
                distinct_id=user_id,
                event=event_name,
                properties=properties or {}
            )
        except Exception as e:
            print(f"Failed to track event in PostHog: {e}")

    def identify_user(
        self,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Identify a user with properties"""
        if not self.posthog_enabled:
            return

        try:
            self.posthog.identify(
                distinct_id=user_id,
                properties=properties or {}
            )
        except Exception as e:
            print(f"Failed to identify user in PostHog: {e}")

    def track_page_view(
        self,
        user_id: str,
        page: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Track a page view"""
        if not self.posthog_enabled:
            return

        try:
            props = properties or {}
            props['$current_url'] = page
            self.posthog.capture(
                distinct_id=user_id,
                event='$pageview',
                properties=props
            )
        except Exception as e:
            print(f"Failed to track page view in PostHog: {e}")

    # ============================================================================
    # Common Events
    # ============================================================================

    def track_user_signup(self, user_id: str, email: str, role: str):
        """Track user signup"""
        self.identify_user(user_id, {
            'email': email,
            'role': role,
            'signup_date': datetime.utcnow().isoformat()
        })
        self.track_event(user_id, 'user_signup', {
            'role': role
        })

    def track_user_login(self, user_id: str, method: str = 'email'):
        """Track user login"""
        self.track_event(user_id, 'user_login', {
            'method': method
        })

    def track_file_upload(self, user_id: str, file_type: str, file_size: int):
        """Track file upload"""
        self.track_event(user_id, 'file_upload', {
            'file_type': file_type,
            'file_size': file_size
        })

    def track_pdf_operation(
        self,
        user_id: str,
        operation: str,
        file_count: int = 1,
        success: bool = True
    ):
        """Track PDF operation"""
        self.track_event(user_id, 'pdf_operation', {
            'operation': operation,
            'file_count': file_count,
            'success': success
        })

    def track_ai_usage(
        self,
        user_id: str,
        ai_operation: str,
        tokens_used: Optional[int] = None
    ):
        """Track AI feature usage"""
        self.track_event(user_id, 'ai_usage', {
            'operation': ai_operation,
            'tokens_used': tokens_used
        })

    def track_subscription_change(
        self,
        user_id: str,
        from_plan: str,
        to_plan: str
    ):
        """Track subscription plan change"""
        self.track_event(user_id, 'subscription_change', {
            'from_plan': from_plan,
            'to_plan': to_plan
        })

    def track_api_key_created(self, user_id: str, key_name: str):
        """Track API key creation"""
        self.track_event(user_id, 'api_key_created', {
            'key_name': key_name
        })

    # ============================================================================
    # Performance Monitoring
    # ============================================================================

    def track_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track performance metrics"""
        if not self.posthog_enabled:
            return

        try:
            props = {
                'operation': operation,
                'duration_ms': duration_ms,
                'success': success
            }
            if metadata:
                props.update(metadata)

            self.posthog.capture(
                distinct_id='system',
                event='performance_metric',
                properties=props
            )
        except Exception as e:
            print(f"Failed to track performance: {e}")

    def shutdown(self):
        """Shutdown monitoring services"""
        if self.posthog_enabled:
            try:
                self.posthog.shutdown()
            except Exception as e:
                print(f"Failed to shutdown PostHog: {e}")


# Singleton instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service singleton"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# Convenience functions
def capture_exception(error: Exception, context: Optional[Dict[str, Any]] = None, user: Optional[Dict[str, Any]] = None):
    """Capture exception to Sentry"""
    get_monitoring_service().capture_exception(error, context, user)


def track_event(user_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
    """Track event to PostHog"""
    get_monitoring_service().track_event(user_id, event_name, properties)
