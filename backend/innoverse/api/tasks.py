from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60,
    time_limit=300,  # 5 minutes hard limit
    soft_time_limit=240  # 4 minutes soft limit
)
def send_payment_verification_email_task(self, participant_data, team_data=None):
    """
    Celery task to send payment verification email with QR code
    
    Args:
        participant_data: Dict with participant info
        team_data: Optional dict with team info
    """
    try:
        logger.info(f"[TASK START] Payment verification email for participant {participant_data.get('id')}")
        
        # Validate input data
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data - missing email")
            return {'success': False, 'error': 'Invalid participant data'}
        
        participant_id = participant_data['id']
        
        # Idempotency check - prevent duplicate sends
        cache_key = f"payment_email_sent_{participant_id}"
        if cache.get(cache_key):
            logger.info(f"Email already sent for participant {participant_id}, skipping")
            return {'success': True, 'message': 'Already sent', 'duplicate': True}
        
        # Import here to avoid circular imports
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        from .utils import generate_qr_code, attach_logo
        
        # Prepare email data
        qr_id = f"p_{participant_id}"
        recipients = [participant_data['email']]
        
        logger.info(f"Preparing context for participant {participant_id}")
        
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_id,
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
            member_emails = team_data.get('member_emails', [])
            for email in member_emails:
                if email and email not in recipients:
                    recipients.append(email)
            
            logger.info(f"Team email - {len(recipients)} recipients")
        
        # Generate QR code
        logger.info(f"Generating QR code for {qr_id}")
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("QR code generation failed")
        
        qr_buffer_size = qr_buffer.getbuffer().nbytes
        logger.info(f"QR code generated: {qr_buffer_size} bytes")
        
        # Render email template
        logger.info("Rendering email template")
        html_content = render_to_string('email_template.html', context)
        
        # Create email
        subject = "Payment Verified - Innoverse Registration"
        if team_data:
            subject = f"Payment Verified - Team {team_data.get('name')} - Innoverse"
        
        logger.info(f"Creating email for {len(recipients)} recipients")
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your payment has been verified.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        try:
            email = attach_logo(email)
            logger.info("Logo attached")
        except Exception as logo_error:
            logger.warning(f"Logo attachment failed: {logo_error}")
        
        # Attach QR code
        logger.info("Attaching QR code")
        qr_buffer.seek(0)  # CRITICAL: Reset buffer
        qr_data = qr_buffer.read()
        
        if not qr_data:
            raise ValueError("QR buffer is empty after read")
        
        logger.info(f"QR data read: {len(qr_data)} bytes")
        
        # Inline QR code
        qr_image = MIMEImage(qr_data)
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
        email.attach(qr_image)
        
        # Downloadable QR code
        email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
        
        logger.info("QR code attached, sending email...")
        
        # Send email
        email.send(fail_silently=False)
        
        # Mark as sent in cache (7 days)
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"✓ [SUCCESS] Email sent to {len(recipients)} recipients")
        
        return {
            'success': True,
            'recipients': recipients,
            'qr_id': qr_id,
            'participant_id': participant_id
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task exceeded soft time limit for participant {participant_data.get('id')}")
        return {
            'success': False,
            'error': 'Task timeout',
            'participant_id': participant_data.get('id')
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Payment email task failed: {str(e)}", exc_info=True)
        
        # Retry with exponential backoff
        try:
            retry_count = self.request.retries
            countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
            
            logger.warning(
                f"Retrying in {countdown}s (attempt {retry_count + 1}/{self.max_retries})"
            )
            
            raise self.retry(exc=e, countdown=countdown)
            
        except MaxRetriesExceededError:
            logger.critical(
                f"Max retries exceeded for participant {participant_data.get('id')}"
            )
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True,
                'participant_id': participant_data.get('id')
            }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes for team emails
    soft_time_limit=540
)
def send_team_payment_verification_emails_task(self, team_data, team_members_data):
    """
    Send payment verification emails to all team members
    
    Args:
        team_data: Dict with team info
        team_members_data: List of dicts with member info
    """
    try:
        logger.info(f"[TASK START] Team verification emails for team {team_data.get('id')}")
        
        if not team_data or not team_members_data:
            logger.error("Invalid team data")
            return {'success': False, 'error': 'Invalid team data'}
        
        team_id = team_data['id']
        
        # Idempotency check
        cache_key = f"team_payment_email_sent_{team_id}"
        if cache.get(cache_key):
            logger.info(f"Team emails already sent for {team_id}, skipping")
            return {'success': True, 'message': 'Already sent', 'duplicate': True}
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        from .utils import generate_qr_code, attach_logo
        
        qr_id = f"t_{team_id}"
        
        # Generate QR code once
        logger.info(f"Generating team QR code for {qr_id}")
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("Team QR code generation failed")
        
        # Read QR data once
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        logger.info(f"Team QR generated: {len(qr_data)} bytes")
        
        sent_count = 0
        failed_emails = []
        
        # Send to each member
        for member in team_members_data:
            member_email = member.get('email')
            if not member_email:
                continue
            
            try:
                context = {
                    'participant_name': member.get('name', 'Team Member'),
                    'team_name': team_data.get('name'),
                    'team_id': team_id,
                    'qr_id': qr_id,
                    'team_competitions': team_data.get('competitions', []),
                }
                
                html_content = render_to_string('email_template.html', context)
                
                email = EmailMultiAlternatives(
                    subject=f"Payment Verified - Team {team_data.get('name')} - Innoverse",
                    body="Your team's payment has been verified.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[member_email]
                )
                
                email.attach_alternative(html_content, "text/html")
                
                try:
                    email = attach_logo(email)
                except Exception:
                    pass
                
                # Attach QR
                qr_image = MIMEImage(qr_data)
                qr_image.add_header('Content-ID', '<qr_code>')
                qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
                email.attach(qr_image)
                email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
                
                email.send(fail_silently=False)
                sent_count += 1
                logger.info(f"✓ Sent to {member_email}")
                
            except Exception as member_error:
                logger.error(f"Failed to send to {member_email}: {member_error}")
                failed_emails.append(member_email)
        
        # Mark as sent
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"✓ [SUCCESS] Team emails: {sent_count} sent, {len(failed_emails)} failed")
        
        return {
            'success': True,
            'sent_count': sent_count,
            'failed_emails': failed_emails,
            'team_id': team_id
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Team email task failed: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for team {team_data.get('id')}")
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True,
                'team_id': team_data.get('id')
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_registration_email_task(self, participant_data, payment_data, team_data=None, 
                                 team_members_data=None, team_competitions=None):
    """Send registration confirmation email"""
    try:
        logger.info(f"[TASK START] Registration email for participant {participant_data.get('id')}")
        
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data")
            return {'success': False, 'error': 'Invalid participant data'}
        
        # Idempotency check
        cache_key = f"reg_email_{participant_data['id']}_{payment_data.get('trx_id')}"
        if cache.get(cache_key):
            logger.info("Registration email already sent")
            return {'success': True, 'message': 'Already sent', 'duplicate': True}
        
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from .utils import attach_logo
        
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
        
        if team_data:
            context.update({
                'team_name': team_data.get('name', ''),
                'team_id': team_data.get('id', ''),
                'team_members': team_members_data or [],
                'team_competitions': team_competitions or []
            })
        
        html_content = render_to_string('registration_email_template.html', context)
        
        subject = "Registration Successful - Innoverse"
        if team_data:
            subject = f"Registration Successful - Team {team_data.get('name')} - Innoverse"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for registering for Innoverse!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[participant_data['email']]
        )
        
        email.attach_alternative(html_content, "text/html")
        email = attach_logo(email)
        email.send(fail_silently=False)
        
        # Mark as sent
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"✓ [SUCCESS] Registration email sent to {participant_data['email']}")
        
        return {
            'success': True,
            'recipient': participant_data['email'],
            'participant_id': participant_data['id']
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Registration email failed: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical("Max retries exceeded for registration email")
            return {
                'success': False,
                'error': str(e),
                'max_retries_exceeded': True,
                'participant_id': participant_data.get('id')
            }