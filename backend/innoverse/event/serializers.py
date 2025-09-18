from rest_framework import serializers
from .models import Segment, Gift, Competition, TeamCompetition
from participant.models import Registration, CompetitionRegistration, TeamCompetitionRegistration
from participant.serializers import ParticipantSerializer, TeamSerializer
from api.models import GiftStatus



class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = "__all__"


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = "__all__"


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = "__all__"


class TeamCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCompetition
        fields = "__all__"






class ParticipantSegmentWiseSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer()

    class Meta:
        model = Registration
        fields = ["participant", "segment", "datetime"]



class ParticipantCompetitionWiseSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer()
    competition = serializers.StringRelatedField()

    class Meta:
        model = CompetitionRegistration
        fields = ["participant", "competition", "datetime"]


class TeamCompetitionWiseSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    competition = serializers.StringRelatedField()

    class Meta:
        model = TeamCompetitionRegistration
        fields = ["team", "competition", "datetime"]







class ParticipantGiftStatusSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer()
    gift = serializers.StringRelatedField()
    volunteer = serializers.StringRelatedField()

    class Meta:
        model = GiftStatus
        fields = ["participant", "gift", "volunteer", "datetime"]






class TeamGiftStatusSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    gift = serializers.StringRelatedField()
    volunteer = serializers.StringRelatedField()

    class Meta:
        model = GiftStatus
        fields = ["team", "gift", "volunteer", "datetime"]