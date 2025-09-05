from rest_framework import serializers
from .models import (Registration, Participant, Payment, CompetitionRegistration)



class ParticipantSerializer(serializers.ModelSerializer):
    event_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'email', 'phone', 'unique_id',
            'age', 'institution',  'institution_id', 'address', 'payment_verified',
            'event_list', 'gift_list', 'entry_status'
        ]

    def get_event_list(self, obj):
        return [seg.segment.segment_name for seg in obj.registration_set.all()]

    def get_gift_list(self, obj):
        return [gift.gift.gift_name for gift in obj.giftstatus_set.all()]

    def get_entry_status(self, obj):
        return obj.entrystatus_set.exists()







class ParticipantRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'email', 'phone', 'unique_id',
            'age', 'institution', 'address', 'payment_verified'
        ]





class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'participant', 'phone', 'amount', 'trx_id', 'datetime']





class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['id', 'participant', 'segment', 'datetime']





class CompetitionRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionRegistration
        fields = ['id', 'participant', 'competition', 'team_name', 'team_leader']