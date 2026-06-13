"""Celery tasks for automated email sending."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from celery import shared_task
import logging

from app.core.database import SessionLocal
from app.models.user import User
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


@shared_task(name="send_churn_prevention_emails")
def send_churn_prevention_emails():
    """
    Send churn prevention emails to inactive users

    Runs daily to find users who haven't logged in for:
    - 7 days (first reminder)
    - 30 days (second reminder)
    - 90 days (final reminder)

    Returns:
        dict: Summary of emails sent
    """
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        emails_sent = {
            "7_days": 0,
            "30_days": 0,
            "90_days": 0,
            "errors": 0
        }

        # Define inactivity thresholds
        thresholds = [
            (7, "7_days"),
            (30, "30_days"),
            (90, "90_days")
        ]

        for days, key in thresholds:
            # Calculate date range (target users inactive for exactly this many days)
            # This prevents sending duplicate emails
            target_date_start = now - timedelta(days=days, hours=1)
            target_date_end = now - timedelta(days=days)

            # Find users inactive for this period
            inactive_users = db.query(User).filter(
                User.is_active == True,
                User.last_login_at >= target_date_start,
                User.last_login_at < target_date_end,
                User.email.isnot(None)
            ).all()

            logger.info(f"Found {len(inactive_users)} users inactive for ~{days} days")

            # Send churn prevention emails
            for user in inactive_users:
                try:
                    success = email_service.send_churn_prevention_email(
                        to=user.email,
                        username=user.full_name or user.email.split('@')[0],
                        days_inactive=days
                    )

                    if success:
                        emails_sent[key] += 1
                        logger.info(f"Churn email sent to {user.email} ({days} days inactive)")
                    else:
                        emails_sent["errors"] += 1

                except Exception as e:
                    logger.error(f"Error sending churn email to {user.email}: {str(e)}")
                    emails_sent["errors"] += 1

        logger.info(f"Churn prevention emails sent: {emails_sent}")
        return emails_sent

    except Exception as e:
        logger.error(f"Error in send_churn_prevention_emails task: {str(e)}")
        raise
    finally:
        db.close()
