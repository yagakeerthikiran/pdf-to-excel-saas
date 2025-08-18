"""
Email Notification Service
Replaces Slack functionality with direct email notifications
"""

import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailNotificationService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', 'your-notifications@gmail.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', 'yagakeerthikiran@gmail.com')
        self.app_name = os.getenv('APP_NAME', 'PDF to Excel SaaS')
        
        # Email templates
        self.templates = {
            'error': self._error_template,
            'warning': self._warning_template,
            'info': self._info_template,
            'critical': self._critical_template,
            'auto_fix_success': self._auto_fix_success_template,
            'auto_fix_failed': self._auto_fix_failed_template,
            'deployment': self._deployment_template,
            'health_check': self._health_check_template
        }

    def send_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """
        Send email notification based on type and data
        
        Args:
            notification_type: Type of notification (error, warning, info, etc.)
            data: Dictionary containing notification data
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.smtp_password:
                logger.warning("SMTP password not configured, skipping email notification")
                return False

            # Get template function
            template_func = self.templates.get(notification_type, self._default_template)
            
            # Generate email content
            subject, html_body, text_body = template_func(data)
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{self.app_name}] {subject}"
            message["From"] = self.smtp_user
            message["To"] = self.notification_email
            
            # Add both text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email notification sent successfully: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _error_template(self, data: Dict[str, Any]) -> tuple:
        """Template for error notifications"""
        severity = data.get('severity', 'medium')
        message = data.get('message', 'Unknown error occurred')
        service = data.get('service', 'Unknown service')
        
        subject = f"🚨 {severity.upper()} Error - {service}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #721c24; margin: 0;">🚨 Error Alert</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <h3>Error Details</h3>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Severity:</strong> <span style="color: #dc3545; font-weight: bold;">{severity.upper()}</span></p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                {self._get_fix_strategy_html(data)}
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                <p style="margin: 0; font-size: 12px; color: #6c757d;">
                    This is an automated notification from {self.app_name} monitoring system.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
ERROR ALERT - {self.app_name}

Service: {service}
Severity: {severity.upper()}
Message: {message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{self._get_fix_strategy_text(data)}

---
This is an automated notification from {self.app_name} monitoring system.
        """
        
        return subject, html_body, text_body

    def _warning_template(self, data: Dict[str, Any]) -> tuple:
        """Template for warning notifications"""
        message = data.get('message', 'Warning condition detected')
        service = data.get('service', 'Unknown service')
        
        subject = f"⚠️ Warning - {service}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #856404; margin: 0;">⚠️ Warning Alert</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <h3>Warning Details</h3>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
WARNING ALERT - {self.app_name}

