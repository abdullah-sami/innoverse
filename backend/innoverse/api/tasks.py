from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


def generate_qr_with_ticket_template(qr_id, settings):
    """
    Generate QR code and overlay it on ticket template
    Returns: (qr_buffer, ticket_buffer)
    """
    try:
        import qrcode
        from io import BytesIO
        from PIL import Image
        import os
        
        logger.info(f"Generating QR code for: {qr_id}")
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_id)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save plain QR to buffer (for inline display)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Load ticket template
        template_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes', 'qr_ticket_template.jpg')
        
        if os.path.exists(template_path):
            # Open template
            template = Image.open(template_path).convert('RGB')
            
            # Resize QR code to fit nicely (e.g., 250x250 px)
            qr_img_pil = qr_img.resize((300, 300), Image.Resampling.LANCZOS)
            
            # Calculate position (centered horizontally and vertically)
            template_width, template_height = template.size
            qr_width, qr_height = qr_img_pil.size

            x_position = (template_width - qr_width) // 2  # Center horizontally
            y_position = (template_height - qr_height) // 2  # Center vertically
            
            # Paste QR code onto template
            template.paste(qr_img_pil, (x_position, y_position))
            
            # Save ticket with QR to buffer
            ticket_buffer = BytesIO()
            template.save(ticket_buffer, format='JPEG', quality=95)
            ticket_buffer.seek(0)
            
            # Also save to disk
            qr_dir = settings.QR_CODE_ROOT
            os.makedirs(qr_dir, exist_ok=True)
            
            # Save plain QR
            qr_filepath = os.path.join(qr_dir, f"{qr_id}_qr.png")
            with open(qr_filepath, 'wb') as f:
                qr_buffer_copy = BytesIO()
                qr_img.save(qr_buffer_copy, format='PNG')
                qr_buffer_copy.seek(0)
                f.write(qr_buffer_copy.read())
            
            # Save ticket with QR
            ticket_filepath = os.path.join(qr_dir, f"{qr_id}_ticket.jpg")
            template.save(ticket_filepath, format='JPEG', quality=95)
            
            logger.info(f"QR and ticket saved: {qr_filepath}, {ticket_filepath}")
            
            # Reset buffers
            qr_buffer.seek(0)
            ticket_buffer.seek(0)
            
            return qr_buffer, ticket_buffer
        else:
            logger.warning(f"Ticket template not found at {template_path}, using plain QR")
            qr_buffer.seek(0)
            return qr_buffer, None
            
    except Exception as e:
        logger.error(f"QR/Ticket generation failed: {str(e)}", exc_info=True)
        return None, None


def attach_logo_inline(email, settings):
    """Attach logo inline"""
    import os
    from email.mime.image import MIMEImage
    
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


