import qrcode
import os
from io import BytesIO
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.image import MIMEImage
import logging

logger = logging.getLogger(__name__)


def attach_logo(email):
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_image = MIMEImage(f.read())
            logo_image.add_header('Content-ID', '<logo>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            email.attach(logo_image)
            logger.info("Logo attached to email")
    else:
        logger.warning(f"Logo not found at {logo_path}")
    
    return email


def generate_qr_code(data, save_filename=None):
    """
    Generate QR code and return as BytesIO buffer
    
    Args:
        data: Data to encode in QR code
        save_filename: Optional filename to save QR code to disk (e.g., "p_123_qr")
    
    Returns:
        BytesIO: Buffer containing QR code image
    """
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
        
        # Save to buffer (always)
        buffer = BytesIO()
        img.save(buffer, format='PNG')  # Changed to PNG for better quality
        buffer.seek(0)
        
        # Optionally save to disk
        if save_filename:
            qr_dir = settings.QR_CODE_ROOT
            os.makedirs(qr_dir, exist_ok=True)
            
            filepath = os.path.join(qr_dir, f"{save_filename}.png")
            
            with open(filepath, 'wb') as f:
                img.save(f, format='PNG')
            
            logger.info(f"QR code saved to {filepath}")
        
        logger.info(f"QR code generated successfully, buffer size: {buffer.getbuffer().nbytes} bytes")
        return buffer
        
    except Exception as e:
        logger.error(f"Failed to generate QR code: {str(e)}", exc_info=True)
        return None


def send_payment_verification_email(participant, team=None):
    """
    SYNCHRONOUS version - for direct calling
    Send payment verification email with QR code
    """
    try:
        recipients = []
        qr_id = f"p_{participant.id}"
        
        context = {
            'participant_name': f"{participant.f_name} {participant.l_name}",
            'participant_id': participant.id,
            'participant_email': participant.email,
            'qr_id': qr_id,
            'segments': [reg.segment.segment_name for reg in participant.registrations.all()],
            'competitions': [comp.competition.competition for comp in participant.competition_registrations.all()],
        }
        
        recipients.append(participant.email)
        
        if team:
            qr_id = f"t_{team.id}"
            context['team_name'] = team.team_name
            context['team_id'] = team.id
            context['qr_id'] = qr_id
            
            team_members = team.members.all()
            for member in team_members:
                if member.email and member.email not in recipients:
                    recipients.append(member.email)
            
            context['team_competitions'] = [
                comp.competition.competition 
                for comp in team.team_competition_registrations.all()
            ]
            
            logger.info(f"Sending team email to {len(recipients)} recipients")
        
        # Generate QR code
        logger.info(f"Generating QR code for {qr_id}")
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        if not qr_buffer:
            logger.error("QR code generation failed!")
            return False
        
        logger.info(f"QR buffer size: {qr_buffer.getbuffer().nbytes} bytes")
        
        # Render HTML template
        html_content = render_to_string('email_template.html', context)
        
        # Create email
        subject = f"Payment Verified - Innoverse Registration"
        from_email = settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your payment has been verified. Please view this email in HTML format.",
            from_email=from_email,
            to=recipients
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        email = attach_logo(email)
        
        # Attach QR code as inline image
        qr_buffer.seek(0)  # CRITICAL: Reset buffer position
        qr_data = qr_buffer.read()
        
        qr_image = MIMEImage(qr_data)
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.png')
        email.attach(qr_image)
        
        # Also attach QR code as downloadable attachment
        email.attach(f'{qr_id}_qr.png', qr_data, 'image/png')
        
        logger.info(f"Sending email to {len(recipients)} recipients: {recipients}")
        email.send(fail_silently=False)
        
        logger.info(f"✓ Email sent successfully to {recipients}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}", exc_info=True)
        return False


def send_registration_confirmation_email(participant, payment, team=None, team_members=None, team_competitions=None):
    """Send registration confirmation email"""
    try:
        context = {
            'participant_name': f"{participant.f_name} {participant.l_name}",
            'participant_id': participant.id,
            'participant_email': participant.email,
            'participant_phone': participant.phone,
            'participant_institution': participant.institution,
            'participant_guardian_phone': participant.guardian_phone,
            'trx_id': payment.trx_id,
            'amount': payment.amount,
            'payment_phone': payment.phone,
            'segments': [reg.segment.segment_name for reg in participant.registrations.all()],
            'competitions': [comp.competition.competition for comp in participant.competition_registrations.all()],
        }
        
        if team:
            context['team_name'] = team.team_name
            context['team_id'] = team.id
            
            if team_members:
                context['team_members'] = [
                    {
                        'name': f"{member.f_name} {member.l_name}",
                        'institution': member.institution
                    }
                    for member in team_members if not member.is_leader
                ]
            
            if team_competitions:
                context['team_competitions'] = [comp.competition.competition for comp in team_competitions]
        
        html_content = render_to_string('registration_email_template.html', context)
        
        subject = "Registration Successful - Innoverse"
        if team:
            subject = f"Registration Successful - Team {team.team_name} - Innoverse"
        
        from_email = settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for registering for Innoverse! Please view this email in HTML format.",
            from_email=from_email,
            to=[participant.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email = attach_logo(email)
        
        email.send(fail_silently=False)
        logger.info(f"Registration confirmation email sent to {participant.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send registration confirmation email: {str(e)}", exc_info=True)
        return False