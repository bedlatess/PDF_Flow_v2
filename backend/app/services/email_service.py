"""
Email service using Resend API
Handles all transactional emails: welcome, password reset, churn prevention
"""
import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Resend email service for transactional emails"""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM
        self.base_url = "https://api.resend.com"
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("RESEND_API_KEY not set - emails will be logged but not sent")

    async def _send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """
        Send email via Resend API

        Args:
            to: Recipient email
            subject: Email subject
            html: HTML body
            text: Plain text body (optional)

        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.info(f"[EMAIL DISABLED] Skipped sending email to {to}: {subject}")
            logger.debug(f"HTML content: {html}")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text or ""
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to}: {subject}")
                    return True
                else:
                    logger.error(f"Failed to send email to {to}: {response.status_code} {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending email to {to}: {str(e)}")
            return False

    async def send_welcome_email(self, to: str, username: str) -> bool:
        """
        Send welcome email to new user

        Args:
            to: User email
            username: User's display name

        Returns:
            bool: True if sent successfully
        """
        subject = "Welcome to PDF-Flow"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e4e8; border-top: none; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .features {{ background: #f6f8fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .feature-item {{ margin: 10px 0; padding-left: 24px; position: relative; }}
                .feature-item:before {{ content: "-"; position: absolute; left: 0; color: #28a745; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; color: #586069; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to PDF-Flow!</h1>
                    <p>Your PDF workspace for everyday and Pro workflows</p>
                </div>

                <div class="content">
                    <p>Hi {username},</p>

                    <p>Thank you for joining PDF-Flow! We're excited to help you handle everyday PDF work and advanced document workflows in one place.</p>

                    <div class="features">
                        <h3>What you can do with PDF-Flow:</h3>
                        <div class="feature-item">Merge, split, rotate, and compress PDFs</div>
                        <div class="feature-item">Convert images to PDF and vice versa</div>
                        <div class="feature-item">Free tools for common PDF tasks</div>
                        <div class="feature-item">Pro OCR and Office conversion</div>
                        <div class="feature-item">Pro AI-powered PDF analysis</div>
                    </div>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/tools" class="button">Start Using PDF-Flow</a>
                    </p>

                    <p><strong>Free Tier Includes:</strong></p>
                    <ul>
                        <li>Everyday PDF tools</li>
                        <li>Starter access to advanced workflows</li>
                        <li>20MB file size limit</li>
                    </ul>

                    <p>Need more? <a href="{settings.FRONTEND_URL}/pricing">Upgrade to Pro</a> for OCR, Office conversion, larger files, and AI capabilities.</p>

                    <p>If you have any questions, feel free to reach out to our support team.</p>

                    <p>Best regards,<br>The PDF-Flow Team</p>
                </div>

                <div class="footer">
                    <p>PDF-Flow - PDF tools and Pro workflows</p>
                    <p><a href="{settings.FRONTEND_URL}">Visit Website</a> | <a href="{settings.FRONTEND_URL}/pricing">Pricing</a> | <a href="{settings.FRONTEND_URL}/support">Support</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        Welcome to PDF-Flow!

        Hi {username},

        Thank you for joining PDF-Flow! We're excited to help you handle everyday PDF work and advanced document workflows in one place.

        What you can do with PDF-Flow:
        - Merge, split, rotate, and compress PDFs
        - Convert images to PDF and vice versa
        - Free tools for common PDF tasks
        - Pro OCR and Office conversion
        - Pro AI-powered PDF analysis

        Free Tier Includes:
        - Everyday PDF tools
        - Starter access to advanced workflows
        - 20MB file size limit

        Start using PDF-Flow: {settings.FRONTEND_URL}/tools

        Need more? Upgrade to Pro: {settings.FRONTEND_URL}/pricing

        Best regards,
        The PDF-Flow Team
        """

        return await self._send_email(to, subject, html, text)

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email with token

        Args:
            to: User email
            username: User's display name
            reset_token: Password reset token (JWT)

        Returns:
            bool: True if sent successfully
        """
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
        subject = "Reset Your PDF-Flow Password"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e4e8; border-top: none; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #586069; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>

                <div class="content">
                    <p>Hi {username},</p>

                    <p>We received a request to reset your PDF-Flow password. Click the button below to create a new password:</p>

                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #0366d6;">{reset_url}</p>

                    <div class="warning">
                        <strong>Security Notice:</strong>
                        <ul style="margin: 10px 0;">
                            <li>This link expires in <strong>1 hour</strong></li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will remain unchanged until you create a new one</li>
                        </ul>
                    </div>

                    <p>If you're having trouble with the button, you can also reset your password by visiting:</p>
                    <p><a href="{settings.FRONTEND_URL}/auth/forgot-password">{settings.FRONTEND_URL}/auth/forgot-password</a></p>

                    <p>Best regards,<br>The PDF-Flow Team</p>
                </div>

                <div class="footer">
                    <p>PDF-Flow - Privacy-First PDF Tools</p>
                    <p>If you didn't request this email, please <a href="{settings.FRONTEND_URL}/support">contact support</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        Password Reset Request

        Hi {username},

        We received a request to reset your PDF-Flow password.

        Click this link to reset your password:
        {reset_url}

        Security Notice:
        - This link expires in 1 hour
        - If you didn't request this reset, please ignore this email
        - Your password will remain unchanged until you create a new one

        Best regards,
        The PDF-Flow Team
        """

        return await self._send_email(to, subject, html, text)

    async def send_churn_prevention_email(
        self,
        to: str,
        username: str,
        days_inactive: int
    ) -> bool:
        """
        Send churn prevention email to inactive users

        Args:
            to: User email
            username: User's display name
            days_inactive: Number of days since last activity

        Returns:
            bool: True if sent successfully
        """
        subject = f"We miss you, {username}! Come back to PDF-Flow"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e4e8; border-top: none; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .highlight {{ background: #f6f8fa; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #586069; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>We Miss You!</h1>
                    <p>Come back and continue working with your PDFs</p>
                </div>

                <div class="content">
                    <p>Hi {username},</p>

                    <p>We noticed it's been <strong>{days_inactive} days</strong> since you last used PDF-Flow, and we wanted to check in!</p>

                    <div class="highlight">
                        <h3>What's New in PDF-Flow:</h3>
                        <ul>
                            <li><strong>AI-Powered Analysis</strong> - Ask questions about your PDFs with Gemini AI</li>
                            <li><strong>Enhanced OCR</strong> - Extract text from scanned documents in 10+ languages</li>
                            <li><strong>Office Conversion</strong> - Convert Word, Excel, PowerPoint to PDF seamlessly</li>
                            <li><strong>Faster Processing</strong> - Optimized performance for all tools</li>
                        </ul>
                    </div>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/tools" class="button">Start Processing PDFs</a>
                    </p>

                    <p><strong>Quick Reminder of What You Can Do:</strong></p>
                    <ul>
                        <li>Merge multiple PDFs into one</li>
                        <li>Split PDFs into individual pages</li>
                        <li>Compress large files</li>
                        <li>Convert images to PDFs</li>
                        <li>Add watermarks to protect your documents</li>
                    </ul>

                    <p>All basic tools work 100% locally in your browser - your files never leave your device!</p>

                    <p>We're here to help if you need anything. Just reply to this email or visit our support page.</p>

                    <p>Hope to see you back soon!</p>

                    <p>Best regards,<br>The PDF-Flow Team</p>

                    <p style="font-size: 12px; color: #6a737d; margin-top: 30px;">
                        <em>P.S. If you'd prefer not to receive these emails, you can <a href="{settings.FRONTEND_URL}/settings/notifications">update your preferences</a>.</em>
                    </p>
                </div>

                <div class="footer">
                    <p>PDF-Flow - Privacy-First PDF Tools</p>
                    <p><a href="{settings.FRONTEND_URL}">Visit Website</a> | <a href="{settings.FRONTEND_URL}/pricing">Pricing</a> | <a href="{settings.FRONTEND_URL}/support">Support</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        We Miss You!

        Hi {username},

        We noticed it's been {days_inactive} days since you last used PDF-Flow, and we wanted to check in!

        What's New in PDF-Flow:
        - AI-Powered Analysis - Ask questions about your PDFs with Gemini AI
        - Enhanced OCR - Extract text from scanned documents in 10+ languages
        - Office Conversion - Convert Word, Excel, PowerPoint to PDF seamlessly
        - Faster Processing - Optimized performance for all tools

        Quick Reminder of What You Can Do:
        - Merge multiple PDFs into one
        - Split PDFs into individual pages
        - Compress large files
        - Convert images to PDFs
        - Add watermarks to protect your documents

        All basic tools work 100% locally in your browser - your files never leave your device!

        Start processing PDFs: {settings.FRONTEND_URL}/tools

        Hope to see you back soon!

        Best regards,
        The PDF-Flow Team

        P.S. If you'd prefer not to receive these emails, update your preferences: {settings.FRONTEND_URL}/settings/notifications
        """

        return await self._send_email(to, subject, html, text)

    async def send_subscription_confirmation_email(
        self,
        to: str,
        username: str,
        plan: str,
        amount: float,
        billing_period: str
    ) -> bool:
        """
        Send subscription confirmation email

        Args:
            to: User email
            username: User's display name
            plan: Subscription plan (Pro/Enterprise)
            amount: Subscription amount
            billing_period: monthly/yearly

        Returns:
            bool: True if sent successfully
        """
        subject = f"Welcome to PDF-Flow {plan}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e4e8; border-top: none; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .info-box {{ background: #f6f8fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #586069; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {plan}!</h1>
                    <p>Thank you for upgrading</p>
                </div>

                <div class="content">
                    <p>Hi {username},</p>

                    <p>Your subscription to PDF-Flow {plan} has been activated! You now have access to all premium features.</p>

                    <div class="info-box">
                        <h3>Subscription Details:</h3>
                        <p><strong>Plan:</strong> {plan}</p>
                        <p><strong>Amount:</strong> ${amount:.2f} / {billing_period}</p>
                        <p><strong>Billing Period:</strong> {billing_period.capitalize()}</p>
                    </div>

                    <p><strong>What You Get with {plan}:</strong></p>
                    <ul>
                        <li>Unlimited cloud processing</li>
                        <li>500MB file size limit</li>
                        <li>OCR in 10+ languages</li>
                        <li>Office to PDF conversion</li>
                        <li>AI-powered PDF analysis (Gemini)</li>
                        <li>Priority support</li>
                        <li>No ads or watermarks</li>
                    </ul>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/tools" class="button">Start Using {plan} Features</a>
                    </p>

                    <p>You can manage your subscription, update payment methods, or cancel anytime from your <a href="{settings.FRONTEND_URL}/profile">account settings</a>.</p>

                    <p>Thank you for supporting PDF-Flow!</p>

                    <p>Best regards,<br>The PDF-Flow Team</p>
                </div>

                <div class="footer">
                    <p>PDF-Flow - Privacy-First PDF Tools</p>
                    <p><a href="{settings.FRONTEND_URL}/profile">Manage Subscription</a> | <a href="{settings.FRONTEND_URL}/support">Support</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        Welcome to {plan}!

        Hi {username},

        Your subscription to PDF-Flow {plan} has been activated! You now have access to all premium features.

        Subscription Details:
        - Plan: {plan}
        - Amount: ${amount:.2f} / {billing_period}
        - Billing Period: {billing_period.capitalize()}

        What You Get with {plan}:
        - Unlimited cloud processing
        - 500MB file size limit
        - OCR in 10+ languages
        - Office to PDF conversion
        - AI-powered PDF analysis (Gemini)
        - Priority support
        - No ads or watermarks

        Start using {plan} features: {settings.FRONTEND_URL}/tools

        Manage subscription: {settings.FRONTEND_URL}/profile

        Thank you for supporting PDF-Flow!

        Best regards,
        The PDF-Flow Team
        """

        return await self._send_email(to, subject, html, text)


# Global email service instance
email_service = EmailService()
