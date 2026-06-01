from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    
    def ready(self):
        """Register review plugins when app is ready."""
        from django.contrib.contenttypes.models import ContentType
        from reviews.plugins import register_plugin
        
        # Resolve InternshipEngagement and MentorshipEngagement content types
        try:
            internship_engagement_ct = ContentType.objects.get(
                app_label='internships',
                model='internshipengagement'
            )
            mentorship_engagement_ct = ContentType.objects.get(
                app_label='mentorships',
                model='mentorshipengagement'
            )
            
            from reviews.plugins import AlumnusRatesStudentPlugin, StudentRatesAlumnusPlugin
            
            # Alumni rates student after internship
            register_plugin(
                internship_engagement_ct.id,
                'alumni',
                AlumnusRatesStudentPlugin
            )
            
            # Student rates alumni after internship
            register_plugin(
                internship_engagement_ct.id,
                'student',
                StudentRatesAlumnusPlugin
            )
            
            # Alumni rates student after mentorship
            register_plugin(
                mentorship_engagement_ct.id,
                'alumni',
                AlumnusRatesStudentPlugin
            )
            
            # Student rates alumni after mentorship
            register_plugin(
                mentorship_engagement_ct.id,
                'student',
                StudentRatesAlumnusPlugin
            )
        except ContentType.DoesNotExist:
            # Content types may not exist yet (e.g., during migrations)
            pass
