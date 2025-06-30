import logging
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException

logger = logging.getLogger(__name__)

def send_password_reset_otp(email, otp, user_name="Valued Customer"):
    """Send beautiful password reset OTP email for Hajj Umrah Services"""
    
    subject = '🕋 Secure Your Hajj Umrah Services Account - Password Reset'
    
    # Beautiful HTML email template
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f7fa; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
            .header {{ background: linear-gradient(135deg, #2c5530 0%, #1a472a 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
            .kaaba-icon {{ font-size: 40px; margin-bottom: 10px; }}
            .content {{ padding: 40px 30px; }}
            .greeting {{ font-size: 18px; color: #2c5530; margin-bottom: 20px; }}
            .otp-section {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 25px; text-align: center; margin: 25px 0; border-left: 4px solid #2c5530; }}
            .otp-code {{ font-size: 32px; font-weight: bold; color: #2c5530; letter-spacing: 8px; margin: 15px 0; font-family: 'Courier New', monospace; }}
            .message {{ line-height: 1.6; color: #495057; margin-bottom: 20px; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
            .footer {{ background-color: #f8f9fa; padding: 25px; text-align: center; border-top: 1px solid #dee2e6; }}
            .footer-text {{ color: #6c757d; font-size: 14px; line-height: 1.5; }}
            .dua {{ font-style: italic; color: #2c5530; margin: 15px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
            .company-name {{ color: #2c5530; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="kaaba-icon">🕋</div>
                <h1>Hajj Umrah Services</h1>
                <p>Your Trusted Partner for Sacred Journeys</p>
            </div>
            
            <div class="content">
                <div class="greeting">Assalamu Alaikum, {user_name}</div>
                
                <div class="message">
                    <p>We received a request to reset the password for your Hajj Umrah Services CRM account. To ensure the security of your sacred journey planning, please use the verification code below to proceed with your password reset.</p>
                </div>
                
                <div class="otp-section">
                    <h3 style="margin-top: 0; color: #2c5530;">Your Verification Code</h3>
                    <div class="otp-code">{otp}</div>
                    <p style="margin-bottom: 0; color: #6c757d; font-size: 14px;">This code will expire in 10 minutes</p>
                </div>
                
                <div class="warning">
                    <strong>🔒 Security Notice:</strong> If you did not request this password reset, please ignore this email and contact our support team immediately. Your account security is our priority.
                </div>
                
                <div class="message">
                    <p>Once you've reset your password, you'll be able to continue planning your blessed journey with complete peace of mind. Our team is here to support you every step of the way towards your spiritual pilgrimage.</p>
                </div>
                
                <div class="dua">
                    <p>"رَبَّنَا تَقَبَّلْ مِنَّا إِنَّكَ أَنتَ السَّمِيعُ الْعَلِيمُ"</p>
                    <p><em>"Our Lord, accept this from us. Indeed, You are the Hearing, the Knowing."</em></p>
                </div>
            </div>
            
            <div class="footer">
                <div class="footer-text">
                    <p><strong class="company-name">Hajj Umrah Services</strong><br>
                    Facilitating Sacred Journeys Since [Year]</p>
                    
                    <p>📧 Email: support@hajjumrahservices.com<br>
                    📞 Phone: +1-XXX-XXX-XXXX<br>
                    🌐 Website: www.hajjumrahservices.com</p>
                    
                    <p style="margin-top: 20px; font-size: 12px;">
                        This is an automated message. Please do not reply to this email.<br>
                        If you need assistance, please contact our customer support team.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    plain_message = f"""
    Assalamu Alaikum, {user_name}
    
    HAJJ UMRAH SERVICES - PASSWORD RESET
    
    We received a request to reset your password for your Hajj Umrah Services CRM account.
    
    Your verification code is: {otp}
    
    This code will expire in 10 minutes.
    
    If you did not request this password reset, please ignore this email and contact our support team immediately.
    
    May Allah bless your sacred journey preparations.
    
    Hajj Umrah Services Team
    Your Trusted Partner for Sacred Journeys
    
    Email: support@hajjumrahservices.com
    Phone: +1-XXX-XXX-XXXX
    Website: www.hajjumrahservices.com
    """
    
    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Password reset OTP email sent successfully to {email}")
        return True
        
    except SMTPException as e:
        logger.error(f"SMTP error sending password reset OTP to {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending password reset OTP to {email}: {str(e)}")
        return False

def send_email_otp(email, otp):
    """Send OTP via email with enhanced error handling (original function)"""
    subject = 'Email Verification OTP'
    message = f'Your OTP for email verification is: {otp}. This OTP will expire in 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {email}")
        return True
        
    except SMTPException as e:
        logger.error(f"SMTP error sending OTP to {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending OTP to {email}: {str(e)}")
        return False