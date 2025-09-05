from rest_framework import serializers
from .models import *


class VolunteerSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = Volunteer
        fields = ['id', 'username', 'v_name', 'email', 'role_name']








class EntryRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryStatus
        fields = ['id', 'unique_id', 'datetime']


class GiftStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftStatus
        fields = ['id', 'unique_id', 'gift', 'datetime']