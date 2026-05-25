from django.shortcuts import get_object_or_404

from rest_framework import serializers

from .models import Internship, InternshipApplication, InternshipOffer, InternshipEngagement, ApplicationResume, InternshipStatus

from core.models import StudentProfile, LevelChoices
from core.serializers import StudentInfoSerializer, AlumniInfoSerializer

class InternshipSerializer(serializers.ModelSerializer):
    skills_required = serializers.ListField(child=serializers.CharField(), required=False)
    levels = serializers.ListField(child=serializers.ChoiceField(choices=LevelChoices.choices))
    alumnus = serializers.CharField(source="alumnus.sqid", read_only=True)
    
    class Meta:
        model = Internship
        exclude = ['is_active', 'deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'alumnus', 'is_active']
        
    def create(self, validated_data):
        available_slots = validated_data.get('available_slots', None)
        validated_data['remaining_slots'] = available_slots
        return super().create(validated_data)
        
class InternshipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = ['sqid', 'is_active']
        read_only_fields = ['sqid']
        
class InternshipOfferSerializer(serializers.ModelSerializer):
    internship = serializers.SlugRelatedField(queryset=Internship.objects.all(), write_only=True, slug_field='sqid')
    student = serializers.SlugRelatedField(queryset=StudentProfile.objects.all(), write_only=True, slug_field='sqid')
    
    internship_info = InternshipSerializer( read_only=True, source='internship')
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='internship.alumnus')
    
    class Meta:
        model = InternshipOffer
        fields = ['internship', 'student', 'internship_info', 'student_info', 'alumnus_info', 'sqid']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        internship = validated_data['internship']
        student = validated_data['student']
        
        if not internship.is_active:
            raise serializers.ValidationError("This internship is inactive. You cannot send new offers.")
        
        if InternshipOffer.objects.filter(internship=internship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already offered this internship."})
        
        if InternshipEngagement.objects.filter(mentorship=internship, student=student, status=InternshipEngagement.EngagementStatus.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "This student is already engaged in this internship."})
        
        return  validated_data
    
class InternshipApplicationSerializer(serializers.ModelSerializer):
    internship = serializers.SlugRelatedField(queryset=Internship.objects.all(), write_only=True, slug_field='sqid')
    
    internship_info = InternshipSerializer(read_only=True, source='internship')
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='internship.alumnus')
    
    resume = serializers.SlugRelatedField(queryset=ApplicationResume.objects.all(), required=False, write_only=True, slug_field='sqid')
    
    class Meta:
        model = InternshipApplication
        fields = ['sqid', 'cover_letter', 'resume', 'internship', 'internship_info', 'student_info', 'alumnus_info', 'status', 'created_at']
        read_only_fields = ['sqid', 'created_at', 'status', 'created_at','deleted_at', 'is_deleted']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        internship = validated_data['internship']
        resume = validated_data.get('resume')
        
        student = self.context['request'].user.student_profile
        require_resume = internship.require_resume
        
        if internship.is_active is False:
            raise serializers.ValidationError({"detail": "This internship is no longer active."})
        
        if InternshipApplication.objects.filter(internship=internship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already applied for this internship."})
        
        if require_resume and not resume:
            raise serializers.ValidationError({"detail": "You must upload a resume before applying for this internship."})
        
        return validated_data
        
class ApplicationResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationResume
        fields = ['resume', 'sqid']
        read_only_fields = ['sqid', 'uploaded_at', 'application', 'student']
        
class InternshipEngagementSerializer(serializers.ModelSerializer):
    internship_info = InternshipSerializer(read_only=True, source='internship')
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='alumnus')
    
    class Meta:
        model = InternshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at']
        
class ManageInternshipOfferSerializer(serializers.Serializer):
    offer_id = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        offer_id = attrs["offer_id"]

        if not offer_id:
            raise serializers.ValidationError("Offer id is required.")

        offer = get_object_or_404(InternshipOffer.objects.select_related("internship", "student", "internship__alumnus"),
            sqid=offer_id)

        if offer.student != request.user.student_profile:
            raise serializers.ValidationError({"detail": "You are not authorized to accept this internship offer."})

        if offer.status != InternshipStatus.PENDING:
            raise serializers.ValidationError({"detail": f"Offer has already been {offer.status.lower()}."})

        if not offer.internship.is_active:
            raise serializers.ValidationError({"detail": "Internship is not active."})

        if InternshipEngagement.objects.filter(internship=offer.internship, student=offer.student, status=InternshipEngagement.EngagementStatus.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "You are already engaged in this internship."})

        attrs["offer"] = offer
        return attrs
        
class ManageInternshipApplicationSerializer(serializers.Serializer):
    application_id = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        application_id = attrs["application_id"]

        if not application_id:
            raise serializers.ValidationError("Application ID is required.")

        application = get_object_or_404(InternshipApplication.objects.select_related("internship", "student", "internship__alumnus"),
            sqid=application_id)

        if application.student != request.user.student_profile:
            raise serializers.ValidationError({"detail": "You are not authorized to perform this action."})

        if application.status != InternshipStatus.PENDING:
            raise serializers.ValidationError({"detail": f"Application has already been {application.status.lower()}."})

        if not application.internship.is_active:
            raise serializers.ValidationError({"detail": "Internship is not active."})

        if InternshipEngagement.objects.filter(internship=application.internship, student=application.student).exists():
            raise serializers.ValidationError({"detail": "You are already engaged in this internship."})

        attrs["application"] = application
        return attrs
   


        