Service: {service}
Message: {message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return subject, html_body, text_body

    def _info_template(self, data: Dict[str, Any]) -> tuple:
        """Template for info notifications"""
        message = data.get('message', 'Information update')
        
        subject = f"ℹ️ Info - {message[:50]}..."
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #0c5460; margin: 0;">ℹ️ Information</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <p>{message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
INFO - {self.app_name}

{message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return subject, html_body, text_body

    def _critical_template(self, data: Dict[str, Any]) -> tuple:
        """Template for critical notifications"""
        message = data.get('message', 'Critical system issue')
        service = data.get('service', 'System')
        
        subject = f"🔥 CRITICAL - {service} DOWN"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="margin: 0;">🔥 CRITICAL ALERT</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px;">IMMEDIATE ATTENTION REQUIRED</p>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 2px solid #dc3545;">
                <h3>Critical Issue Details</h3>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; margin-top: 15px;">
                    <p style="margin: 0; font-weight: bold; color: #721c24;">
                        ⚡ This requires immediate action to restore service functionality.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
🔥 CRITICAL ALERT - {self.app_name}
IMMEDIATE ATTENTION REQUIRED

Service: {service}
Message: {message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

⚡ This requires immediate action to restore service functionality.
        """
        
        return subject, html_body, text_body

    def _auto_fix_success_template(self, data: Dict[str, Any]) -> tuple:
        """Template for successful auto-fix notifications"""
        fix_strategy = data.get('fix_strategy', 'Unknown fix')
        original_issue = data.get('original_issue', 'Unknown issue')
        
        subject = f"✅ Auto-Fix Successful - {fix_strategy}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #155724; margin: 0;">✅ Auto-Fix Successful</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <p><strong>Fix Applied:</strong> {fix_strategy}</p>
                <p><strong>Original Issue:</strong> {original_issue}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; margin-top: 15px;">
                    <p style="margin: 0; color: #155724;">
                        🤖 The monitoring system automatically resolved this issue.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
✅ AUTO-FIX SUCCESSFUL - {self.app_name}

Fix Applied: {fix_strategy}
Original Issue: {original_issue}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🤖 The monitoring system automatically resolved this issue.
        """
        
        return subject, html_body, text_body

    def _auto_fix_failed_template(self, data: Dict[str, Any]) -> tuple:
        """Template for failed auto-fix notifications"""
        fix_strategy = data.get('fix_strategy', 'Unknown fix')
        error = data.get('error', 'Unknown error')
        
        subject = f"❌ Auto-Fix Failed - Manual Intervention Required"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #721c24; margin: 0;">❌ Auto-Fix Failed</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <p><strong>Failed Fix:</strong> {fix_strategy}</p>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 15px;">
                    <p style="margin: 0; color: #856404; font-weight: bold;">
                        🔧 Manual intervention required to resolve this issue.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
❌ AUTO-FIX FAILED - {self.app_name}
MANUAL INTERVENTION REQUIRED

Failed Fix: {fix_strategy}
Error: {error}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🔧 Manual intervention required to resolve this issue.
        """
        
        return subject, html_body, text_body

    def _deployment_template(self, data: Dict[str, Any]) -> tuple:
        """Template for deployment notifications"""
        status = data.get('status', 'completed')
        version = data.get('version', 'unknown')
        
        subject = f"🚀 Deployment {status.title()} - v{version}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="color: #0c5460; margin: 0;">🚀 Deployment Update</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #dee2e6;">
                <p><strong>Status:</strong> {status.title()}</p>
                <p><strong>Version:</strong> v{version}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
🚀 DEPLOYMENT UPDATE - {self.app_name}

Status: {status.title()}
Version: v{version}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return subject, html_body, text_body

    def _health_check_template(self, data: Dict[str, Any]) -> tuple:
        """Template for health check notifications"""
        service = data.get('service', 'Unknown')
        status = data.get('status', 'unknown')
        
        subject = f"💓 Health Check - {service} is {status}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <p><strong>Service:</strong> {service}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </body>
        </html>
        """
        
        text_body = f"""
💓 HEALTH CHECK - {self.app_name}

Service: {service}
Status: {status}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return subject, html_body, text_body

    def _default_template(self, data: Dict[str, Any]) -> tuple:
        """Default template for unknown notification types"""
        message = data.get('message', 'System notification')
        
        subject = f"📢 Notification - {self.app_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <p>{message}</p>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </body>
        </html>
        """
        
        text_body = f"""
NOTIFICATION - {self.app_name}

{message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return subject, html_body, text_body

    def _get_fix_strategy_html(self, data: Dict[str, Any]) -> str:
        """Get HTML for fix strategy information"""
        fix_strategy = data.get('fix_strategy')
        if fix_strategy:
            return f"""
            <div style="background-color: #e2e3e5; padding: 10px; border-radius: 5px; margin-top: 15px;">
                <p style="margin: 0;">
                    <strong>Suggested Fix:</strong> {fix_strategy}
                </p>
            </div>
            """
        return ""

    def _get_fix_strategy_text(self, data: Dict[str, Any]) -> str:
        """Get text for fix strategy information"""
        fix_strategy = data.get('fix_strategy')
        if fix_strategy:
            return f"\nSuggested Fix: {fix_strategy}\n"
        return ""

# Global instance
email_service = EmailNotificationService()

def send_email_notification(notification_type: str, data: Dict[str, Any]) -> bool:
    """
    Convenient function to send email notifications
    
    Args:
        notification_type: Type of notification (error, warning, info, etc.)
        data: Dictionary containing notification data
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    return email_service.send_notification(notification_type, data)
