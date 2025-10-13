# api/tasks.py - Enhanced version
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_registration_email_task(self, participant_data, payment_data, team_data=None, 
                                 team_members_data=None, team_competitions=None):
    """
    Celery task to send registration confirmation email with better error handling
    """
    try:
        # Validate data before processing
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data: missing email")
            return {'success': False, 'error': 'Invalid participant data'}
        
        # Check for duplicate send (idempotency)
        from django.core.cache import cache
        cache_key = f"reg_email_{participant_data['id']}_{payment_data.get('trx_id', 'unknown')}"
        
        if cache.get(cache_key):
            logger.info(f"Email already sent for {cache_key}, skipping")
            return {'success': True, 'message': 'Email already sent', 'duplicate': True}
        
        # Prepare context for email template
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_data['id'],
            'participant_email': participant_data['email'],
            'participant_phone': participant_data.get('phone', ''),
            'participant_institution': participant_data.get('institution', ''),
            'trx_id': payment_data.get('trx_id', ''),
            'amount': payment_data.get('amount', ''),
            'payment_phone': payment_data.get('phone', ''),
            'segments': participant_data.get('segments', []),
            'competitions': participant_data.get('competitions', []),
        }
        
        # Add team information if provided
        if team_data:
            context.update({
                'team_name': team_data.get('name', ''),
                'team_id': team_data.get('id', ''),
                'team_members': team_members_data or [],
                'team_competitions': team_competitions or []
            })
        
        # Render and send email
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from .utils import attach_logo
        
        html_content = render_to_string('registration_email_template.html', context)
        
        subject = "Registration Successful - Innoverse"
        if team_data:
            subject = f"Registration Successful - Team {team_data.get('name', '')} - Innoverse"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for registering for Innoverse! Please view this email in HTML format.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[participant_data['email']]
        )
        
        email.attach_alternative(html_content, "text/html")
        email = attach_logo(email)
        email.send(fail_silently=False)
        
        # Mark as sent (cache for 7 days)
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"Registration email sent successfully to {participant_data['email']}")
        return {
            'success': True, 
            'recipient': participant_data['email'],
            'participant_id': participant_data['id']
        }
        
    except Exception as e:
        logger.error(f"Failed to send registration email: {str(e)}", exc_info=True)
        
        # Retry with exponential backoff
        try:
            # Calculate exponential backoff: 60s, 120s, 240s
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for registration email to {participant_data.get('email')}")
            return {
                'success': False, 
                'error': str(e),
                'participant_id': participant_data.get('id'),
                'max_retries_exceeded': True
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_verification_email_task(self, participant_data, team_data=None):
    """
    Celery task to send payment verification email with QR code - Enhanced
    """
    try:
        # Validate data
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data for payment verification")
            return {'success': False, 'error': 'Invalid participant data'}
        
        qr_id = f"p_{participant_data['id']}"
        recipients = [participant_data['email']]
        
        # Check for duplicate send
        from django.core.cache import cache
        cache_key = f"payment_email_{qr_id}"
        
        if cache.get(cache_key):
            logger.info(f"Payment email already sent for {qr_id}, skipping")
            return {'success': True, 'message': 'Email already sent', 'duplicate': True}
        
        # Prepare context
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_data['id'],
            'participant_email': participant_data['email'],
            'qr_id': qr_id,
            'segments': participant_data.get('segments', []),
            'competitions': participant_data.get('competitions', []),
        }
        
        # Handle team data
        if team_data:
            qr_id = f"t_{team_data['id']}"
            context.update({
                'team_name': team_data.get('name', ''),
                'team_id': team_data['id'],
                'qr_id': qr_id
            })
            
            # Add team member emails
            for member_email in team_data.get('member_emails', []):
                if member_email and member_email not in recipients:
                    recipients.append(member_email)
        
        # Generate QR code
        from .utils import generate_qr_code
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        # Render and send email
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from email.mime.image import MIMEImage
        from .utils import attach_logo
        
        html_content = render_to_string('email_template.html', context)
        
        email = EmailMultiAlternatives(
            subject="Payment Verified - Innoverse Registration",
            body="Your payment has been verified. Please view this email in HTML format.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        
        email.attach_alternative(html_content, "text/html")
        email = attach_logo(email)
        
        # Attach QR code
        qr_image = MIMEImage(qr_buffer.read())
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.jpg')
        email.attach(qr_image)
        
        qr_buffer.seek(0)
        email.attach(f'{qr_id}_qr.jpg', qr_buffer.read(), 'image/jpeg')
        
        email.send(fail_silently=False)
        
        # Mark as sent
        cache.set(cache_key, True, timeout=604800)  # 7 days
        
        logger.info(f"Payment verification email sent to {len(recipients)} recipients")
        return {
            'success': True,
            'recipients': recipients,
            'qr_id': qr_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send payment verification email: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for payment verification email")
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True
            }