@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60,
    time_limit=300,
    soft_time_limit=240
)
def send_payment_verification_email_task(self, participant_data, is_team_leader=False):
    """
    Send payment verification email for PARTICIPANT (solo competitions)
    Team leaders will receive this separately from team email
    """
    try:
        logger.info(f"[TASK START] Payment verification email for participant {participant_data.get('id')}")
        
        if not participant_data or not participant_data.get('email'):
            logger.error("Invalid participant data - missing email")
            return {'success': False, 'error': 'Invalid participant data'}
        
        participant_id = participant_data['id']
        
        # Idempotency check
        try:
            cache_key = f"payment_email_sent_{participant_id}"
            if cache.get(cache_key):
                logger.info(f"Email already sent for participant {participant_id}, skipping")
                return {'success': True, 'message': 'Already sent', 'duplicate': True}
        except Exception as cache_error:
            logger.warning(f"Cache check failed: {cache_error}")
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        
        # Generate QR and ticket
        qr_id = f"p_{participant_id}"
        qr_buffer, ticket_buffer = generate_qr_with_ticket_template(qr_id, settings)
        
        if not qr_buffer:
            raise ValueError("QR code generation failed")
        
        # Prepare context
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_id,
            'participant_email': participant_data['email'],
            'qr_id': qr_id,
            'segments': participant_data.get('segments', []),
            'competitions': participant_data.get('competitions', []),
            'is_team_leader': is_team_leader,
        }
        
        # Render email
        html_content = render_to_string('email_template.html', context)
        
        subject = "Payment Verified - Solo Competitions - Innoverse"
        if is_team_leader:
            subject = "Payment Verified - Your Solo Competitions - Innoverse"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your payment has been verified.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[participant_data['email']]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        try:
            email = attach_logo_inline(email, settings)
        except Exception:
            pass
        
        # Attach inline QR (for email display)
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        
        qr_image = MIMEImage(qr_data)
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
        email.attach(qr_image)
        
        # Attach downloadable QR ticket (if template exists)
        if ticket_buffer:
            ticket_buffer.seek(0)
            ticket_data = ticket_buffer.read()
            email.attach(f'{qr_id}_ticket.jpg', ticket_data, 'image/jpeg')
            logger.info(f"Ticket attached ({len(ticket_data)} bytes)")
        else:
            # Fallback: attach plain QR as download
            email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
        
        # Send
        email.send(fail_silently=False)
        
        # Cache
        try:
            cache.set(cache_key, True, timeout=604800)
        except Exception:
            pass
        
        logger.info(f"✓ [SUCCESS] Participant email sent to {participant_data['email']}")
        
        return {
            'success': True,
            'recipient': participant_data['email'],
            'qr_id': qr_id,
            'participant_id': participant_id
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for participant {participant_data.get('id')}")
        return {'success': False, 'error': 'Task timeout'}
        
    except Exception as e:
        logger.error(f"[ERROR] Payment email failed: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for participant {participant_data.get('id')}")
            return {'success': False, 'error': str(e), 'max_retries_exceeded': True}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,
    soft_time_limit=540
)
def send_team_payment_verification_emails_task(self, team_data, team_members_data):
    """
    Send payment verification email for TEAM competitions
    Uses CC to send one email to all members efficiently
    """
    try:
        logger.info(f"[TASK START] Team verification email for team {team_data.get('id')}")
        
        if not team_data or not team_members_data:
            logger.error("Invalid team data")
            return {'success': False, 'error': 'Invalid team data'}
        
        team_id = team_data['id']
        
        # Idempotency check
        try:
            cache_key = f"team_payment_email_sent_{team_id}"
            if cache.get(cache_key):
                logger.info(f"Team email already sent for {team_id}, skipping")
                return {'success': True, 'message': 'Already sent', 'duplicate': True}
        except Exception as cache_error:
            logger.warning(f"Cache check failed: {cache_error}")
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from email.mime.image import MIMEImage
        
        # Generate team QR and ticket
        qr_id = f"t_{team_id}"
        qr_buffer, ticket_buffer = generate_qr_with_ticket_template(qr_id, settings)
        
        if not qr_buffer:
            raise ValueError("Team QR generation failed")
        
        # Prepare recipient lists
        leader_email = None
        cc_emails = []
        
        for member in team_members_data:
            email = member.get('email')
            if not email:
                continue
            
            if member.get('is_leader'):
                leader_email = email
            else:
                cc_emails.append(email)
        
        if not leader_email:
            logger.error("No team leader email found")
            return {'success': False, 'error': 'No team leader email'}
        
        # Prepare context
        context = {
            'team_name': team_data.get('name'),
            'team_id': team_id,
            'qr_id': qr_id,
            'team_competitions': team_data.get('competitions', []),
            'team_members': [
                {'name': m.get('name'), 'is_leader': m.get('is_leader')}
                for m in team_members_data
            ],
        }
        
        # Render email
        html_content = render_to_string('email_template.html', context)
        
        subject = f"Payment Verified - Team {team_data.get('name')} - Innoverse"
        
        # Create email with CC
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your team's payment has been verified.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[leader_email],
            cc=cc_emails  # All other members as CC
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        try:
            email = attach_logo_inline(email, settings)
        except Exception:
            pass
        
        # Attach inline QR
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        
        qr_image = MIMEImage(qr_data)
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
        email.attach(qr_image)
        
        # Attach ticket
        if ticket_buffer:
            ticket_buffer.seek(0)
            ticket_data = ticket_buffer.read()
            email.attach(f'{qr_id}_ticket.jpg', ticket_data, 'image/jpeg')
            logger.info(f"Team ticket attached ({len(ticket_data)} bytes)")
        else:
            email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
        
        # Send (ONE email to all via CC)
        email.send(fail_silently=False)
        
        # Cache
        try:
            cache.set(cache_key, True, timeout=604800)
        except Exception:
            pass
        
        recipients_count = len(cc_emails) + 1
        logger.info(f"✓ [SUCCESS] Team email sent to {recipients_count} members (1 TO + {len(cc_emails)} CC)")
        
        return {
            'success': True,
            'team_id': team_id,
            'recipients_count': recipients_count,
            'leader': leader_email,
            'cc_count': len(cc_emails)
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Team email failed: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical(f"Max retries exceeded for team {team_data.get('id')}")
            return {'success': False, 'error': str(e), 'max_retries_exceeded': True}


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
            logger.warning(f"Cache check failed: {cache_error}")
        
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        from django.conf import settings
        from email.mime.image import MIMEImage
        import os
        
        # Attach logo helper
        def attach_logo(email):
            logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_image = MIMEImage(f.read())
                    logo_image.add_header('Content-ID', '<logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                    email.attach(logo_image)
            return email
        
        context = {
            'participant_name': participant_data.get('name', 'Participant'),
            'participant_id': participant_data['id'],
            'participant_email': participant_data['email'],
            'participant_phone': participant_data.get('phone', ''),
            'participant_institution': participant_data.get('institution', ''),
            'participant_guardian_phone': participant_data.get('guardian_phone', ''),
            'trx_id': payment_data.get('trx_id', ''),
            'amount': payment_data.get('amount', ''),
            'method': payment_data.get('method', ''),
            'payment_phone': payment_data.get('phone', ''),
            'segments': participant_data.get('segments', []),
            'competitions': participant_data.get('competitions', []),
        }
        
        # Prepare CC list for team
        cc_emails = []
        
        if team_data:
            context.update({
                'team_name': team_data.get('name', ''),
                'team_id': team_data.get('id', ''),
                'team_members': team_members_data or [],
                'team_competitions': team_competitions or []
            })
            
            # Add team members as CC
            if team_members_data:
                for member in team_members_data:
                    member_email = member.get('email')
                    if member_email and member_email != participant_data['email']:
                        cc_emails.append(member_email)
        
        html_content = render_to_string('registration_email_template.html', context)
        
        subject = "Registration Successful - Innoverse"
        if team_data:
            subject = f"Registration Successful - Team {team_data.get('name')} - Innoverse"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for registering for Innoverse!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[participant_data['email']],
            cc=cc_emails if cc_emails else None
        )
        
        email.attach_alternative(html_content, "text/html")
        email = attach_logo(email)
        email.send(fail_silently=False)
        
        # Cache
        try:
            cache.set(cache_key, True, timeout=604800)
        except Exception:
            pass
        
        logger.info(f"✓ [SUCCESS] Registration email sent to {participant_data['email']} (CC: {len(cc_emails)})")
        
        return {
            'success': True,
            'recipient': participant_data['email'],
            'cc_count': len(cc_emails),
            'participant_id': participant_data['id']
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Registration email failed: {str(e)}", exc_info=True)
        
        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=countdown)
        except MaxRetriesExceededError:
            logger.critical("Max retries exceeded for registration email")
            return {'success': False, 'error': str(e), 'max_retries_exceeded': True}