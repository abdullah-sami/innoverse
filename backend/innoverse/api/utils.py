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


def generate_qr_code(data, participant_id=None):
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
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    
    
    if participant_id:
        qr_dir = settings.QR_CODE_ROOT
        os.makedirs(qr_dir, exist_ok=True)
        
        filename = f"{participant_id}_qr.jpg"
        filepath = os.path.join(qr_dir, filename)
        
        with open(filepath, 'wb') as f:
            img.save(f, format='JPEG')
        
        logger.info(f"QR code saved to {filepath}")
    
    return buffer


def send_payment_verification_email(participant, team=None):
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
        
        # Get all team members
        team_members = team.members.all()
        for member in team_members:
            if member.email and member.email not in recipients:
                recipients.append(member.email)
        
        logger.info(f"Sending team email to {len(recipients)} recipients")
    
    # Generate QR code
    qr_buffer = generate_qr_code(qr_id, qr_id)
    
    # Render HTML template
    html_content = render_to_string('email_template.html', context)
    
    # Create email
    subject = f"Payment Verified - Innoverse Registration"
    from_email = settings.DEFAULT_FROM_EMAIL
    
    # Create email with HTML content
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
    qr_image = MIMEImage(qr_buffer.read())
    qr_image.add_header('Content-ID', '<qr_code>')
    qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.jpg')
    email.attach(qr_image)
    
    # Also attach QR code as downloadable attachment
    qr_buffer.seek(0)
    email.attach(f'{qr_id}_qr.jpg', qr_buffer.read(), 'image/jpeg')
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {recipients}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_registration_confirmation_email(participant, payment, team=None, team_members=None, team_competitions=None):

    # Prepare context for email template
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
    
    # Render HTML template
    html_content = render_to_string('registration_email_template.html', context)
    
    # Create email
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
    
    # Attach logo
    email = attach_logo(email)
    
    try:
        email.send(fail_silently=False)
        logger.info(f"Registration confirmation email sent to {participant.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send registration confirmation email: {str(e)}")
        return False


def send_team_registration_confirmation_emails(team, team_members, team_competitions, payment):
    """
    Send registration confirmation emails to all team members
    """
    if not team_members:
        logger.warning(f"No team members found for team {team.id}")
        return False
    
    success_count = 0
    
    for member in team_members:
        if not member.email:
            continue
        
        context = {
            'participant_name': f"{member.f_name} {member.l_name}",
            'participant_id': member.id,
            'participant_email': member.email,
            'participant_phone': member.phone,
            'participant_institution': member.institution,
            'team_name': team.team_name,
            'team_id': team.id,
            'trx_id': payment.trx_id,
            'amount': payment.amount,
            'payment_phone': payment.phone,
            'team_competitions': [comp.competition.competition for comp in team_competitions],
            'team_members': [
                {
                    'name': f"{m.f_name} {m.l_name}",
                    'institution': m.institution
                }
                for m in team_members if m.id != member.id
            ]
        }
        
        # Render HTML template
        html_content = render_to_string('registration_email_template.html', context)
        
        # Create email
        role = "Team Leader" if member.is_leader else "Team Member"
        subject = f"Registration Successful - {role} - Team {team.team_name} - Innoverse"
        from_email = settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for registering for Innoverse! Please view this email in HTML format.",
            from_email=from_email,
            to=[member.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        email = attach_logo(email)
        
        try:
            email.send(fail_silently=False)
            logger.info(f"Registration confirmation email sent to team member {member.email}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send registration confirmation email to {member.email}: {str(e)}")
    
    return success_count > 0



def send_team_payment_verification_emails(team):
    """
    Send payment verification email to all team members
    """
    qr_id = f"t_{team.id}"
    team_members = team.members.all()
    
    if not team_members.exists():
        logger.warning(f"No team members found for team {team.id}")
        return False
    
    # Get leader info for context
    leader = team_members.filter(is_leader=True).first()
    
    for member in team_members:
        if not member.email:
            continue
            
        context = {
            'participant_name': f"{member.f_name} {member.l_name}",
            'participant_id': member.id,
            'participant_email': member.email,
            'team_name': team.team_name,
            'team_id': team.id,
            'qr_id': qr_id,
            'competitions': [comp.competition.competition for comp in team.team_competition_registrations.all()],
        }
        
        # Generate QR code
        qr_buffer = generate_qr_code(qr_id, qr_id)
        
        # Render HTML template
        html_content = render_to_string('email_template.html', context)
        
        # Create email
        subject = f"Payment Verified - Team {team.team_name} - Innoverse"
        from_email = settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Your team payment has been verified. Please view this email in HTML format.",
            from_email=from_email,
            to=[member.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Attach logo
        email = attach_logo(email)
        
        # Attach QR code as inline image
        qr_image = MIMEImage(qr_buffer.read())
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'{qr_id}_qr.jpg')
        email.attach(qr_image)
        
        # Also attach QR code as downloadable attachment
        qr_buffer.seek(0)
        email.attach(f'{qr_id}_qr.jpg', qr_buffer.read(), 'image/jpeg')
        
        try:
            email.send(fail_silently=False)
            logger.info(f"Email sent to team member {member.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {member.email}: {str(e)}")
    
    return True