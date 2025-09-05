from django.db import models
from event.models import Segment, Competition, Gift


class Participant(models.Model):
    f_name = models.CharField(max_length=100)
    l_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    age = models.IntegerField()
    institution = models.CharField(max_length=200)
    institution_id = models.CharField(max_length=100)
    address = models.TextField()
    payment_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.f_name} {self.l_name}"









class Payment(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='payments')
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    trx_id = models.CharField(max_length=100)
    datetime = models.DateTimeField(auto_now_add=True)


class Registration(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='registrations')
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='segment_registrations')
    datetime = models.DateTimeField(auto_now_add=True)


class CompetitionRegistration(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='competition_registrations')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='competitions')
    team_name = models.CharField(max_length=100, null=True, blank=True)
    team_leader = models.BooleanField(default=False)