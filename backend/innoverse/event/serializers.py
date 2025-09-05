from rest_framework import serializers
from .models import *


class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = ['id', 'segment_name']


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'competition_name', 'competition_type']

