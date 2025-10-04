from rest_framework import serializers
from .models import Role, Volunteer, GiftStatus, EntryStatus

from participant.models import (
    Participant, Team, TeamParticipant, Payment,
    Registration, CompetitionRegistration, TeamCompetitionRegistration
)
from event.models import Segment, Competition, TeamCompetition


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








class ParticipantRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'])
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    age = serializers.IntegerField()
    institution = serializers.CharField(max_length=200)
    institution_id = serializers.CharField(max_length=100)
    address = serializers.CharField(required=False, allow_blank=True)
    t_shirt_size = serializers.ChoiceField(
        choices=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        required=False,
        allow_blank=True
    )
    club_reference = serializers.CharField(max_length=200, required=False, allow_blank=True)
    campus_ambassador = serializers.CharField(max_length=200, required=False, allow_blank=True)


class PaymentRegistrationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    phone = serializers.CharField(max_length=20)
    trx_id = serializers.CharField(max_length=100)


class TeamMemberRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'])
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20)
    age = serializers.IntegerField()
    institution = serializers.CharField(max_length=200)
    institution_id = serializers.CharField(max_length=100)
    address = serializers.CharField(required=False, allow_blank=True)
    t_shirt_size = serializers.ChoiceField(
        choices=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        required=False,
        allow_blank=True
    )
    club_reference = serializers.CharField(max_length=200, required=False, allow_blank=True)
    campus_ambassador = serializers.CharField(max_length=200, required=False, allow_blank=True)


class TeamInfoSerializer(serializers.Serializer):
    team_name = serializers.CharField(max_length=100)
    participant = TeamMemberRegistrationSerializer(many=True)


class TeamCompetitionInfoSerializer(serializers.Serializer):
    team = TeamInfoSerializer()
    competition = serializers.ListField(child=serializers.CharField(max_length=20))


class CompleteRegistrationSerializer(serializers.Serializer):
    participant = ParticipantRegistrationSerializer()
    payment = PaymentRegistrationSerializer()
    segment = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        allow_empty=True,
        default=list
    )
    competition = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        allow_empty=True,
        default=list
    )
    team_competition = TeamCompetitionInfoSerializer(required=False, allow_null=True)

    def validate_payment(self, value):
        # Check if transaction ID already exists
        trx_id = value.get('trx_id')
        if Payment.objects.filter(trx_id=trx_id).exists():
            raise serializers.ValidationError(f"Transaction ID {trx_id} already exists")
        return value

    def validate_segment(self, value):
        if value:
            invalid_codes = []
            for code in value:
                if not Segment.objects.filter(code=code).exists():
                    invalid_codes.append(code)
            if invalid_codes:
                raise serializers.ValidationError(f"Invalid segment codes: {', '.join(invalid_codes)}")
        return value

    def validate_competition(self, value):
        if value:
            invalid_codes = []
            for code in value:
                if not Competition.objects.filter(code=code).exists():
                    invalid_codes.append(code)
            if invalid_codes:
                raise serializers.ValidationError(f"Invalid competition codes: {', '.join(invalid_codes)}")
        return value

    def validate_team_competition(self, value):
        if value and 'competition' in value:
            invalid_codes = []
            for code in value['competition']:
                if not TeamCompetition.objects.filter(code=code).exists():
                    invalid_codes.append(code)
            if invalid_codes:
                raise serializers.ValidationError(f"Invalid team competition codes: {', '.join(invalid_codes)}")
        return value

    def validate(self, data):
        participant = data.get('participant', {})
        team_competition = data.get('team_competition')

        # Check if participant email already exists
        email = participant.get('email')
        if Participant.objects.filter(email=email).exists():
            raise serializers.ValidationError({"participant": f"Email {email} is already registered"})

        # Check if team name already exists
        if team_competition:
            team_name = team_competition['team']['team_name']
            if Team.objects.filter(team_name=team_name).exists():
                raise serializers.ValidationError({"team_competition": f"Team name '{team_name}' already exists"})

            # Check for duplicate emails in team members
            team_members = team_competition['team']['participant']
            emails = [m.get('email') for m in team_members if m.get('email')]
            
            # Check if leader email matches any team member email
            if email in emails:
                raise serializers.ValidationError({"team_competition": "Team leader email cannot be the same as team member email"})
            
            # Check for duplicate emails within team
            if len(emails) != len(set(emails)):
                raise serializers.ValidationError({"team_competition": "Duplicate emails found in team members"})

        return data
    
















class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'phone', 'amount', 'trx_id', 'datetime']


class RegistrationInfoSerializer(serializers.ModelSerializer):
    segment_name = serializers.CharField(source='segment.segment_name', read_only=True)
    segment_code = serializers.CharField(source='segment.code', read_only=True)
    
    class Meta:
        model = Registration
        fields = ['segment_name', 'segment_code', 'datetime']


class CompetitionRegistrationInfoSerializer(serializers.ModelSerializer):
    competition_name = serializers.CharField(source='competition.competition', read_only=True)
    competition_code = serializers.CharField(source='competition.code', read_only=True)
    
    class Meta:
        model = CompetitionRegistration
        fields = ['competition_name', 'competition_code', 'datetime']


