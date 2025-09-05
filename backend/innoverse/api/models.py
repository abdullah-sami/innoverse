
from django.db import models
from django.contrib.auth.models import AbstractUser, User
import uuid
from participant.models import *
from event.models import *



# class User(AbstractUser):
#     email = models.EmailField(unique=True)


class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.role_name


class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    v_name = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='volunteers')

    def __str__(self):
        return f"{self.v_name} ({self.role.role_name})"









class GiftStatus(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='gift_status')
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)


class EntryStatus(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='entry_status')
    datetime = models.DateTimeField(auto_now_add=True)
