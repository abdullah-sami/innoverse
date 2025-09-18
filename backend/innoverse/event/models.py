from django.db import models


class Segment(models.Model):
    segment_name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.segment_name




class Gift(models.Model):
    gift_name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.gift_name




class Competition(models.Model):
    competition = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.competition



class TeamCompetition(models.Model):
    competition = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.competition