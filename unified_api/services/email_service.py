import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend_config import Backend_config
from typing import Tuple, Optional
from datetime import datetime
import logging

settings = Backend_config()
logger = logging.getLogger("auth.email")


class EmailService:
    @staticmethod
    async def send_password_reset_email(
        recipient_email: str,
        reset_link: str,
        recipient_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        try:
            subject = "Password Reset Request"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <h2>Password Reset Request</h2>
                        <p>Hello {recipient_name or 'User'},</p>
                        <p>We received a request to reset your password. Click the link below to proceed:</p>
                        <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all;">{reset_link}</p>
                        <p>This link will expire in {settings.RESET_TOKEN_EXPIRE_HOURS} hour(s).</p>
                        <p>If you didn't request this, you can ignore this email.</p>
                        <hr>
                        <p style="color: #666; font-size: 12px;">© {datetime.now().year} {settings.SENDER_NAME}. All rights reserved.</p>
                    </div>
                </body>
            </html>
            """
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
            message["To"] = recipient_email
            message.attach(MIMEText(html_body, "html"))

            async with aiosmtplib.SMTP(hostname=settings.SMTP_SERVER, port=settings.SMTP_PORT) as smtp:
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                await smtp.sendmail(settings.SENDER_EMAIL, [recipient_email], message.as_string())

            return True, "Email sent successfully"

        except Exception as e:
            logger.exception("Failed to send password reset email")
            return False, "Failed to send email"

    @staticmethod
    async def send_welcome_email(
        recipient_email: str,
        recipient_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        try:
            subject = f"Welcome to {settings.SENDER_NAME}!"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <h2>Welcome to {settings.SENDER_NAME}!</h2>
                        <p>Hello {recipient_name or 'User'},</p>
                        <p>Thank you for signing up! Your account has been successfully created.</p>
                        <p>You can now log in and start using our service.</p>
                        <hr>
                        <p style="color: #666; font-size: 12px;">© {datetime.now().year} {settings.SENDER_NAME}. All rights reserved.</p>
                    </div>
                </body>
            </html>
            """
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
            message["To"] = recipient_email
            message.attach(MIMEText(html_body, "html"))

            async with aiosmtplib.SMTP(hostname=settings.SMTP_SERVER, port=settings.SMTP_PORT) as smtp:
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                await smtp.sendmail(settings.SENDER_EMAIL, [recipient_email], message.as_string())

            return True, "Welcome email sent successfully"

        except Exception:
            logger.exception("Failed to send welcome email")
            return False, "Failed to send welcome email"
