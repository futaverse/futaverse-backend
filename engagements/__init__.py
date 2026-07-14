"""
Engagements — shared abstraction layer for internship and mentorship engagement models.

Provides:
  - BaseEngagement, BaseApplication, BaseOffer abstract models
  - EngagementLifecycleStatus enum
  - Generic accept/reject/withdraw views in views.py
  - Plugin registry for per-type serializers and feed metadata in plugins.py
  - Task utilities for auto-acknowledge workflow in tasks.py
  - Factory serializers for per-domain validation in serializers.py
"""
