from django.apps import AppConfig


class EngagementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'engagements'

    def ready(self):
        from engagements.models import Engagement
        from engagements.plugins import ENGAGEMENT_PLUGIN

        for engagement_type in Engagement.EngagementType.values:
            if engagement_type not in ENGAGEMENT_PLUGIN:
                raise RuntimeError(
                    f"Engagement type '{engagement_type}' is not registered in "
                    f"engagements.plugins.ENGAGEMENT_PLUGIN. Add it to enable feed events and notifications."
                )
