from event.serializers import CouponSerializer
from rest_framework import serializers
from .models import Role, Volunteer, GiftStatus, EntryStatus

from participant.models import (
    Participant, Team, TeamParticipant, Payment,
    Registration, CompetitionRegistration, TeamCompetitionRegistration
)
from event.models import Coupons, Segment, Competition, TeamCompetition

from django.core.cache import cache
from django.db.models import Q
from participant.models import TanvinAward


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
    
    institution = serializers.CharField(max_length=200)
    address = serializers.CharField(required=False, allow_blank=True)
    guardian_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    grade = serializers.CharField(max_length=20, required=False, allow_blank=True)
    t_shirt_size = serializers.ChoiceField(
        choices=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        required=False,
        allow_blank=True
    )


class PaymentRegistrationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    phone = serializers.CharField(max_length=20)
    method = serializers.CharField(max_length=50)
    trx_id = serializers.CharField(max_length=100)


class TeamMemberRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'])
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20)
    
    institution = serializers.CharField(max_length=200)
    address = serializers.CharField(required=False, allow_blank=True)
    t_shirt_size = serializers.ChoiceField(
        choices=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        required=False,
        allow_blank=True
    )


class TeamInfoSerializer(serializers.Serializer):
    team_name = serializers.CharField(max_length=100)
    participant = TeamMemberRegistrationSerializer(many=True)


class TeamCompetitionInfoSerializer(serializers.Serializer):
    team = TeamInfoSerializer()
    competition = serializers.ListField(child=serializers.CharField(max_length=20))



