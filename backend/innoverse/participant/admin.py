from django.contrib import admin
from .models import *


admin.site.register(Participant)
admin.site.register(Team)
admin.site.register(TeamParticipant)
admin.site.register(Payment)
admin.site.register(Registration)
admin.site.register(CompetitionRegistration)
admin.site.register(TeamCompetitionRegistration)