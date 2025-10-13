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

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_verification_email_task(self, participant_data, team_data=None):
    """
    Celery task to send payment verification email with QR code - Optimized & Enhanced
    """
    try:
        logger.info(f"Starting payment verification email task for participant {participant_data.get('id')}")
        
        # Validate data
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data for payment verification")
            return {'success': False, 'error': 'Invalid participant data'}
        
        qr_id = f"p_{participant_data['id']}"
        recipients = [participant_data['email']]
        
        # Check for duplicate send (prevent double-sending)
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
                'qr_id': qr_id,
                'team_competitions': team_data.get('competitions', []),
            })
            
            # Add team member emails
            for member_email in team_data.get('member_emails', []):
                if member_email and member_email not in recipients:
                    recipients.append(member_email)
        
        logger.info(f"Generating QR code for {qr_id}")
        
        # Generate QR code
        from .utils import generate_qr_code
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("Failed to generate QR code")
        
        logger.info(f"Rendering email template for {qr_id}")
        
        # Render email
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from email.mime.image import MIMEImage
        from .utils import attach_logo
        
        html_content = render_to_string('email_template.html', context)
        
        subject = "Payment Verified - Innoverse Registration"
        if team_data:
            subject = f"Payment Verified - Team {team_data.get('name')} - Innoverse"
        
        logger.info(f"Creating email for {len(recipients)} recipients")
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your payment has been verified. Please view this email in HTML format.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        try:
            email = attach_logo(email)
        except Exception as logo_error:
            logger.warning(f"Failed to attach logo: {logo_error}")
            # Continue without logo
        
        # Attach QR code
        try:
            qr_image = MIMEImage(qr_buffer.read())
            qr_image.add_header('Content-ID', '<qr_code>')
            qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.jpg')
            email.attach(qr_image)
            
            # Also attach as downloadable
            qr_buffer.seek(0)
            email.attach(f'{qr_id}_qr.jpg', qr_buffer.read(), 'image/jpeg')
        except Exception as qr_error:
            logger.error(f"Failed to attach QR code: {qr_error}")
            raise
        
        logger.info(f"Sending email to {recipients}")
        
        # Send email
        email.send(fail_silently=False)
        
        # Mark as sent in cache (7 days)
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"✓ Payment verification email sent successfully to {len(recipients)} recipients")
        
        return {
            'success': True,
            'recipients': recipients,
            'qr_id': qr_id,
            'email_count': len(recipients)
        }
        
    except Exception as e:
        logger.error(f"Failed to send payment verification email: {str(e)}", exc_info=True)
        
        # Retry logic
        try:
            # Exponential backoff: 60s, 120s, 240s
            countdown = 60 * (2 ** self.request.retries)
            logger.warning(f"Retrying payment verification email in {countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for payment verification email to {participant_data.get('email')}")
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True,
                'participant_id': participant_data.get('id')
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_team_payment_verification_emails_task(self, team_data, team_members_data):
    """
    Send payment verification emails to all team members
    """
    try:
        logger.info(f"Starting team verification emails for team {team_data.get('id')}")
        
        if not team_data or not team_members_data:
            logger.error("Invalid team data for payment verification")
            return {'success': False, 'error': 'Invalid team data'}
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        from .utils import generate_qr_code, attach_logo
        
        qr_id = f"t_{team_data['id']}"
        
        # Generate QR code once for all members
        logger.info(f"Generating team QR code for {qr_id}")
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("Failed to generate team QR code")
        
        sent_count = 0
        failed_emails = []
        
        # Send individual emails to each team member
        for member in team_members_data:
            if not member.get('email'):
                continue
            
            try:
                context = {
                    'member_name': member.get('name', 'Team Member'),
                    'team_name': team_data.get('name'),
                    'team_id': team_data['id'],
                    'qr_id': qr_id,
                    'team_competitions': team_data.get('competitions', []),
                }
                
                html_content = render_to_string('team_email_template.html', context)
                
                email = EmailMultiAlternatives(
                    subject=f"Payment Verified - Team {team_data.get('name')} - Innoverse",
                    body="Your team's payment has been verified. Please view this email in HTML format.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[member['email']]
                )
                
                email.attach_alternative(html_content, "text/html")
                
                try:
                    email = attach_logo(email)
                except Exception as logo_error:
                    logger.warning(f"Failed to attach logo for {member['email']}: {logo_error}")
                
                # Attach QR code
                qr_buffer.seek(0)
                qr_image = MIMEImage(qr_buffer.read())
                qr_image.add_header('Content-ID', '<qr_code>')
                qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.jpg')
                email.attach(qr_image)
                
                qr_buffer.seek(0)
                email.attach(f'{qr_id}_qr.jpg', qr_buffer.read(), 'image/jpeg')
                
                email.send(fail_silently=False)
                sent_count += 1
                logger.info(f"✓ Team email sent to {member['email']}")
                
            except Exception as member_error:
                logger.error(f"Failed to send email to team member {member['email']}: {member_error}")
                failed_emails.append(member['email'])
        
        logger.info(f"Team verification emails: {sent_count} sent, {len(failed_emails)} failed")
        
        return {
            'success': True,
            'sent_count': sent_count,
            'failed_emails': failed_emails,
            'team_id': team_data['id']
        }
        
    except Exception as e:
        logger.error(f"Failed to send team verification emails: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            logger.warning(f"Retrying team emails in {countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for team verification emails")
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True,
                'team_id': team_data.get('id')
            }