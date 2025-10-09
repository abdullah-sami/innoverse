import logging
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Participant, Team, EntryStatus, Gift, GiftStatus
from .serializers import (
    ParticipantDetailSerializer,
    ParticipantListSerializer,
    TeamListSerializer,
    PaymentVerificationSerializer,
    CompleteRegistrationSerializer,
    EntryStatusSerializer,
    GiftStatusSerializer
)
from event.models import Coupons, Segment, Competition, TeamCompetition
from event.serializers import SegmentSerializer, CompetitionSerializer, TeamCompetitionSerializer
from api.models import Volunteer
from participant.models import Registration, CompetitionRegistration, TeamCompetitionRegistration, Payment, TeamParticipant
from participant.serializers import ParticipantSerializer, TeamSerializer

logger = logging.getLogger(__name__)



class IsAdminVolunteer(IsAuthenticated):
    """Permission class that allows only admin volunteers"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        try:
            volunteer = Volunteer.objects.get(user=request.user)
            return volunteer.role.role_name.lower() == 'admin'
        except Volunteer.DoesNotExist:
            return False





def parse_full_name(full_name):
    name_parts = full_name.strip().split(maxsplit=1)
    f_name = name_parts[0]
    l_name = name_parts[1] if len(name_parts) > 1 else ""
    return f_name, l_name


def get_entity_info(participant=None, team=None):
    info = {}
    
    if participant:
        info['participant'] = {
            'id': participant.id,
            'name': f"{participant.f_name} {participant.l_name}",
            'email': participant.email,
            'phone': participant.phone,
            'institution': participant.institution,
            'payment_verified': participant.payment_verified
        }
        
        # Auto-detect team if not provided
        if not team:
            team = Team.objects.filter(members__email=participant.email).first()
    
    if team:
        info['team'] = {
            'id': team.id,
            'name': team.team_name,
            'member_count': team.members.count(),
            'payment_verified': team.payment_verified,
            'members': [
                {
                    'name': f"{member.f_name} {member.l_name}",
                    'email': member.email,
                    'is_leader': member.is_leader
                }
                for member in team.members.all()
            ]
        }
    
    return info


def parse_id_parameter(id_param):
    if id_param.startswith("p_"):
        return 'participant', id_param.split("_")[1]
    elif id_param.startswith("t_"):
        return 'team', id_param.split("_")[1]
    else:
        raise ValueError("Invalid ID format. Use 'p_' for participant or 't_' for team")


def get_entity_by_id(id_param):
    entity_type, entity_id = parse_id_parameter(id_param)
    
    if entity_type == 'participant':
        participant = Participant.objects.get(id=entity_id)
        team = Team.objects.filter(members__email=participant.email).first()
        return participant, team
    else:
        team = Team.objects.get(id=entity_id)
        return None, team





class RegisterViewSet(viewsets.ViewSet):
    
    permission_classes = [AllowAny]
    
    def list(self, request):
        return Response({
            "message": "Registration endpoint is ready",
            "method": "POST",
            "endpoint": "/api/register/"
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        serializer = CompleteRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        try:
            with transaction.atomic():
                coupon = validated_data.get('coupon')
                
                # Create main participant (team leader if team competition)
                participant = self._create_participant(validated_data['participant'])
                
                # Record payment with coupon discount
                participant_payment = self._create_payment(
                    validated_data['payment'],
                    participant=participant,
                    coupon=coupon
                )
                
                # Register for segments and solo competitions
                self._register_segments(participant, validated_data.get('segment', []))
                self._register_competitions(participant, validated_data.get('competition', []))
                
                # Handle team competition registration if provided
                team = None
                team_payment = None
                team_members = None
                team_competitions = None
                
                if 'team_competition' in validated_data:
                    team, team_payment = self._handle_team_competition(
                        validated_data['team_competition'],
                        validated_data['payment'],
                        participant,
                        coupon
                    )
                    team_members = team.members.all()
                    team_competitions = team.team_competition_registrations.all()

                # Update coupon usage count
                self._update_coupon(coupon)

                # Build response data
                response_data = self._build_response_data(
                    participant, participant_payment, team, team_payment, 
                    validated_data, coupon
                )
                
                # Send confirmation emails
                self._send_confirmation_emails(
                    response_data, participant, participant_payment, 
                    team, team_members, team_competitions, team_payment
                )

                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Registration failed",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_participant(self, participant_data):
        f_name, l_name = parse_full_name(participant_data['full_name'])
        
        return Participant.objects.create(
            f_name=f_name,
            l_name=l_name,
            gender=participant_data['gender'],
            email=participant_data['email'],
            phone=participant_data['phone'],
            age=participant_data['age'],
            institution=participant_data['institution'],
            address=participant_data.get('address', ''),
            t_shirt_size=participant_data.get('t_shirt_size', ''),
            payment_verified=False
        )
    
    def _create_payment(self, payment_data, participant=None, team=None, coupon=None):
        return Payment.objects.create(
            participant=participant,
            team=team,
            phone=payment_data['phone'],
            amount=payment_data['amount'],
            trx_id=payment_data['trx_id'],
            coupon=coupon
        )
    
    def _register_segments(self, participant, segment_codes):
        for code in segment_codes:
            segment = Segment.objects.get(code=code)
            Registration.objects.create(
                participant=participant,
                segment=segment
            )
    
    def _register_competitions(self, participant, competition_codes):
        for code in competition_codes:
            competition = Competition.objects.get(code=code)
            CompetitionRegistration.objects.create(
                participant=participant,
                competition=competition
            )
    
    def _handle_team_competition(self, team_competition_data, payment_data, leader_participant, coupon=None):
        team_info = team_competition_data['team']
        
        team = Team.objects.create(
            team_name=team_info['team_name'],
            payment_verified=False
        )
        
        TeamParticipant.objects.create(
            f_name=leader_participant.f_name,
            l_name=leader_participant.l_name,
            gender=leader_participant.gender,
            email=leader_participant.email,
            phone=leader_participant.phone,
            age=leader_participant.age,
            institution=leader_participant.institution,
            address=leader_participant.address,
            t_shirt_size=leader_participant.t_shirt_size,
            team=team,
            is_leader=True
        )
        
        for member_data in team_info['participant']:
            f_name, l_name = parse_full_name(member_data['full_name'])
            
            TeamParticipant.objects.create(
                f_name=f_name,
                l_name=l_name,
                gender=member_data['gender'],
                email=member_data.get('email', ''),
                phone=member_data['phone'],
                age=member_data['age'],
                institution=member_data['institution'],
                address=member_data.get('address', ''),
                t_shirt_size=member_data.get('t_shirt_size', ''),
                team=team,
                is_leader=False
            )
        
        team_payment = self._create_payment(payment_data, team=team, coupon=coupon)
        
        for competition_code in team_competition_data['competition']:
            competition = TeamCompetition.objects.get(code=competition_code)
            TeamCompetitionRegistration.objects.create(
                team=team,
                competition=competition
            )
        
        return team, team_payment
    
    def _update_coupon(self, coupon):
        if coupon and coupon.coupon_number > 0:
            coupon.coupon_number -= 1
            coupon.save()
            return True
        return False
    
    def _build_response_data(self, participant, participant_payment, team, team_payment, validated_data, coupon):
        response_data = {
            "success": True,
            "message": "Registration completed successfully",
            "data": {
                "participant": {
                    "id": participant.id,
                    "name": f"{participant.f_name} {participant.l_name}",
                    "email": participant.email,
                    "payment_verified": participant.payment_verified
                },
                "payment": {
                    "coupon": coupon.coupon_code if coupon else None,
                    "discount": str(coupon.discount) if coupon else None,
                    "trx_id": participant_payment.trx_id,
                    "amount": str(participant_payment.amount)
                },
                "segments": validated_data.get('segment', []),
                "competitions": validated_data.get('competition', [])
            }
        }
        
        if team:
            response_data["data"]["team"] = {
                "id": team.id,
                "name": team.team_name,
                "payment_verified": team.payment_verified,
                "members_count": team.members.count(),
                "competitions": validated_data['team_competition']['competition']
            }
            response_data["data"]["team_payment"] = {
                "trx_id": team_payment.trx_id,
                "amount": str(team_payment.amount)
            }
        
        return response_data
    
    def _send_confirmation_emails(self, response_data, participant, participant_payment, 
                                  team, team_members, team_competitions, team_payment):
        from .utils import send_registration_confirmation_email, send_team_registration_confirmation_emails

        try:
            # Send individual participant email
            email_sent = send_registration_confirmation_email(participant, participant_payment)
            
            if email_sent:
                response_data["email_sent"] = True
                response_data["message"] += " Confirmation email sent."
            else:
                response_data["email_warning"] = "Registration successful but email failed to send"
            
            # Send team emails if team exists
            if team:
                team_email_sent = send_team_registration_confirmation_emails(
                    team, team_members, team_competitions, team_payment
                )
                
                if team_email_sent:
                    response_data["team_email_sent"] = True
                    response_data["message"] += " Team confirmation emails sent to all members."
                else:
                    response_data["team_email_warning"] = "Team registration successful but team emails failed to send"
                    
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            response_data["email_warning"] = "Registration successful but email(s) failed to send"




class ParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminVolunteer]
    
    def get_queryset(self):
        queryset = Participant.objects.all().select_related().prefetch_related(
            'registrations__segment',
            'competition_registrations__competition',
            'gift_status__gift',
            'entry_status'
        )
        
        segment_code = self.request.query_params.get('segment')
        competition_code = self.request.query_params.get('competition')
        payment_verified = self.request.query_params.get('payment_verified')
        search = self.request.query_params.get('search')
        
        if segment_code:
            queryset = queryset.filter(registrations__segment__code=segment_code).distinct()
        
        if competition_code:
            queryset = queryset.filter(competition_registrations__competition__code=competition_code).distinct()
        
        if payment_verified is not None:
            is_verified = payment_verified.lower() == 'true'
            queryset = queryset.filter(payment_verified=is_verified)
        
        if search:
            queryset = queryset.filter(
                Q(f_name__icontains=search) |
                Q(l_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-id')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ParticipantDetailSerializer
        return ParticipantListSerializer
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'success': True,
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching participants list: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch participants'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            participant = self.get_object()
            serializer = self.get_serializer(participant)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Participant.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Participant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching participant details: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch participant details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamListViewSet(viewsets.ReadOnlyModelViewSet):
    
    permission_classes = [IsAdminVolunteer]
    serializer_class = TeamListSerializer
    
    def get_queryset(self):
        queryset = Team.objects.all().prefetch_related(
            'members',
            'team_competition_registrations__competition',
            'gift_status__gift',
            'entry_status'
        )
        
        competition_code = self.request.query_params.get('competition')
        payment_verified = self.request.query_params.get('payment_verified')
        
        if competition_code:
            queryset = queryset.filter(
                team_competition_registrations__competition__code=competition_code
            ).distinct()
        
        if payment_verified is not None:
            is_verified = payment_verified.lower() == 'true'
            queryset = queryset.filter(payment_verified=is_verified)
        
        return queryset.order_by('-id')
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'success': True,
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching teams list: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch teams'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SegmentViewSet(viewsets.ReadOnlyModelViewSet):
    
    permission_classes = [IsAdminVolunteer]
    serializer_class = SegmentSerializer
    queryset = Segment.objects.all()
    lookup_field = 'code'
    
    def retrieve(self, request, *args, **kwargs):
        try:
            segment = self.get_object()
            serializer = self.get_serializer(segment)
            
            # Get all participants registered for this segment
            participants = Participant.objects.filter(
                registrations__segment=segment
            ).distinct()
            
            from .serializers import ParticipantListSerializer
            participant_serializer = ParticipantListSerializer(participants, many=True)
            
            return Response({
                'success': True,
                'segment': serializer.data,
                'participant_count': participants.count(),
                'participants': participant_serializer.data
            }, status=status.HTTP_200_OK)
        except Segment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Segment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching segment: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch segment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompetitionViewSet(viewsets.ReadOnlyModelViewSet):
    
    permission_classes = [IsAdminVolunteer]
    serializer_class = CompetitionSerializer
    queryset = Competition.objects.all()
    lookup_field = 'code'
    
    def retrieve(self, request, *args, **kwargs):
        try:
            competition = self.get_object()
            serializer = self.get_serializer(competition)
            
            participants = Participant.objects.filter(
                competition_registrations__competition=competition
            ).distinct()
            
            from .serializers import ParticipantListSerializer
            participant_serializer = ParticipantListSerializer(participants, many=True)
            
            return Response({
                'success': True,
                'competition': serializer.data,
                'participant_count': participants.count(),
                'participants': participant_serializer.data
            }, status=status.HTTP_200_OK)
        except Competition.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Competition not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching competition: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch competition'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamCompetitionViewSet(viewsets.ReadOnlyModelViewSet):
    
    permission_classes = [IsAdminVolunteer]
    serializer_class = TeamCompetitionSerializer
    queryset = TeamCompetition.objects.all()
    lookup_field = 'code'
    
    def retrieve(self, request, *args, **kwargs):
        try:
            competition = self.get_object()
            serializer = self.get_serializer(competition)
            
            teams = Team.objects.filter(
                team_competition_registrations__competition=competition
            ).distinct()
            
            team_serializer = TeamListSerializer(teams, many=True)
            
            return Response({
                'success': True,
                'competition': serializer.data,
                'team_count': teams.count(),
                'teams': team_serializer.data
            }, status=status.HTTP_200_OK)
        except TeamCompetition.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Team competition not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching team competition: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch team competition'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CouponValidationViewSet(viewsets.ViewSet):
    
    permission_classes = [AllowAny]

    def list(self, request, code=None):
        if not code:
            return Response({
                'success': False,
                'error': 'Coupon code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupons.objects.get(coupon_code=code)

            # Check if coupon has remaining uses
            if coupon.coupon_number <= 0:
                return Response({
                    'success': False,
                    'error': 'Coupon code is no longer valid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'coupon': {
                    'code': coupon.coupon_code,
                    'discount': coupon.discount,
                }
            }, status=status.HTTP_200_OK)
        
        except Coupons.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid or inactive coupon code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error validating coupon: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to validate coupon'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentVerificationViewSet(viewsets.ViewSet):
    
    permission_classes = [IsAdminVolunteer]
    
    def create(self, request):
        try:
            serializer = PaymentVerificationSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            participant_id = serializer.validated_data['id']
            
            try:
                participant = Participant.objects.get(id=participant_id)
                
                was_verified = participant.payment_verified
                participant.payment_verified = not participant.payment_verified
                participant.save()
                
                response_data = {
                    'participant': {
                        'id': participant.id,
                        'name': f'{participant.f_name} {participant.l_name}',
                        'payment_verified': participant.payment_verified
                    }
                }
                
                team_member = TeamParticipant.objects.filter(
                    email=participant.email, 
                    is_leader=True
                ).first()
                
                team = None
                if team_member:
                    team = team_member.team
                    team.payment_verified = participant.payment_verified
                    team.save()
                    
                    response_data['team'] = {
                        'id': team.id,
                        'name': team.team_name,
                        'payment_verified': team.payment_verified
                    }
                
                message = f'Payment verified for {participant.f_name} {participant.l_name}'
                if team_member:
                    message += f' and team {team.team_name}'
                
                if participant.payment_verified and not was_verified:
                    self._send_verification_emails(participant, team, response_data, message)
                
                return Response({
                    'success': True,
                    'message': message,
                    'data': response_data
                }, status=status.HTTP_200_OK)
                
            except Participant.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Participant not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error updating payment verification: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update payment verification',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_verification_emails(self, participant, team, response_data, message):
        from .utils import send_payment_verification_email, send_team_payment_verification_emails
        
        email_sent = send_payment_verification_email(participant, team=None)
        
        if email_sent:
            message += '. Participant confirmation email sent.'
            response_data['email_sent'] = True
        else:
            message += '. Warning: Participant email failed to send.'
            response_data['email_sent'] = False
            response_data['email_warning'] = 'Failed to send participant confirmation email'
        
        if team:
            team_email_sent = send_team_payment_verification_emails(team)
            
            if team_email_sent:
                message += ' Team confirmation emails sent to all members.'
                response_data['team_email_sent'] = True
            else:
                message += ' Warning: Team emails failed to send.'
                response_data['team_email_sent'] = False
                if 'email_warning' in response_data:
                    response_data['email_warning'] += '; Team emails also failed'
                else:
                    response_data['email_warning'] = 'Failed to send team confirmation emails'









class RecordEntryViewSet(viewsets.ModelViewSet):
    
    queryset = EntryStatus.objects.all().order_by('-datetime')
    serializer_class = EntryStatusSerializer

    def get_queryset(self):
        id_param = self.kwargs.get("id")
        
        try:
            entity_type, entity_id = parse_id_parameter(id_param)
            
            if entity_type == 'participant':
                return EntryStatus.objects.filter(participant__id=entity_id)
            else:
                return EntryStatus.objects.filter(team__id=entity_id)
        except ValueError:
            return EntryStatus.objects.none()

    def list(self, request, *args, **kwargs):
        id_param = self.kwargs.get("id")
        
        try:
            participant, team = get_entity_by_id(id_param)
        except ValueError as e:
            return Response({
                "success": False, 
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Participant.DoesNotExist:
            return Response({
                "success": False, 
                "error": "No participant with the ID"
            }, status=status.HTTP_404_NOT_FOUND)
        except Team.DoesNotExist:
            return Response({
                "success": False, 
                "error": "No team with the ID"
            }, status=status.HTTP_404_NOT_FOUND)
        
        queryset = self.get_queryset()
        has_entry = queryset.exists()
        entity_info = get_entity_info(participant, team)
        
        return Response({
            "success": True,
            "has_entry": has_entry,
            **entity_info
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        id_param = self.kwargs.get("id")
        data = {}
        participant = None
        team = None

        try:
            entity_type, entity_id = parse_id_parameter(id_param)
            
            if entity_type == 'participant':
                participant = Participant.objects.get(id=entity_id)
                data["participant"] = participant.id
                
                if EntryStatus.objects.filter(participant_id=participant.id).exists():
                    return Response({
                        "success": False, 
                        "error": "Already recorded entry"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                team = Team.objects.get(id=entity_id)
                data["team"] = team.id
                
                if EntryStatus.objects.filter(team__id=team.id).exists():
                    return Response({
                        "success": False, 
                        "error": "Already recorded entry"
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except ValueError as e:
            return Response({
                "success": False, 
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Participant.DoesNotExist:
            return Response({
                "success": False, 
                "error": "No participant with the ID"
            }, status=status.HTTP_404_NOT_FOUND)
        except Team.DoesNotExist:
            return Response({
                "success": False, 
                "error": "No team with the ID"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            volunteer = Volunteer.objects.get(user=self.request.user)
            data["volunteer"] = volunteer.id
        except Volunteer.DoesNotExist:
            return Response({
                "success": False, 
                "error": "Volunteer not found for this user"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            entity_info = get_entity_info(participant, team)
            
            return Response({
                "success": True,
                "message": "Entry recorded successfully",
                **entity_info
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False, 
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GiftsStatusViewSet(viewsets.ViewSet):
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request, id=None):
        try:
            participant, team = get_entity_by_id(id)
        except ValueError as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Participant.DoesNotExist:
            return Response({
                "error": "No participant with the ID"
            }, status=status.HTTP_404_NOT_FOUND)
        except Team.DoesNotExist:
            return Response({
                "error": "No team with the ID"
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            all_gifts = Gift.objects.all()
            gift_status_dict = {gift.gift_name.lower(): 0 for gift in all_gifts}
            
            if participant:
                received_gifts = GiftStatus.objects.filter(participant=participant)
            else:
                received_gifts = GiftStatus.objects.filter(team=team)
            
            for gift_status_obj in received_gifts:
                gift_name = gift_status_obj.gift.gift_name.lower()
                gift_status_dict[gift_name] = 1
            
            entity_info = get_entity_info(participant, team)
            
            return Response({
                "gifts": gift_status_dict,
                **entity_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching gifts status for {id}: {str(e)}")
            return Response({
                "error": "Failed to fetch gifts status"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, id=None):
        try:
            gift_name = request.data.get('gift_name')
            if not gift_name:
                return Response({
                    "error": "gift_name is required in request body"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                gift = Gift.objects.get(gift_name__iexact=gift_name)
            except Gift.DoesNotExist:
                return Response({
                    "error": f"Gift '{gift_name}' not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            try:
                participant, team = get_entity_by_id(id)
            except ValueError as e:
                return Response({
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Participant.DoesNotExist:
                return Response({
                    "error": "No participant with the ID"
                }, status=status.HTTP_404_NOT_FOUND)
            except Team.DoesNotExist:
                return Response({
                    "error": "No team with the ID"
                }, status=status.HTTP_404_NOT_FOUND)
            
            data = {"gift": gift.id}
            
            if participant:
                data["participant"] = participant.id
                
                if GiftStatus.objects.filter(participant=participant, gift=gift).exists():
                    entity_info = get_entity_info(participant, None)
                    return Response({
                        "message": f"{gift.gift_name} already marked as received",
                        **entity_info
                    }, status=status.HTTP_200_OK)
            else:
                data["team"] = team.id
                
                if GiftStatus.objects.filter(team=team, gift=gift).exists():
                    entity_info = get_entity_info(None, team)
                    return Response({
                        "message": f"{gift.gift_name} already marked as received",
                        **entity_info
                    }, status=status.HTTP_200_OK)
            
            try:
                volunteer = Volunteer.objects.get(user=request.user)
                data["volunteer"] = volunteer.id
            except Volunteer.DoesNotExist:
                return Response({
                    "error": "Volunteer not found for this user"
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = GiftStatusSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                entity_info = get_entity_info(participant, team)
                
                return Response({
                    "message": f"{gift.gift_name} marked as received successfully",
                    "gift": gift.gift_name,
                    **entity_info
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "error": "Failed to update gift status", 
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            logger.error(f"Error updating gift status for {id}: {str(e)}")
            return Response({
                "error": "Failed to update gift status"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, page, event, id):
        try:
            # Get participant or team
            try:
                participant, team = get_entity_by_id(id)
            except ValueError as e:
                return Response({
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Participant.DoesNotExist:
                return Response({
                    "error": "No participant with the ID"
                }, status=status.HTTP_404_NOT_FOUND)
            except Team.DoesNotExist:
                return Response({
                    "error": "No team with the ID"
                }, status=status.HTTP_404_NOT_FOUND)

            allowed = False

            # Check registration based on page type
            if page == "segment":
                if participant:
                    allowed = Registration.objects.filter(
                        participant=participant, 
                        segment__code=event
                    ).exists()

            elif page == "solo":
                if participant:
                    allowed = CompetitionRegistration.objects.filter(
                        participant=participant, 
                        competition__code=event
                    ).exists()

            elif page == "team":
                if team:
                    allowed = TeamCompetitionRegistration.objects.filter(
                        team=team, 
                        competition__code=event
                    ).exists()

            else:
                return Response({
                    "error": "Invalid page type. Use 'segment', 'solo', or 'team'"
                }, status=status.HTTP_400_BAD_REQUEST)

            entity_info = get_entity_info(participant, team)
            
            return Response({
                "allowed": allowed,
                "page": page,
                "event": event,
                **entity_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in CheckViewSet: {str(e)}")
            return Response({
                "error": f"Failed to check allowance: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParticipantTeamInfoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Only allow GET requests"""
        if self.action not in ['list']:
            self.http_method_names = ['get'] 
        return super().get_permissions()

    def list(self, request, id=None):
        try:
            try:
                participant, team = get_entity_by_id(id)
            except ValueError as e:
                return Response({
                    "error": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Participant.DoesNotExist:
                return Response({
                    "error": "No participant with the ID"
                }, status=status.HTTP_404_NOT_FOUND)
            except Team.DoesNotExist:
                return Response({
                    "error": "No team with the ID"
                }, status=status.HTTP_404_NOT_FOUND)

            response_data = {}
            
            if participant:
                response_data["participant"] = ParticipantSerializer(participant).data
            
            if team:
                response_data["team"] = TeamSerializer(team).data

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching participant/team info for {id}: {str(e)}")
            return Response({
                "error": "Failed to fetch participant/team info"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)