from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.db import transaction

from .models import Participant, Team,  EntryStatus, Gift, GiftStatus
from .serializers import (
    ParticipantDetailSerializer,
    ParticipantListSerializer,
    TeamListSerializer,
    PaymentVerificationSerializer,
    CompleteRegistrationSerializer,
    EntryStatusSerializer,
    GiftStatusSerializer

)
from event.models import Segment, Competition, TeamCompetition
from event.serializers import SegmentSerializer, CompetitionSerializer, TeamCompetitionSerializer
from api.models import Volunteer
from participant.models import Registration, CompetitionRegistration, TeamCompetitionRegistration, Payment, TeamParticipant
from participant.serializers import ParticipantSerializer, TeamSerializer
import logging

logger = logging.getLogger(__name__)


class IsAdminVolunteer(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        try:
            volunteer = Volunteer.objects.get(user=request.user)
            return volunteer.role.role_name.lower() == 'admin'
        except Volunteer.DoesNotExist:
            return False




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
                # Step 1: Create main participant (team leader)
                participant = self._create_participant(validated_data['participant'])
                
                # Step 2: Record participant payment
                participant_payment = self._create_payment(
                    validated_data['payment'],
                    participant=participant
                )
                
                # Step 3: Register for segments
                segment_codes = validated_data.get('segment', [])
                self._register_segments(participant, segment_codes)
                
                # Step 4: Register for solo competitions
                competition_codes = validated_data.get('competition', [])
                self._register_competitions(participant, competition_codes)
                
                # Step 5: Handle team competition if provided
                team = None
                team_payment = None
                if 'team_competition' in validated_data:
                    team, team_payment = self._handle_team_competition(
                        validated_data['team_competition'],
                        validated_data['payment'],
                        participant
                    )
                
                # Build response
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
                            "trx_id": participant_payment.trx_id,
                            "amount": str(participant_payment.amount)
                        },
                        "segments": segment_codes,
                        "competitions": competition_codes
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
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Registration failed",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_participant(self, participant_data):
        full_name = participant_data['full_name'].strip()
        name_parts = full_name.split(maxsplit=1)
        f_name = name_parts[0]
        l_name = name_parts[1] if len(name_parts) > 1 else ""
        
        participant = Participant.objects.create(
            f_name=f_name,
            l_name=l_name,
            gender=participant_data['gender'],
            email=participant_data['email'],
            phone=participant_data['phone'],
            age=participant_data['age'],
            institution=participant_data['institution'],
            institution_id=participant_data['institution_id'],
            address=participant_data.get('address', ''),
            t_shirt_size=participant_data.get('t_shirt_size', ''),
            club_reference=participant_data.get('club_reference', ''),
            campus_ambassador=participant_data.get('campus_ambassador', ''),
            payment_verified=False
        )
        return participant
    
    def _create_payment(self, payment_data, participant=None, team=None):
        payment = Payment.objects.create(
            participant=participant,
            team=team,
            phone=payment_data['phone'],
            amount=payment_data['amount'],
            trx_id=payment_data['trx_id']
        )
        return payment
    
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
    
    def _handle_team_competition(self, team_competition_data, payment_data, leader_participant):
        team_info = team_competition_data['team']
        team_name = team_info['team_name']
        
        team = Team.objects.create(
            team_name=team_name,
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
            institution_id=leader_participant.institution_id,
            address=leader_participant.address,
            t_shirt_size=leader_participant.t_shirt_size,
            club_reference=leader_participant.club_reference,
            campus_ambassador=leader_participant.campus_ambassador,
            team=team,
            is_leader=True
        )
        
        for member_data in team_info['participant']:
            full_name = member_data['full_name'].strip()
            name_parts = full_name.split(maxsplit=1)
            f_name = name_parts[0]
            l_name = name_parts[1] if len(name_parts) > 1 else ""
            
            TeamParticipant.objects.create(
                f_name=f_name,
                l_name=l_name,
                gender=member_data['gender'],
                email=member_data.get('email', ''),
                phone=member_data['phone'],
                age=member_data['age'],
                institution=member_data['institution'],
                institution_id=member_data['institution_id'],
                address=member_data.get('address', ''),
                t_shirt_size=member_data.get('t_shirt_size', ''),
                club_reference=member_data.get('club_reference', ''),
                campus_ambassador=member_data.get('campus_ambassador', ''),
                team=team,
                is_leader=False
            )
        
        team_payment = self._create_payment(
            payment_data,
            team=team
        )
        
        for competition_code in team_competition_data['competition']:
            competition = TeamCompetition.objects.get(code=competition_code)
            TeamCompetitionRegistration.objects.create(
                team=team,
                competition=competition
            )
        
        return team, team_payment