class TeamCompetitionRegistrationInfoSerializer(serializers.ModelSerializer):
    competition_name = serializers.CharField(source='competition.competition', read_only=True)
    competition_code = serializers.CharField(source='competition.code', read_only=True)
    
    class Meta:
        model = TeamCompetitionRegistration
        fields = ['competition_name', 'competition_code', 'datetime']


class ParticipantListSerializer(serializers.ModelSerializer):
    """Serializer for participant list view - minimal info"""
    full_name = serializers.SerializerMethodField()
    segments = serializers.SerializerMethodField()
    competitions = serializers.SerializerMethodField()
    has_entry = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = [
            'id', 'full_name', 'email', 'phone', 'institution',
            'payment_verified', 'segments', 'competitions', 'has_entry'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.f_name} {obj.l_name}"
    
    def get_segments(self, obj):
        return [reg.segment.segment_name for reg in obj.registrations.all()]
    
    def get_competitions(self, obj):
        return [comp.competition.competition for comp in obj.competition_registrations.all()]
    
    def get_has_entry(self, obj):
        return obj.entry_status.exists()


class ParticipantDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    segment_registrations = RegistrationInfoSerializer(source='registrations', many=True, read_only=True)
    competition_registrations = CompetitionRegistrationInfoSerializer(many=True, read_only=True)
    gifts_received = serializers.SerializerMethodField()
    payments = PaymentSerializer(many=True, read_only=True)
    has_entry = serializers.SerializerMethodField()
    entry_datetime = serializers.SerializerMethodField()
    team_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'full_name', 'email', 'phone',
            'age', 'institution', 'institution_id', 'address',
            'payment_verified', 'segment_registrations', 
            'competition_registrations', 'gifts_received', 'payments',
            'has_entry', 'entry_datetime', 'team_info'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.f_name} {obj.l_name}"
    
    def get_gifts_received(self, obj):
        return [{
            'gift_name': gift.gift.gift_name,
            'received_at': gift.datetime,
            'volunteer': gift.volunteer.v_name if gift.volunteer else None
        } for gift in obj.gift_status.all()]
    
    def get_has_entry(self, obj):
        return obj.entry_status.exists()
    
    def get_entry_datetime(self, obj):
        entry = obj.entry_status.first()
        return entry.datetime if entry else None
    
    def get_team_info(self, obj):
        try:
            team = Team.objects.filter(members__email=obj.email).first()
            if team:
                return {
                    'id': team.id,
                    'team_name': team.team_name,
                    'payment_verified': team.payment_verified
                }
        except:
            pass
        return None


class TeamParticipantSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamParticipant
        fields = [
            'id', 'f_name', 'l_name', 'full_name', 'email', 'phone',
            'age', 'institution', 'institution_id', 'is_leader'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.f_name} {obj.l_name}"


class TeamListSerializer(serializers.ModelSerializer):
    """Serializer for team list and detail view"""
    members = TeamParticipantSerializer(many=True, read_only=True)
    competition_registrations = TeamCompetitionRegistrationInfoSerializer(
        source='team_competition_registrations', many=True, read_only=True
    )
    gifts_received = serializers.SerializerMethodField()
    payments = PaymentSerializer(many=True, read_only=True)
    has_entry = serializers.SerializerMethodField()
    entry_datetime = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'team_name', 'payment_verified', 'member_count',
            'members', 'competition_registrations', 'gifts_received',
            'payments', 'has_entry', 'entry_datetime'
        ]
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_gifts_received(self, obj):
        return [{
            'gift_name': gift.gift.gift_name,
            'received_at': gift.datetime,
            'volunteer': gift.volunteer.v_name if gift.volunteer else None
        } for gift in obj.gift_status.all()]
    
    def get_has_entry(self, obj):
        return obj.entry_status.exists()
    
    def get_entry_datetime(self, obj):
        entry = obj.entry_status.first()
        return entry.datetime if entry else None


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification request"""
    id = serializers.IntegerField()



class ParticipantSerializer(serializers.ModelSerializer):
    segment_list = serializers.SerializerMethodField()
    comp_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'email', 'phone', 
            'age', 'institution',  'institution_id', 'address', 'payment_verified',
            'segment_list', 'comp_list', 'gift_list', 'entry_status'
        ]

    def get_segment_list(self, obj):
        return [seg.segment.segment_name for seg in obj.registrations.all()]
    
    def get_comp_list(self, obj):
        return [comp.competition.competition for comp in obj.competition_registrations.all()]

    def get_gift_list(self, obj):
        return [gift.gift.gift_name for gift in obj.gift_status.all()]

    def get_entry_status(self, obj):
        return obj.entry_status.exists()


class TeamSerializer(serializers.ModelSerializer):
    comp_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()
    members = TeamParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'team_name', 'payment_verified', 'comp_list', 'gift_list', 'entry_status', 'members']

    def get_comp_list(self, obj):
        return [comp.competition.competition for comp in obj.team_competition_registrations.all()]
    
    def get_gift_list(self, obj):
        return [gift.gift.gift_name for gift in obj.gift_status.all()]
    
    def get_entry_status(self, obj):
        return obj.entry_status.exists()


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = "__all__"


class CompetitionRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionRegistration
        fields = "__all__"


class TeamCompetitionRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCompetitionRegistration
        fields = "__all__"