class TanvinAwardSerializer(serializers.Serializer):
    """Serializer for Tanvin Award project details"""
    project_name = serializers.CharField(max_length=200)
    project_type = serializers.ChoiceField(choices=[
        ("robotics", "Robotics"),
        ("ai", "Artificial Intelligence"),
        ("cs", "Computer Science & Programming"),
        ("data_science", "Data Science & Analytics"),
        ("environment", "Environment & Sustainability"),
        ("health", "Health & Life Sciences"),
        ("engineering", "Engineering & Design"),
        ("education", "Education & Social Development"),
        ("media", "Media & Communication"),
        ("other", "Other")
    ])
    project_description = serializers.CharField()
    pitch_deck = serializers.URLField(required=False, allow_blank=True)
    video_link = serializers.URLField(required=False, allow_blank=True)


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
    tanvin_award = TanvinAwardSerializer(required=False, allow_null=True)  # ADD THIS LINE
    coupon = serializers.DictField(required=False, allow_null=True)

    def validate_payment(self, value):
        """Check if transaction ID already exists - OPTIMIZED"""
        trx_id = value.get('trx_id')
        if Payment.objects.filter(trx_id=trx_id).only('id').exists():
            raise serializers.ValidationError(f"Transaction ID {trx_id} already exists")
        return value

    def validate_segment(self, value):
        """Validate all segment codes in ONE query - OPTIMIZED"""
        if not value:
            return value
        
        valid_codes = set(
            Segment.objects.filter(code__in=value).values_list('code', flat=True)
        )
        
        invalid_codes = [code for code in value if code not in valid_codes]
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid segment codes: {', '.join(invalid_codes)}"
            )
        
        return value

    def validate_competition(self, value):
        """Validate all competition codes in ONE query - OPTIMIZED"""
        if not value:
            return value
        
        valid_codes = set(
            Competition.objects.filter(code__in=value).values_list('code', flat=True)
        )
        
        invalid_codes = [code for code in value if code not in valid_codes]
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid competition codes: {', '.join(invalid_codes)}"
            )
        
        return value

    def validate_team_competition(self, value):
        """Validate all team competition codes in ONE query - OPTIMIZED"""
        if not value or 'competition' not in value:
            return value
        
        competition_codes = value['competition']
        
        valid_codes = set(
            TeamCompetition.objects.filter(
                code__in=competition_codes
            ).values_list('code', flat=True)
        )
        
        invalid_codes = [code for code in competition_codes if code not in valid_codes]
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid team competition codes: {', '.join(invalid_codes)}"
            )
        
        return value

    def validate_coupon(self, value):
        """Validate coupon - OPTIMIZED with select_for_update"""
        if not value:
            return None
        
        coupon_code = value.get('coupon_code')
        if not coupon_code:
            raise serializers.ValidationError("coupon_code is required")
        
        try:
            coupon = Coupons.objects.only(
                'id', 'coupon_code', 'coupon_number', 'discount'
            ).get(coupon_code=coupon_code)
            
            if coupon.coupon_number <= 0:
                raise serializers.ValidationError(
                    f"Coupon '{coupon_code}' has no remaining uses"
                )
            
            return coupon
            
        except Coupons.DoesNotExist:
            raise serializers.ValidationError(f"Invalid coupon code: {coupon_code}")

    def validate(self, data):
        """
        Cross-field validation - OPTIMIZED
        Now includes Tanvin Award validation
        """
        participant = data.get('participant', {})
        team_competition = data.get('team_competition')
        tanvin_award = data.get('tanvin_award')
        
        # Validate Tanvin Award logic
        if tanvin_award:
            # Tanvin Award requires team_competition
            if not team_competition:
                raise serializers.ValidationError({
                    "tanvin_award": "Tanvin Award requires team competition registration"
                })
            
            # Check if 'tanvin' is in competition codes
            competition_codes = team_competition.get('competition', [])
            if 'tanvin' not in competition_codes:
                raise serializers.ValidationError({
                    "tanvin_award": "Tanvin Award data provided but 'tanvin' not in team competitions"
                })
        
        # If 'tanvin' is in competitions, tanvin_award should be provided
        if team_competition:
            competition_codes = team_competition.get('competition', [])
            if 'tanvin' in competition_codes and not tanvin_award:
                raise serializers.ValidationError({
                    "tanvin_award": "Tanvin Award project details are required when registering for 'tanvin' competition"
                })
        
        # Collect all emails to check in one query
        emails_to_check = [participant.get('email')]
        team_name_to_check = None
        
        if team_competition:
            team_name_to_check = team_competition['team']['team_name']
            team_member_emails = [
                m.get('email') for m in team_competition['team']['participant'] 
                if m.get('email')
            ]
            emails_to_check.extend(team_member_emails)
            
            # Check for duplicate emails within team (in-memory, no DB query)
            if len(team_member_emails) != len(set(team_member_emails)):
                raise serializers.ValidationError({
                    "team_competition": "Duplicate emails found in team members"
                })
            
            # Check if leader email matches any team member email
            if participant.get('email') in team_member_emails:
                raise serializers.ValidationError({
                    "team_competition": "Team leader email cannot be the same as team member email"
                })
        
        # Single query to check all emails and team name at once
        errors = {}
        
        # Check participant email
        if Participant.objects.filter(email=participant.get('email')).only('id').exists():
            errors['participant'] = f"Email {participant.get('email')} is already registered"
        
        # Check team name if needed
        if team_name_to_check and Team.objects.filter(team_name=team_name_to_check).only('id').exists():
            errors['team_competition'] = f"Team name '{team_name_to_check}' already exists"
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    


# BONUS: Add caching for frequently accessed codes (optional but powerful)
class CachedValidationMixin:
    """
    Mixin to add caching to code validation
    Use this if you have stable segment/competition codes that don't change often
    """
    
    @staticmethod
    def get_valid_codes_cached(model, codes, cache_key_prefix, timeout=3600):
        """
        Get valid codes with caching
        
        Args:
            model: Django model class (Segment, Competition, etc.)
            codes: List of codes to validate
            cache_key_prefix: Prefix for cache key (e.g., 'valid_segments')
            timeout: Cache timeout in seconds (default 1 hour)
        """
        cache_key = f"{cache_key_prefix}_all"
        
        # Try to get from cache
        valid_codes = cache.get(cache_key)
        
        if valid_codes is None:
            # Cache miss - fetch from database
            valid_codes = set(model.objects.values_list('code', flat=True))
            cache.set(cache_key, valid_codes, timeout)
        
        # Filter requested codes
        valid_codes_set = set(codes) & valid_codes
        invalid_codes = [code for code in codes if code not in valid_codes_set]
        
        return valid_codes_set, invalid_codes