# admin dashboard viewsets  *************************************************











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
                'error': 'Failed to update payment verification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

















# app viewsets ******************************************************************














class RecordEntryViewSet(viewsets.ModelViewSet):
    queryset = EntryStatus.objects.all().order_by('-datetime')
    serializer_class = EntryStatusSerializer

    def get_queryset(self):
        id_param = self.kwargs.get("id")

        if id_param.startswith("p_"):
            participant_id = id_param.split("_")[1]
            return EntryStatus.objects.filter(participant__id=participant_id)

        elif id_param.startswith("t_"):
            team_id = id_param.split("_")[1]
            return EntryStatus.objects.filter(team__id=team_id)

        return EntryStatus.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        id_param = self.kwargs.get("id")
        data = {}

        # Participant entry
        if id_param.startswith("p_"):
            participant_id = id_param.split("_")[1]
            try:
                participant = Participant.objects.get(id=participant_id)
            except Participant.DoesNotExist:
                return Response(
                    {"success": False, "error": "No participant with the ID"},
                    status=status.HTTP_404_NOT_FOUND
                )
            data["participant"] = participant.id

            if EntryStatus.objects.filter(participant_id=participant.id).exists():
                return Response(
                    {"success": False, "error": "Already recorded entry"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Team entry
        elif id_param.startswith("t_"):
            team_id = id_param.split("_")[1]
            try:
                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                return Response(
                    {"success": False, "error": "No team with the ID"},
                    status=status.HTTP_404_NOT_FOUND
                )
            data["team"] = team.id

            if EntryStatus.objects.filter(team__id=team.id).exists():
                return Response(
                    {"success": False, "error": "Already recorded entry"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Attach volunteer
        try:
            volunteer = Volunteer.objects.get(user=self.request.user)
        except Volunteer.DoesNotExist:
            return Response(
                {"success": False, "error": "Volunteer not found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )

        data["volunteer"] = volunteer.id

        team_participant = TeamParticipant.objects.filter(team=team).count() if 'team' in data else 0

        res = {"p_name": f"{participant.f_name} {participant.l_name}" if data.get("participant") else None, "t_name": f"{team.team_name} ({team_participant} members)" if data.get("team") else None}

        # Serialize
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": res}, status=status.HTTP_201_CREATED)

        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)














class GiftsStatusViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request, id=None):
        try:
            id_param = id
            participant = None
            team = None
            
            
            if id_param.startswith("p_"):
                participant_id = id_param.split("_")[1]
                try:
                    participant = Participant.objects.get(id=participant_id)
                except Participant.DoesNotExist:
                    return Response(
                        {"error": "No participant with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif id_param.startswith("t_"):
                team_id = id_param.split("_")[1]
                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    return Response(
                        {"error": "No team with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {"error": "Invalid ID format. Use 'p_' for participant or 't_' for team"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            all_gifts = Gift.objects.all()
            gift_status_dict = {}
            
            
            for gift in all_gifts:
                gift_status_dict[gift.gift_name.lower()] = 0
            
            
            if participant:
                received_gifts = GiftStatus.objects.filter(participant=participant)
            else:
                received_gifts = GiftStatus.objects.filter(team=team)
            
            
            for gift_status_obj in received_gifts:
                gift_name = gift_status_obj.gift.gift_name.lower()
                gift_status_dict[gift_name] = 1
            
           
            return Response(gift_status_dict, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching gifts status for {id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch gifts status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, id=None):
        try:
            id_param = id
            
            
            gift_name = request.data.get('gift_name')
            if not gift_name:
                return Response(
                    {"error": "gift_name is required in request body"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            try:
                gift = Gift.objects.get(gift_name__iexact=gift_name)
            except Gift.DoesNotExist:
                return Response(
                    {"error": f"Gift '{gift_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {}
            participant = None
            team = None
            
           
            if id_param.startswith("p_"):
                participant_id = id_param.split("_")[1]
                try:
                    participant = Participant.objects.get(id=participant_id)
                except Participant.DoesNotExist:
                    return Response(
                        {"error": "No participant with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                data["participant"] = participant.id
                
                
                if GiftStatus.objects.filter(participant=participant, gift=gift).exists():
                    return Response(
                        {"message": f"{gift.gift_name} already marked as received"},
                        status=status.HTTP_200_OK
                    )
                    
            elif id_param.startswith("t_"):
                team_id = id_param.split("_")[1]
                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    return Response(
                        {"error": "No team with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                data["team"] = team.id
                
                
                if GiftStatus.objects.filter(team=team, gift=gift).exists():
                    return Response(
                        {"message": f"{gift.gift_name} already marked as received"},
                        status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {"error": "Invalid ID format. Use 'p_' for participant or 't_' for team"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            try:
                volunteer = Volunteer.objects.get(user=request.user)
                data["volunteer"] = volunteer.id
            except Volunteer.DoesNotExist:
                return Response(
                    {"error": "Volunteer not found for this user"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            
            data["gift"] = gift.id

            
            
            
            serializer = GiftStatusSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": f"{gift.gift_name} marked as received successfully"},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": "Failed to update gift status", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                    
        except Exception as e:
            logger.error(f"Error updating gift status for {id}: {str(e)}")
            return Response(
                {"error": "Failed to update gift status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        







class ParticipantTeamInfoViewSet(viewsets.ViewSet):
    
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action not in ['list']:
            self.http_method_names = ['get'] 
        return super().get_permissions()

    def list(self, request, id=None):
        try:
            id_param = id
            participant = None
            team = None

            if id_param.startswith("p_"):
                participant_id = id_param.split("_")[1]
                try:
                    participant = Participant.objects.get(id=participant_id)
                except Participant.DoesNotExist:
                    return Response(
                        {"error": "No participant with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                try:
                    team = Team.objects.filter(members__email=participant.email).first()
                except Exception:
                    team = None

            elif id_param.startswith("t_"):
                team_id = id_param.split("_")[1]
                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    return Response(
                        {"error": "No team with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {"error": "Invalid ID format. Use 'p_' for participant or 't_' for team"},
                    status=status.HTTP_400_BAD_REQUEST
                )

           
            response_data = {}
            if participant:
                response_data["participant"] = ParticipantSerializer(participant).data
            if team:
                response_data["team"] = TeamSerializer(team).data

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching participant/team info for {id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch participant/team info"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )














class CheckViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, page, event, id):
        try:
            participant = None
            team = None
            allowed = False

            if id.startswith("p_"):
                participant_id = id.split("_")[1]
                try:
                    participant = Participant.objects.get(id=participant_id)
                except Participant.DoesNotExist:
                    return Response(
                        {"error": "No participant with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                
                team = Team.objects.filter(members__email=participant.email).first()

            elif id.startswith("t_"):
                team_id = id.split("_")[1]
                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    return Response(
                        {"error": "No team with the ID"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            else:
                return Response(
                    {"error": "Invalid ID format. Use 'p_' for participant or 't_' for team"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if page == "segment":
                if participant:
                    allowed = Registration.objects.filter(
                        participant=participant, segment__code=event
                    ).exists()

            elif page == "solo":
                if participant:
                    allowed = CompetitionRegistration.objects.filter(
                        participant=participant, competition__code=event
                    ).exists()

            elif page == "team":
                if team:
                    allowed = TeamCompetitionRegistration.objects.filter(
                        team=team, competition__code=event
                    ).exists()

            else:
                return Response(
                    {"error": "Invalid page type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({"allowed": allowed}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to fetch participant/team info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )













