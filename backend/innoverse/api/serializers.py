from rest_framework import serializers
from .models import Role, Volunteer, GiftStatus, EntryStatus


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class VolunteerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volunteer
        fields = "__all__"


class GiftStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftStatus
        fields = "__all__"


class EntryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryStatus
        fields = "__all__"
