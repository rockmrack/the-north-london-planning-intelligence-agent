"""
Notification service for the Planning Intelligence Agent.
Handles email, Slack, and other notifications.
"""

import json
from typing import Dict, List, Optional

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class NotificationService:
    """
    Service for sending notifications via multiple channels.

    Supports:
    - Email via SendGrid
    - Slack webhooks
    - (Future) HubSpot CRM sync
    """

    def __init__(self):
        self.sendgrid_key = settings.sendgrid_api_key if hasattr(settings, 'sendgrid_api_key') else None
        self.slack_webhook = settings.slack_webhook_url if hasattr(settings, 'slack_webhook_url') else None
        self.hubspot_key = settings.hubspot_api_key if hasattr(settings, 'hubspot_api_key') else None

    # ==================== Email Notifications ====================

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = None,
    ) -> bool:
        """Send an email via SendGrid."""
        if not self.sendgrid_key:
            logger.warning("SendGrid API key not configured, skipping email")
            return False

        from_email = from_email or "noreply@planningintelligence.co.uk"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": to_email}]}],
                        "from": {"email": from_email},
                        "subject": subject,
                        "content": [{"type": "text/html", "value": html_content}],
                    },
                )

                if response.status_code in [200, 202]:
                    logger.info("Email sent successfully", to=to_email, subject=subject)
                    return True
                else:
                    logger.error(
                        "Failed to send email",
                        status=response.status_code,
                        response=response.text,
                    )
                    return False

        except Exception as e:
            logger.error("Email sending error", error=str(e))
            return False

    async def send_new_lead_email(
        self,
        admin_email: str,
        lead_data: Dict,
    ) -> bool:
        """Send notification email for new lead to admin."""
        subject = f"New Lead: {lead_data.get('name', 'Unknown')} - {lead_data.get('borough', 'Unknown Borough')}"

        html_content = f"""
        <h2>New Lead Captured</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Name</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('name', 'Not provided')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Email</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('email', 'Not provided')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Phone</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('phone', 'Not provided')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Postcode</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('postcode', 'Not provided')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Borough</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('borough', 'Not detected')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Project Type</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('project_type', 'Not specified')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Source</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead_data.get('source', 'chat_widget')}</td>
            </tr>
        </table>
        <p style="margin-top: 20px;">
            <a href="{settings.frontend_url}/admin/leads/{lead_data.get('id', '')}"
               style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Lead Details
            </a>
        </p>
        """

        return await self.send_email(admin_email, subject, html_content)

    async def send_welcome_email(
        self,
        to_email: str,
        name: str = None,
    ) -> bool:
        """Send welcome email to new lead."""
        subject = "Welcome to North London Planning Intelligence"

        html_content = f"""
        <h2>Welcome{f', {name}' if name else ''}!</h2>
        <p>Thank you for using the North London Planning Intelligence Agent.</p>
        <p>You can now continue asking questions about planning permission for your project.
           Our AI assistant has access to thousands of official planning documents from:</p>
        <ul>
            <li>Camden Council</li>
            <li>Barnet Council</li>
            <li>Westminster Council</li>
            <li>Brent Council</li>
            <li>Haringey Council</li>
        </ul>
        <p>If you'd like to discuss your project with a planning expert, feel free to reply to this email
           or book a consultation through our website.</p>
        <p>Best regards,<br>The Planning Intelligence Team</p>
        """

        return await self.send_email(to_email, subject, html_content)

    # ==================== Slack Notifications ====================

    async def send_slack_message(
        self,
        message: str,
        blocks: List[Dict] = None,
        channel: str = None,
    ) -> bool:
        """Send a message to Slack via webhook."""
        if not self.slack_webhook:
            logger.debug("Slack webhook not configured, skipping notification")
            return False

        try:
            payload = {"text": message}
            if blocks:
                payload["blocks"] = blocks

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook,
                    json=payload,
                )

                if response.status_code == 200:
                    logger.info("Slack message sent successfully")
                    return True
                else:
                    logger.error(
                        "Failed to send Slack message",
                        status=response.status_code,
                        response=response.text,
                    )
                    return False

        except Exception as e:
            logger.error("Slack notification error", error=str(e))
            return False

    async def send_new_lead_slack_notification(
        self,
        lead_data: Dict,
    ) -> bool:
        """Send Slack notification for new lead."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "New Lead Captured",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Name:*\n{lead_data.get('name', 'Not provided')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:*\n{lead_data.get('email', 'Not provided')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Borough:*\n{lead_data.get('borough', 'Not detected')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Project:*\n{lead_data.get('project_type', 'Not specified')}",
                    },
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Lead",
                        },
                        "url": f"{settings.frontend_url}/admin/leads/{lead_data.get('id', '')}",
                    },
                ],
            },
        ]

        return await self.send_slack_message(
            f"New lead: {lead_data.get('name', 'Unknown')} ({lead_data.get('email', '')})",
            blocks=blocks,
        )

    async def send_daily_summary_slack(
        self,
        stats: Dict,
    ) -> bool:
        """Send daily summary to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Daily Summary",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Queries:*\n{stats.get('total_queries', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Unique Sessions:*\n{stats.get('unique_sessions', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*New Leads:*\n{stats.get('new_leads', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Response Time:*\n{stats.get('avg_response_time', 0):.0f}ms",
                    },
                ],
            },
        ]

        return await self.send_slack_message(
            f"Daily Summary: {stats.get('total_queries', 0)} queries, {stats.get('new_leads', 0)} new leads",
            blocks=blocks,
        )

    # ==================== High-Level Notification Methods ====================

    async def send_new_lead_notification(
        self,
        lead_id: str,
        lead_data: Dict,
    ) -> None:
        """Send all notifications for a new lead."""
        # Send Slack notification
        await self.send_new_lead_slack_notification(lead_data)

        # Send welcome email to lead
        if lead_data.get("email"):
            await self.send_welcome_email(
                lead_data["email"],
                lead_data.get("name"),
            )

        # Send notification to admin (if configured)
        admin_email = getattr(settings, 'admin_email', None)
        if admin_email:
            await self.send_new_lead_email(admin_email, lead_data)

        logger.info("New lead notifications sent", lead_id=lead_id)

    async def send_returning_user_notification(
        self,
        lead_id: str,
    ) -> None:
        """Send notification for returning user (minimal for now)."""
        logger.info("Returning user", lead_id=lead_id)

    async def send_error_alert(
        self,
        error_type: str,
        error_message: str,
        context: Dict = None,
    ) -> None:
        """Send alert for system errors."""
        if self.slack_webhook:
            message = f":warning: *Error Alert: {error_type}*\n```{error_message}```"
            if context:
                message += f"\n*Context:*\n```{json.dumps(context, indent=2)}```"

            await self.send_slack_message(message)


# Global instance
notification_service = NotificationService()
