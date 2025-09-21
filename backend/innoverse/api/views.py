from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *

class RecordEntryViewSet(ModelViewSet):
    queryset = EntryStatus.objects.all().order_by('-datetime')
    serializer_class = EntryStatusSerializer
    

    def get_queryset(self):
        """
        Filter entries based on the id passed in URL.
        id format: p_0001 or t_0001
        """
        id_param = self.kwargs.get("id")

        if id_param.startswith("p_"):
            participant_id = id_param.split("_")[1]
            return EntryStatus.objects.filter(participant__id=participant_id)

        elif id_param.startswith("t_"):
            team_id = id_param.split("_")[1]
            return EntryStatus.objects.filter(team__id=team_id)

        return EntryStatus.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            if not queryset.exists():
                return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            id_param = self.kwargs.get("id")
            data = {}

            if id_param.startswith("p_"):
                participant_id = id_param.split("_")[1]
                participant = get_object_or_404(Participant, id=participant_id)

                data["participant"] = participant.id

            elif id_param.startswith("t_"):
                team_id = id_param.split("_")[1]
                team = get_object_or_404(Team, id=team_id)
                data["team"] = team.id

            volunteer = get_object_or_404(Volunteer, user=self.request.user)
            data["volunteer"] = volunteer.id


            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True}, status=status.HTTP_201_CREATED)

            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            entry = queryset.first()
            if not entry:
                return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)

            entry.delete()
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)
