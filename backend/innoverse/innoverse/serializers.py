from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.SerializerMethodField()

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.get_role(self.user),
        }
        return data
    
    def get_role(self, obj):
        if hasattr(obj, 'volunteer_profile') and obj.volunteer_profile.role:
            return obj.volunteer_profile.role.role_name
        return None