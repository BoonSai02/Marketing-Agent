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
    async def send_verification_otp(
        recipient_email: str,
        otp: str,
        recipient_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        try:
            subject = "Verify your account"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <h2>Verify your account</h2>
                        <p>Hello {recipient_name or 'User'},</p>
                        <p>Your verification code is:</p>
                        <h1 style="background-color: #f8f9fa; padding: 10px; text-align: center; letter-spacing: 5px;">{otp}</h1>
                        <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
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

            return True, "Verification email sent successfully"

        except Exception as e:
            logger.exception("Failed to send verification email")
            return False, "Failed to send email"

    @staticmethod
    async def send_password_reset_otp(
        recipient_email: str,
        otp: str,
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
                        <p>We received a request to reset your password. Your password reset code is:</p>
                        <h1 style="background-color: #f8f9fa; padding: 10px; text-align: center; letter-spacing: 5px;">{otp}</h1>
                        <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
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

            return True, "Password reset OTP sent successfully"

        except Exception as e:
            logger.exception("Failed to send password reset OTP")
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

    @staticmethod
    async def send_generic_email(
        recipient_email: str,
        subject: str,
        html_body: str
    ) -> Tuple[bool, str]:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
            message["To"] = recipient_email
            message.attach(MIMEText(html_body, "html"))

            async with aiosmtplib.SMTP(hostname=settings.SMTP_SERVER, port=settings.SMTP_PORT) as smtp:
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                await smtp.sendmail(settings.SENDER_EMAIL, [recipient_email], message.as_string())

            return True, "Email sent successfully"

        except Exception:
            logger.exception("Failed to send generic email")
            return False, "Failed to send email"
