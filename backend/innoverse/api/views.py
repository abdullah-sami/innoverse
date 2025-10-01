from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction 
from .models import *
from .serializers import *
from participant.models import Participant, Team, Registration, CompetitionRegistration, TeamCompetitionRegistration, TeamParticipant
from participant.serializers import ParticipantSerializer, TeamSerializer
from rest_framework import viewsets

import logging

logger = logging.getLogger(__name__)







class RecordEntryViewSet(ModelViewSet):
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
