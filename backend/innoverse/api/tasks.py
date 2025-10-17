from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60,
    time_limit=300,
    soft_time_limit=240
)
def send_payment_verification_email_task(self, participant_data, team_data=None):
    """
    Celery task to send payment verification email with QR code
    """
    try:
        logger.info(f"[TASK START] Payment verification email for participant {participant_data.get('id')}")
        
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data - missing email")
            return {'success': False, 'error': 'Invalid participant data'}
        
        participant_id = participant_data['id']
        
        # Idempotency check (skip if cache fails)
        try:
            cache_key = f"payment_email_sent_{participant_id}"
            if cache.get(cache_key):
                logger.info(f"Email already sent for participant {participant_id}, skipping")
                return {'success': True, 'message': 'Already sent', 'duplicate': True}
        except Exception as cache_error:
            logger.warning(f"Cache check failed, continuing anyway: {cache_error}")
        
        # Import email utilities
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        import qrcode
        from io import BytesIO
        import os
        
        # Inline QR generation to avoid serialization issues
        def generate_qr_inline(data, save_filename=None):
            """Generate QR code inline"""
            try:
                logger.info(f"Generating QR code for: {data}")
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Save to buffer
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Save to disk if needed
                if save_filename:
                    qr_dir = settings.QR_CODE_ROOT
                    os.makedirs(qr_dir, exist_ok=True)
                    filepath = os.path.join(qr_dir, f"{save_filename}.png")
                    
                    with open(filepath, 'wb') as f:
                        img.save(f, format='PNG')
                    
                    logger.info(f"QR code saved to {filepath}")
                
                return buffer
                
            except Exception as e:
                logger.error(f"QR generation failed: {str(e)}", exc_info=True)
                return None
        
        # Inline logo attachment
        def attach_logo_inline(email):
            """Attach logo inline"""
            logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_image = MIMEImage(f.read())
                    logo_image.add_header('Content-ID', '<logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                    email.attach(logo_image)
                    logger.info("Logo attached")
            else:
                logger.warning(f"Logo not found at {logo_path}")
            
            return email
        
        # Prepare email recipients and context
        qr_id = f"p_{participant_id}"
        recipients = [participant_data['email']]
        
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_id,
            'participant_email': participant_data['email'],
            'qr_id': qr_id,
            'segments': participant_data.get('segments', []),
            'competitions': participant_data.get('competitions', []),
        }
        
        # Handle team data (should NOT be present for participant emails)
        if team_data:
            logger.warning("Team data should not be in participant email task!")
            # Ignore team_data in this task
        
        # Generate QR code
        logger.info(f"Generating QR code for {qr_id}")
        qr_buffer = generate_qr_inline(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("QR code generation failed")
        
        logger.info(f"QR buffer size: {qr_buffer.getbuffer().nbytes} bytes")
        
        # Render email template
        html_content = render_to_string('email_template.html', context)
        
        # Create email
        subject = "Payment Verified - Innoverse Registration"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your payment has been verified.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        try:
            email = attach_logo_inline(email)
        except Exception as logo_error:
            logger.warning(f"Logo attachment failed: {logo_error}")
        
        # Attach QR code
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        
        if not qr_data:
            raise ValueError("QR buffer is empty")
        
        logger.info(f"QR data size: {len(qr_data)} bytes")
        
        # Inline QR
        qr_image = MIMEImage(qr_data)
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
        email.attach(qr_image)
        
        # Downloadable QR
        email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
        
        logger.info(f"Sending email to {recipients}...")
        
        # Send email
        email.send(fail_silently=False)
        
        # Mark as sent
        cache.set(cache_key, True, timeout=604800)
        
        logger.info(f"✓ [SUCCESS] Email sent to {recipients}")
        
        return {
            'success': True,
            'recipients': recipients,
            'qr_id': qr_id,
            'participant_id': participant_id
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for participant {participant_data.get('id')}")
        return {'success': False, 'error': 'Task timeout'}
        
    except Exception as e:
        logger.error(f"[ERROR] Payment email failed: {str(e)}", exc_info=True)
        
        try:
            retry_count = self.request.retries
            countdown = 60 * (2 ** retry_count)
            logger.warning(f"Retrying in {countdown}s (attempt {retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)
            
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for participant {participant_data.get('id')}")
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
    time_limit=600,
    soft_time_limit=540
)
def send_team_payment_verification_emails_task(self, team_data, team_members_data):
    """
    Send payment verification emails to all team members
    """
    try:
        logger.info(f"[TASK START] Team verification emails for team {team_data.get('id')}")
        
        if not team_data or not team_members_data:
            logger.error("Invalid team data")
            return {'success': False, 'error': 'Invalid team data'}
        
        team_id = team_data['id']
        
        # Idempotency check (skip if cache fails)
        try:
            cache_key = f"team_payment_email_sent_{team_id}"
            if cache.get(cache_key):
                logger.info(f"Team emails already sent for {team_id}, skipping")
                return {'success': True, 'message': 'Already sent', 'duplicate': True}
        except Exception as cache_error:
            logger.warning(f"Cache check failed, continuing anyway: {cache_error}")
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        import qrcode
        from io import BytesIO
        import os
        
        # Inline QR generation
        def generate_qr_inline(data, save_filename=None):
            try:
                logger.info(f"Generating QR code for: {data}")
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                if save_filename:
                    qr_dir = settings.QR_CODE_ROOT
                    os.makedirs(qr_dir, exist_ok=True)
                    filepath = os.path.join(qr_dir, f"{save_filename}.png")
                    
                    with open(filepath, 'wb') as f:
                        img.save(f, format='PNG')
                    
                    logger.info(f"QR saved to {filepath}")
                
                return buffer
                
            except Exception as e:
                logger.error(f"QR generation failed: {str(e)}", exc_info=True)
                return None
        
        # Inline logo
        def attach_logo_inline(email):
            logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_image = MIMEImage(f.read())
                    logo_image.add_header('Content-ID', '<logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                    email.attach(logo_image)
            
            return email
        
        qr_id = f"t_{team_id}"
        
        # Generate team QR once
        logger.info(f"Generating team QR for {qr_id}")
        qr_buffer = generate_qr_inline(qr_id, qr_id)
        
        if not qr_buffer:
            raise ValueError("Team QR generation failed")
        
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        logger.info(f"Team QR size: {len(qr_data)} bytes")
        
        sent_count = 0
        failed_emails = []
        
        # Send to each member
        for member in team_members_data:
            member_email = member.get('email')
            if not member_email:
                logger.warning(f"Skipping member without email: {member.get('name')}")
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
                    email = attach_logo_inline(email)
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
                logger.error(f"Failed to send to {member_email}: {member_error}", exc_info=True)
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
        try:
            cache_key = f"reg_email_{participant_data['id']}_{payment_data.get('trx_id')}"
            if cache.get(cache_key):
                logger.info("Registration email already sent")
                return {'success': True, 'message': 'Already sent', 'duplicate': True}
        except Exception as cache_error:
            logger.warning(f"Cache check failed, continuing anyway: {cache_error}")

        
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
        try:
            cache.set(cache_key, True, timeout=604800)
        except Exception as cache_error:
            logger.warning(f"Failed to set cache: {cache_error}")
        
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