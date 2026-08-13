"""
Engagements — shared layer for internship and mentorship engagements.

Provides:
  - Engagement concrete model with canonical EngagementType enum
  - EngagementLifecycleStatus enum and BaseApplication/BaseOffer abstract models
  - Engagement service (creation, detail resolution, display text, feed events)
  - Generic accept/reject/withdraw views in views.py
  - Serializer registry for engagement feed rendering in plugins.py
  - Auto-acknowledge task utilities in tasks.py
  - Factory serializers for per-domain validation in serializers.py
"""
