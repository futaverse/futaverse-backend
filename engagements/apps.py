from django.apps import AppConfig


class EngagementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'engagements'

    def ready(self):
        from engagements.models import BaseEngagement
        from engagements.plugins import ENGAGEMENT_PLUGIN

        for subclass in BaseEngagement.__subclasses__():
            if subclass not in ENGAGEMENT_PLUGIN:
                raise RuntimeError(
                    f"Engagement model '{subclass.__name__}' is not registered in "
                    f"engagements.plugins.ENGAGEMENT_PLUGIN. Add it to enable feed events and notifications."
                )