# Example usage of caching (modify your serializer methods):
class CompleteRegistrationSerializerWithCache(CompleteRegistrationSerializer):
    """
    Version with aggressive caching - use if codes rarely change
    Clear cache when you add/remove segments/competitions
    """
    
    def validate_segment(self, value):
        if not value:
            return value
        
        _, invalid_codes = CachedValidationMixin.get_valid_codes_cached(
            Segment, value, 'valid_segments', timeout=3600
        )
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid segment codes: {', '.join(invalid_codes)}"
            )
        
        return value
    
    def validate_competition(self, value):
        if not value:
            return value
        
        _, invalid_codes = CachedValidationMixin.get_valid_codes_cached(
            Competition, value, 'valid_competitions', timeout=3600
        )
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid competition codes: {', '.join(invalid_codes)}"
            )
        
        return value
    
    def validate_team_competition(self, value):
        if not value or 'competition' not in value:
            return value
        
        _, invalid_codes = CachedValidationMixin.get_valid_codes_cached(
            TeamCompetition, value['competition'], 'valid_team_competitions', timeout=3600
        )
        
        if invalid_codes:
            raise serializers.ValidationError(
                f"Invalid team competition codes: {', '.join(invalid_codes)}"
            )
        
        return value
    







class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'phone', 'amount', 'method', 'trx_id', 'datetime']


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
    payments = PaymentSerializer(many=True, read_only=True) 
    
    class Meta:
        model = Participant
        fields = [
            'id', 'full_name', 'email', 'phone', 'institution',
            'payment_verified', 'payments', 'segments', 'competitions', 'has_entry'
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
            'id', 'f_name', 'l_name', 'full_name', 'email', 'phone', 'grade', 'institution', 'address',
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
            'id', 'f_name', 'l_name', 'full_name', 'email', 'phone', 'institution', 'is_leader'
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
    id = serializers.IntegerField()



class ParticipantSerializer(serializers.ModelSerializer):
    segment_list = serializers.SerializerMethodField()
    comp_list = serializers.SerializerMethodField()
    gift_list = serializers.SerializerMethodField()
    entry_status = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'f_name', 'l_name', 'email', 'phone', 'institution', 'address', 'payment_verified',
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








class TeamMemberDetailSerializer(serializers.ModelSerializer):
    """Serializer for team member details"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamParticipant
        fields = [
            'id', 'full_name', 'f_name', 'l_name', 'gender', 
            'email', 'phone', 'institution', 'grade', 
            't_shirt_size', 'is_leader'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.f_name} {obj.l_name}"


class TeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for team details"""
    members = TeamMemberDetailSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    competitions = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'team_name', 'payment_verified', 
            'member_count', 'members', 'competitions'
        ]
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_competitions(self, obj):
        """Get all team competitions"""
        return list(
            obj.team_competition_registrations
            .select_related('competition')
            .values_list('competition__competition', flat=True)
        )


class TanvinAwardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Tanvin Award with team information"""
    team = TeamDetailSerializer(read_only=True)
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    
    class Meta:
        model = TanvinAward
        fields = [
            'id', 'team', 'project_name', 'project_type', 
            'project_type_display', 'project_description', 
            'pitch_deck', 'video_link'
        ]


class TanvinAwardListSerializer(serializers.ModelSerializer):
    """Minimal serializer for list view"""
    team_name = serializers.CharField(source='team.team_name', read_only=True)
    team_id = serializers.IntegerField(source='team.id', read_only=True)
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TanvinAward
        fields = [
            'id', 'team_id', 'team_name', 'project_name', 
            'project_type', 'project_type_display', 'member_count'
        ]
    
    def get_member_count(self, obj):
        return obj.team.members.count()