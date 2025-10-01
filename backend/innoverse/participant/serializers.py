from rest_framework import serializers
from .models import (
    Participant, Team, TeamParticipant,
    Payment, Registration, CompetitionRegistration,
    TeamCompetitionRegistration
)


class ParticipantSerializer(serializers.ModelSerializer):
    segment_list = serializers.SerializerMethodField()
    comp_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'email', 'phone', 
            'age', 'institution',  'institution_id', 'address', 'payment_verified',
            'segment_list', 'comp_list', 'gift_list', 'entry_status'
        ]

    def get_segment_list(self, obj):
        return [seg.segment.segment_name for seg in obj.registrations.all()]
    
    def get_comp_list(self, obj):
        return [comp.competition.competition for comp in obj.competition_registrations.all()]

    def get_gift_list(self, obj):
        return [gift.gift.gift_name for gift in obj.gift_status.all()]

    def get_entry_status(self, obj):
        return obj.entry_status.exists()





class TeamParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamParticipant
        fields = ['id', 'f_name', 'l_name', 'email', 'phone', 'age', 'institution', 'institution_id', 'is_leader']




class TeamSerializer(serializers.ModelSerializer):
    comp_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()
    members = TeamParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'team_name', 'payment_verified', 'comp_list', 'gift_list', 'entry_status', 'members']  # Add 'members' here

    def get_comp_list(self, obj):
        return [comp.competition.competition for comp in obj.team_competition_registrations.all()]
    
    def get_gift_list(self, obj):
        return [gift.gift.gift_name for gift in obj.gift_status.all()]
    
    def get_entry_status(self, obj):
        return obj.entry_status.exists()






class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = "__all__"


class CompetitionRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionRegistration
        fields = "__all__"


class TeamCompetitionRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCompetitionRegistration
        fields = "__all__"
