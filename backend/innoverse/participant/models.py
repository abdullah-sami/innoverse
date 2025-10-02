from django.db import models
from django.core.exceptions import ValidationError
from event.models import Segment, Competition, Gift, TeamCompetition


class Participant(models.Model):
    f_name = models.CharField(max_length=100, db_index=True)
    l_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    age = models.IntegerField()
    institution = models.CharField(max_length=200)
    institution_id = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    payment_verified = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.f_name} {self.l_name}"




class Team(models.Model):
    team_name = models.CharField(max_length=100, unique=True, db_index=True)
    payment_verified = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.team_name


class TeamParticipant(models.Model):
    f_name = models.CharField(max_length=100, db_index=True)
    l_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    age = models.IntegerField()
    institution = models.CharField(max_length=200)
    institution_id = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', db_index=True)
    is_leader = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.f_name} {self.l_name}"









class Payment(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='payments', null=True, blank=True, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='payments', null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    trx_id = models.CharField(max_length=100, unique=True, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def clean(self):
        if not self.participant and not self.team:
            raise ValidationError("Payment must be linked to either a participant or a team.")
        if self.participant and self.team:
            raise ValidationError("Payment cannot be linked to both a participant and a team.")

    def __str__(self):
        if self.participant:
            return f"Payment {self.trx_id} - Participant: {self.participant}"
        return f"Payment {self.trx_id} - Team: {self.team}"






class Registration(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='registrations', db_index=True)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='segment_registrations', db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.participant} - {self.segment}"




class CompetitionRegistration(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='competition_registrations', db_index=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='competitions', db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.participant} - {self.competition}"


class TeamCompetitionRegistration(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_competition_registrations', db_index=True)
    competition = models.ForeignKey(TeamCompetition, on_delete=models.CASCADE, related_name='team_competitions', db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_index=True)

    
    def __str__(self):
        return f"{self.team} - {self.competition}"