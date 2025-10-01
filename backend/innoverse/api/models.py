from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from participant.models import Participant, Team
from event.models import Gift


class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, db_index=True)
    def __str__(self):
        return self.role_name


class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile', db_index=True)
    v_name = models.CharField(max_length=100, db_index=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='volunteers', db_index=True)

    def __str__(self):
        return f"{self.v_name} ({self.role.role_name})"







class GiftStatus(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='gift_status', null=True, blank=True, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='gift_status', null=True, blank=True, db_index=True)
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE, db_index=True)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def clean(self):
        if not self.participant and not self.team:
            raise ValidationError("Gifts must be linked to either a participant or a team.")
        if self.participant and self.team:
            raise ValidationError("Gifts cannot be linked to both a participant and a team.")

    def __str__(self):
        if self.participant:
            return f"{self.gift} - Participant: {self.participant}"
        return f"{self.gift} - Team: {self.team}"



class EntryStatus(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='entry_status', null=True, blank=True, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='entry_status', null=True, blank=True, db_index=True)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def clean(self):
        if not self.participant and not self.team:
            raise ValidationError("Entry must be linked to either a participant or a team.")
        if self.participant and self.team:
            raise ValidationError("Entry cannot be linked to both a participant and a team.")

    def __str__(self):
        if self.participant:
            return f"Entry {self.datetime} - Participant: {self.participant}"
        return f"Entry {self.datetime} - Team: {self.team}"



# class User(AbstractUser):
#     email = models.EmailField(unique=True)
