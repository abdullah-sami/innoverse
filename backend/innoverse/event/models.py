from django.db import models


class Segment(models.Model):
    segment_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.segment_name




class Gift(models.Model):
    gift_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.gift_name




class Competition(models.Model):
    COMPETITION_TYPE = [
        ('solo', 'Solo'),
        ('team', 'Team'),
    ]
    competition_name = models.CharField(max_length=100, unique=True)
    competition_type = models.CharField(max_length=10, choices=COMPETITION_TYPE)

    def __str__(self):
        return f"{self.competition_name} ({self.competition_type})"


