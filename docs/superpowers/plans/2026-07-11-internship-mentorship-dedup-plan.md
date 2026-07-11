# Internship & Mentorship Deduplication — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate ~350 lines of duplicated code across the `internships` and `mentorships` apps by extracting shared Application/Offer lifecycle abstractions into the existing `engagements/` shared layer.

**Architecture:** Three abstract base classes (`EngagementLifecycleStatus`, `BaseApplication`, `BaseOffer`) in `engagements/models.py`; six generic view classes in `engagements/views.py`; four serializer factory functions in `engagements/serializers.py`; and two utility helpers in `engagements/helpers.py`. Each app's concrete classes inherit/instantiate from these with class-level configuration.

**Tech Stack:** Django 5.x, Django REST Framework, Python 3.12+

## Global Constraints

- No ViewSets/routers (project convention)
- `APPEND_SLASH=False` — URL patterns must match exactly
- All existing endpoints, response shapes, and permissions stay identical
- Keep business logic and domain-specific fields inside each app
- `InternshipStatus` / `MentorshipStatus` enums replaced by shared `EngagementLifecycleStatus` — values are identical so no data migration needed, only code migration

---

## Phase 1: Shared Infrastructure in `engagements/`

### Task 1: Add abstract bases to `engagements/models.py`

**Files:**
- Modify: `engagements/models.py`

- [ ] **Step 1: Append `EngagementLifecycleStatus`, `BaseApplication`, `BaseOffer`**

Insert after the `BaseEngagement` class (after line 58). The full additions:

```python
class EngagementLifecycleStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class BaseApplication(BaseModel):
    status = models.CharField(
        choices=EngagementLifecycleStatus.choices,
        max_length=20,
        default=EngagementLifecycleStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    cover_letter = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def accept(self):
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        self.status = EngagementLifecycleStatus.WITHDRAWN
        self.save(update_fields=["status"])


class BaseOffer(BaseModel):
    status = models.CharField(
        choices=EngagementLifecycleStatus.choices,
        max_length=20,
        default=EngagementLifecycleStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def accept(self):
        self.status = EngagementLifecycleStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def reject(self):
        self.status = EngagementLifecycleStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def withdraw(self):
        self.status = EngagementLifecycleStatus.WITHDRAWN
        self.save(update_fields=["status"])
```

- [ ] **Step 2: Verify no import errors**

```powershell
python -c "from engagements.models import EngagementLifecycleStatus, BaseApplication, BaseOffer; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add engagements/models.py
git commit -m "feat(engagements): add abstract lifecycle status, application, offer bases"
```

---

### Task 2: Create `engagements/helpers.py`

**Files:**
- Create: `engagements/helpers.py`

- [ ] **Step 1: Write the helpers**

```python
from django.urls import path

from core.models import User


def queryset_by_role(user, model_class, *, alumnus_filter, student_filter,
                     select_related=(), order_by=None):
    if user.role == User.Role.ALUMNI:
        qs = model_class.objects.filter(**alumnus_filter)
    elif user.role == User.Role.STUDENT:
        qs = model_class.objects.filter(**student_filter)
    else:
        return model_class.objects.none()

    if select_related:
        qs = qs.select_related(*select_related)
    if order_by:
        qs = qs.order_by(order_by)
    return qs


def generate_engagement_urls(*, prefix, entity_views, application_views,
                              offer_views, engagement_views, extra=None):
    patterns = []

    patterns.append(path(
        "/application",
        application_views["create"].as_view(),
        name=f"create-{prefix}-application",
    ))
    patterns.append(path(
        "/applications",
        application_views["list"].as_view(),
        name=f"list-{prefix}-applications",
    ))
    patterns.append(path(
        "/applications/<slug:sqid>",
        application_views["retrieve"].as_view(),
        name=f"retrieve-{prefix}-application",
    ))
    patterns.append(path(
        "/applications/<slug:application_id>/accept",
        application_views["accept"].as_view(),
        name=f"accept-{prefix}-application",
    ))
    patterns.append(path(
        "/applications/<slug:application_id>/reject",
        application_views["reject"].as_view(),
        name=f"reject-{prefix}-application",
    ))
    patterns.append(path(
        "/applications/<slug:application_id>/withdraw",
        application_views["withdraw"].as_view(),
        name=f"withdraw-{prefix}-application",
    ))

    patterns.append(path(
        "/offer",
        offer_views["create"].as_view(),
        name=f"create-{prefix}-offer",
    ))
    patterns.append(path(
        "/offers",
        offer_views["list"].as_view(),
        name=f"list-{prefix}-offers",
    ))
    patterns.append(path(
        "/offers/<slug:sqid>",
        offer_views["retrieve"].as_view(),
        name=f"retrieve-{prefix}-offer",
    ))
    patterns.append(path(
        "/offers/<slug:offer_id>/accept",
        offer_views["accept"].as_view(),
        name=f"accept-{prefix}-offer",
    ))
    patterns.append(path(
        "/offers/<slug:offer_id>/reject",
        offer_views["reject"].as_view(),
        name=f"reject-{prefix}-offer",
    ))
    patterns.append(path(
        "/offers/<slug:offer_id>/withdraw",
        offer_views["withdraw"].as_view(),
        name=f"withdraw-{prefix}-offer",
    ))

    patterns.append(path(
        "/engagements",
        engagement_views["list"].as_view(),
        name=f"list-{prefix}-engagements",
    ))
    patterns.append(path(
        "/engagements/<slug:sqid>",
        engagement_views["retrieve"].as_view(),
        name=f"retrieve-{prefix}-engagement",
    ))
    patterns.append(path(
        "/engagements/<slug:sqid>/completed",
        engagement_views["completed"].as_view(),
        name=f"mark-{prefix}-completed",
    ))
    patterns.append(path(
        "/engagements/<slug:sqid>/acknowledged",
        engagement_views["acknowledged"].as_view(),
        name=f"mark-{prefix}-acknowledged",
    ))

    patterns.append(path(
        "",
        entity_views["list_create"].as_view(),
        name=f"list-create-{prefix}s",
    ))
    patterns.append(path(
        "/<slug:sqid>",
        entity_views["rud"].as_view(),
        name=f"rud-{prefix}",
    ))
    patterns.append(path(
        "/<slug:sqid>/toggle-active",
        entity_views["toggle_active"].as_view(),
        name=f"toggle-{prefix}-active",
    ))

    if extra:
        patterns.extend(extra)

    return patterns
```

- [ ] **Step 2: Verify the module imports**

```powershell
python -c "from engagements.helpers import queryset_by_role, generate_engagement_urls; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add engagements/helpers.py
git commit -m "feat(engagements): add queryset_by_role helper and URL generator"
```

---

### Task 3: Create `engagements/serializers.py`

**Files:**
- Create: `engagements/serializers.py`

- [ ] **Step 1: Write the four serializer factory functions**

```python
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from engagements.models import EngagementLifecycleStatus


def make_student_manage_offer_serializer(offer_model, engagement_model, relation_name):
    """
    Factory for student accept/reject offer serializers.
    relation_name is the FK field on the offer model pointing to the parent entity
    (e.g. "internship", "mentorship").
    """

    class StudentManageOfferSerializer(serializers.Serializer):
        offer_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            offer_id = attrs["offer_id"]

            if not offer_id:
                raise serializers.ValidationError("Offer id is required.")

            offer = get_object_or_404(
                offer_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=offer_id,
            )

            if offer.student != request.user.student_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to perform this action."}
                )

            if offer.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"This offer has already been {offer.status.lower()}."}
                )

            parent = getattr(offer, relation_name)
            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if engagement_model.objects.filter(
                **{relation_name: parent},
                student=offer.student,
                status="active",
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "You are already engaged in this opportunity."}
                )

            attrs["offer"] = offer
            return attrs

    return StudentManageOfferSerializer


def make_alumnus_manage_offer_serializer(offer_model, relation_name):
    """
    Factory for alumnus withdraw offer serializers.
    """

    class AlumnusManageOfferSerializer(serializers.Serializer):
        offer_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            offer_id = attrs["offer_id"]

            if not offer_id:
                raise serializers.ValidationError("Offer id is required.")

            offer = get_object_or_404(
                offer_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=offer_id,
            )

            parent = getattr(offer, relation_name)
            if parent.alumnus != request.user.alumni_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to withdraw this offer."}
                )

            if offer.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"This offer has already been {offer.status.lower()}."}
                )

            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            attrs["offer"] = offer
            return attrs

    return AlumnusManageOfferSerializer


def make_student_manage_application_serializer(
    application_model, engagement_model, relation_name
):
    """
    Factory for student withdraw application serializers.
    """

    class StudentManageApplicationSerializer(serializers.Serializer):
        application_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            application_id = attrs["application_id"]

            if not application_id:
                raise serializers.ValidationError("Application ID is required.")

            application = get_object_or_404(
                application_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=application_id,
            )

            if application.student != request.user.student_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to perform this action."}
                )

            if application.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"Application has already been {application.status.lower()}."}
                )

            parent = getattr(application, relation_name)
            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if engagement_model.objects.filter(
                **{relation_name: parent},
                student=application.student,
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "You are already engaged in this opportunity."}
                )

            attrs["application"] = application
            return attrs

    return StudentManageApplicationSerializer


def make_alumnus_manage_application_serializer(
    application_model, engagement_model, relation_name
):
    """
    Factory for alumnus accept/reject application serializers.
    """

    class AlumnusManageApplicationSerializer(serializers.Serializer):
        application_id = serializers.CharField()

        def validate(self, attrs):
            request = self.context["request"]
            application_id = attrs["application_id"]

            if not application_id:
                raise serializers.ValidationError("Application ID is required.")

            application = get_object_or_404(
                application_model.objects.select_related(
                    relation_name, "student", f"{relation_name}__alumnus"
                ),
                sqid=application_id,
            )

            parent = getattr(application, relation_name)
            if parent.alumnus != request.user.alumni_profile:
                raise serializers.ValidationError(
                    {"detail": "You are not authorized to manage this application."}
                )

            if application.status != EngagementLifecycleStatus.PENDING:
                raise serializers.ValidationError(
                    {"detail": f"Application has already been {application.status.lower()}."}
                )

            if not parent.is_active:
                raise serializers.ValidationError(
                    {"detail": "This opportunity is not active."}
                )

            if engagement_model.objects.filter(
                **{relation_name: parent},
                student=application.student,
            ).exists():
                raise serializers.ValidationError(
                    {"detail": "This student is already engaged in this opportunity."}
                )

            attrs["application"] = application
            return attrs

    return AlumnusManageApplicationSerializer
```

- [ ] **Step 2: Verify the module imports**

```powershell
python -c "from engagements.serializers import make_student_manage_offer_serializer, make_alumnus_manage_offer_serializer, make_student_manage_application_serializer, make_alumnus_manage_application_serializer; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add engagements/serializers.py
git commit -m "feat(engagements): add serializer factories for offer/application management"
```

---

### Task 4: Add generic views to `engagements/views.py`

**Files:**
- Modify: `engagements/views.py` (currently empty)

- [ ] **Step 1: Write the six generic view classes**

```python
from django.db import transaction

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent


class AcceptApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    application_model = None
    engagement_model = None
    engagement_serializer_class = None
    validation_serializer_class = None
    relation_name = None

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        parent = getattr(application, self.relation_name)
        student = application.student
        alumnus = parent.alumnus

        engagement = self.engagement_model.objects.create(
            **{self.relation_name: parent},
            student=student,
            alumnus=alumnus,
            source=self.engagement_model.Source.APPLICATION,
            source_id=application.id,
        )

        application.accept()
        parent.decrement_remaining_slots()

        return Response(
            {
                "detail": "Application accepted successfully.",
                "engagement": self.engagement_serializer_class(engagement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RejectApplicationView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        application.reject()

        return Response(
            {"detail": "Application rejected successfully."},
            status=status.HTTP_200_OK,
        )


class WithdrawApplicationView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"application_id": kwargs.get("application_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data["application"]

        application.withdraw()

        return Response(
            {"detail": "Application withdrawn successfully."},
            status=status.HTTP_200_OK,
        )


class AcceptOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    offer_model = None
    engagement_model = None
    engagement_serializer_class = None
    validation_serializer_class = None
    relation_name = None

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        parent = getattr(offer, self.relation_name)
        student = offer.student
        alumnus = parent.alumnus

        engagement = self.engagement_model.objects.create(
            **{self.relation_name: parent},
            student=student,
            alumnus=alumnus,
            source=self.engagement_model.Source.OFFER,
            source_id=offer.id,
        )

        offer.accept()
        parent.decrement_remaining_slots()

        return Response(
            {
                "detail": "Offer accepted successfully.",
                "engagement": self.engagement_serializer_class(engagement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RejectOfferView(APIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        offer.reject()

        return Response(
            {"detail": "Offer rejected successfully."},
            status=status.HTTP_200_OK,
        )


class WithdrawOfferView(APIView):
    permission_classes = [IsAuthenticatedAlumnus]
    serializer_class = None

    validation_serializer_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.validation_serializer_class(
            data={"offer_id": kwargs.get("offer_id")},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.validated_data["offer"]

        offer.withdraw()

        return Response(
            {"detail": "Offer withdrawn successfully."},
            status=status.HTTP_200_OK,
        )
```

- [ ] **Step 2: Verify imports**

```powershell
python -c "from engagements.views import AcceptApplicationView, RejectApplicationView, WithdrawApplicationView, AcceptOfferView, RejectOfferView, WithdrawOfferView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add engagements/views.py
git commit -m "feat(engagements): add generic accept/reject/withdraw views for applications and offers"
```

---

### Task 5: Update `engagements/plugins.py`

**Files:**
- Modify: `engagements/plugins.py`

- [ ] **Step 1: No changes needed**

The plugins file imports `InternshipEngagement`, `MentorshipEngagement` and their feed serializers — none of which reference `InternshipStatus` or `MentorshipStatus`. The status enum references are internal to model methods. No import updates needed here.

- [ ] **Step 2: Confirm**

```powershell
python -c "from engagements.plugins import ENGAGEMENT_PLUGIN, get_engagement_plugin; print('OK')"
```

Expected: `OK`

---

## Phase 2: Migrate `internships/`

### Task 6: Update `internships/models.py`

**Files:**
- Modify: `internships/models.py`

- [ ] **Step 1: Remove `InternshipStatus` class and update `InternshipApplication` and `InternshipOffer` to inherit from bases**

Remove `InternshipStatus` (lines 8-12). Update `InternshipApplication` and `InternshipOffer` to inherit from `BaseApplication` and `BaseOffer` respectively, removing the duplicated fields and methods.

Replace the entire model file with:

```python
from django.db import models
from core.models import StudentProfile, AlumniProfile
from futaverse.models import BaseModel
from django.utils import timezone

from engagements.models import BaseEngagement, BaseApplication, BaseOffer, EngagementLifecycleStatus


class Internship(BaseModel):
    class WorkMode(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'

    class EngagementType(models.TextChoices):
        FULL_TIME = 'Full-time', 'Full-time'
        PART_TIME = 'Part-time', 'Part-time'
        CONTRACT = 'Contract', 'Contract'

    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='internships')

    title = models.CharField(max_length=255)
    description = models.TextField()
    work_mode = models.CharField(choices=WorkMode.choices, max_length=20)
    engagement_type = models.CharField(choices=EngagementType.choices, max_length=20)
    location = models.CharField(max_length=255)
    skills_required = models.JSONField(default=list, blank=True)
    duration_weeks = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    levels = models.JSONField(default=list)

    company = models.CharField(max_length=255)
    company_type = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    company_linkedin_url = models.URLField(blank=True, null=True, max_length=200)
    company_website_url = models.URLField(blank=True, null=True, max_length=200)

    available_slots = models.PositiveIntegerField(blank=True, null=True)
    remaining_slots = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    require_resume = models.BooleanField(default=True)
    require_cover_letter = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])

    def decrement_remaining_slots(self):
        if self.available_slots is None:
            return

        if self.remaining_slots > 0:
            self.remaining_slots -= 1
            self.save(update_fields=['remaining_slots'])
            return self.remaining_slots
        return 0

    def __str__(self):
        return f"{self.title} (internship)"

    @property
    def feed_targets(self):
        targets = []

        for skill in self.skills_required:
            targets.append({'target_type': 'skill', 'target_value': skill})

        if self.industry:
            targets.append({'target_type': 'industry', 'target_value': self.industry})

        if self.company_type:
            targets.append({'target_type': 'company_type', 'target_value': self.company_type})

        return targets


class InternshipApplication(BaseApplication):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internship_applications')

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.internship.title} (internship)"


class InternshipOffer(BaseOffer):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internship_offers')

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer to {self.student.full_name} for {self.internship.title}"


class InternshipEngagement(BaseEngagement):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer"

    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='engagements')

    @property
    def post_context(self):
        return {
            "type": "internship",
            "title": self.internship.title,
            "company": self.internship.company,
        }

    def __str__(self):
        return f"Engagement of {self.student.full_name} in {self.internship.title}"


class ApplicationResume(BaseModel):
    application = models.OneToOneField(InternshipApplication, on_delete=models.CASCADE, related_name='resume', blank=True, null=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, related_name='application_resumes', null=True)
    resume = models.URLField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.application:
            return f"Resume of {self.application.student.full_name} for {self.application.internship.title}"
        return f"Unlinked resume (ID: {self.sqid})"
```

- [ ] **Step 2: Verify model imports**

```powershell
python -c "from internships.models import Internship, InternshipApplication, InternshipOffer, InternshipEngagement, ApplicationResume; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Generate and verify migration**

```powershell
python manage.py makemigrations internships
```

Review the generated migration file in `internships/migrations/`. Verify:
- No `AddField` operations for `status`, `responded_at`, `cover_letter` (these columns already exist)
- No `DeleteField` operations
- Only `AlterField` operations (Django changes field to point to abstract parent)

- [ ] **Step 4: Apply migration**

```powershell
python manage.py migrate internships
```

- [ ] **Step 5: Commit**

```powershell
git add internships/models.py internships/migrations/
git commit -m "refactor(internships): inherit application/offer from shared abstract bases"
```

---

### Task 7: Update `internships/serializers.py`

**Files:**
- Modify: `internships/serializers.py`

- [ ] **Step 1: Replace 4 management serializers with factory calls**

Replace the content with:

```python
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from .models import Internship, InternshipApplication, InternshipOffer, InternshipEngagement, ApplicationResume
from engagements.models import EngagementLifecycleStatus

from core.models import StudentProfile, LevelChoices
from core.serializers import StudentInfoSerializer, AlumniInfoSerializer

from engagements.serializers import (
    make_student_manage_offer_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_alumnus_manage_application_serializer,
)


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

    internship_info = InternshipSerializer(read_only=True, source='internship')
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

        request = self.context["request"]
        if internship.alumnus != request.user.alumni_profile:
            raise serializers.ValidationError("You can only send offers for your own internships.")

        if not internship.is_active:
            raise serializers.ValidationError("This internship is inactive. You cannot send new offers.")

        if InternshipOffer.objects.filter(internship=internship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already offered this internship."})

        if InternshipEngagement.objects.filter(internship=internship, student=student, status=InternshipEngagement.EngagementStatus.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "This student is already engaged in this internship."})

        return validated_data


class InternshipApplicationSerializer(serializers.ModelSerializer):
    internship = serializers.SlugRelatedField(queryset=Internship.objects.all(), write_only=True, slug_field='sqid')

    internship_info = InternshipSerializer(read_only=True, source='internship')
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='internship.alumnus')

    resume = serializers.SlugRelatedField(queryset=ApplicationResume.objects.all(), required=False, write_only=True, slug_field='sqid')

    class Meta:
        model = InternshipApplication
        fields = ['sqid', 'cover_letter', 'resume', 'internship', 'internship_info', 'student_info', 'alumnus_info', 'status', 'created_at']
        read_only_fields = ['sqid', 'created_at', 'status']

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

    engagement = serializers.CharField(read_only=True, source='engagement_ptr.sqid')

    class Meta:
        model = InternshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id', 'internship', 'student', 'alumnus']
        read_only_fields = ['sqid', 'created_at', 'updated_at']


StudentManageInternshipOfferSerializer = make_student_manage_offer_serializer(
    InternshipOffer, InternshipEngagement, "internship"
)

AlumnusManageInternshipOfferSerializer = make_alumnus_manage_offer_serializer(
    InternshipOffer, "internship"
)

StudentManageInternshipApplicationSerializer = make_student_manage_application_serializer(
    InternshipApplication, InternshipEngagement, "internship"
)

AlumnusManageInternshipApplicationSerializer = make_alumnus_manage_application_serializer(
    InternshipApplication, InternshipEngagement, "internship"
)


class InternshipEngagementFeedSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source='internship.title')
    company = serializers.CharField(source='internship.company')
    alumnus_name = serializers.CharField(source='alumnus.full_name')

    class Meta:
        model = InternshipEngagement
        fields = ['sqid', 'internship_title', 'company', 'alumnus_name', 'status']
```

- [ ] **Step 2: Verify imports**

```powershell
python -c "from internships.serializers import InternshipSerializer, StudentManageInternshipOfferSerializer, AlumnusManageInternshipOfferSerializer, StudentManageInternshipApplicationSerializer, AlumnusManageInternshipApplicationSerializer; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add internships/serializers.py
git commit -m "refactor(internships): replace management serializers with factory calls"
```

---

### Task 8: Update `internships/views/applications.py`

**Files:**
- Modify: `internships/views/applications.py`

- [ ] **Step 1: Replace Accept/Reject/Withdraw views with subclasses of generic views**

Replace the file with:

```python
from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from internships.models import InternshipApplication, ApplicationResume, InternshipEngagement
from internships.serializers import (
    InternshipApplicationSerializer,
    ApplicationResumeSerializer,
    StudentManageInternshipApplicationSerializer,
    AlumnusManageInternshipApplicationSerializer,
    InternshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent
from futaverse.utils.supabase import upload_file_to_supabase

from engagements.helpers import queryset_by_role
from engagements.views import AcceptApplicationView, RejectApplicationView, WithdrawApplicationView


@extend_schema(tags=['Internship Applications'], summary='Apply for an internship (student)')
class CreateInternshipApplicationView(generics.CreateAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedStudent]

    @transaction.atomic
    def perform_create(self, serializer):
        resume = serializer.validated_data.pop('resume', None)
        student = self.request.user.student_profile

        application = serializer.save(student=student)

        if resume:
            resume.application = application
            resume.save(update_fields=['application'])


@extend_schema(tags=['Internship Applications'], summary='List all internship applications (alumnus and student)')
class ListInternshipApplicationsView(generics.ListAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter={
                "internship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter={
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("internship", "student", "resume"),
            order_by="-created_at",
        )


@extend_schema(tags=['Internship Applications'], summary='Retrieve an internship application by id (alumnus and student)')
class RetrieveInternshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipApplicationSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipApplication,
            alumnus_filter={"internship__alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("internship", "student", "internship__alumnus"),
        )


@extend_schema(tags=['Internship Applications'], summary='Upload a resume for an internship application (student)')
class UploadApplicationResumeView(generics.CreateAPIView):
    queryset = ApplicationResume.objects.all()
    serializer_class = ApplicationResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticatedStudent]

    def create(self, request, *args, **kwargs):
        resume = request.FILES.get('resume')
        student = request.user.student_profile

        if not resume:
            return Response({"detail": "Resume not provided", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        resume_url = upload_file_to_supabase(resume, 'application_resumes/')

        serializer = self.get_serializer(data={'resume': resume_url})
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Internship Applications'], summary='Accept an internship application (alumnus)')
class AcceptInternshipApplicationView(AcceptApplicationView):
    application_model = InternshipApplication
    engagement_model = InternshipEngagement
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer
    relation_name = "internship"


@extend_schema(tags=['Internship Applications'], summary='Reject an internship application (alumnus)')
class RejectInternshipApplicationView(RejectApplicationView):
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer


@extend_schema(tags=['Internship Applications'], summary='Withdraw an internship application (student)')
class WithdrawInternshipApplicationView(WithdrawApplicationView):
    validation_serializer_class = StudentManageInternshipApplicationSerializer
```

- [ ] **Step 2: Verify imports**

```powershell
python -c "from internships.views.applications import AcceptInternshipApplicationView, RejectInternshipApplicationView, WithdrawInternshipApplicationView, CreateInternshipApplicationView, ListInternshipApplicationsView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add internships/views/applications.py
git commit -m "refactor(internships): use generic views for application management"
```

---

### Task 9: Update `internships/views/offers.py`

**Files:**
- Modify: `internships/views/offers.py`

- [ ] **Step 1: Replace Accept/Reject/Withdraw views with subclasses**

Replace the file with:

```python
from drf_spectacular.utils import extend_schema

from rest_framework import generics

from internships.models import InternshipOffer, InternshipEngagement
from internships.serializers import (
    InternshipOfferSerializer,
    StudentManageInternshipOfferSerializer,
    AlumnusManageInternshipOfferSerializer,
    InternshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.helpers import queryset_by_role
from engagements.views import AcceptOfferView, RejectOfferView, WithdrawOfferView


@extend_schema(tags=['Internship Offers'], summary='Create an internship offer (alumnus)')
class CreateInternshipOfferView(generics.CreateAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]


@extend_schema(tags=['Internship Offers'], summary='List internship offers (alumnus, student)')
class ListInternshipOfferView(generics.ListAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipOffer,
            alumnus_filter={
                "internship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter={
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("internship", "student"),
            order_by="-created_at",
        )


@extend_schema(tags=['Internship Offers'], summary='Retrieve an internship offer by id (alumnus and student)')
class RetrieveInternshipOfferView(generics.RetrieveAPIView):
    serializer_class = InternshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipOffer,
            alumnus_filter={"internship__alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("internship", "student", "internship__alumnus"),
        )


@extend_schema(tags=['Internship Offers'], summary='Accept an internship offer (student)')
class AcceptInternshipOfferView(AcceptOfferView):
    offer_model = InternshipOffer
    engagement_model = InternshipEngagement
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = StudentManageInternshipOfferSerializer
    relation_name = "internship"


@extend_schema(tags=['Internship Offers'], summary='Reject an internship offer (student)')
class RejectInternshipOfferView(RejectOfferView):
    validation_serializer_class = StudentManageInternshipOfferSerializer


@extend_schema(tags=['Internship Offers'], summary='Withdraw an internship offer (alumnus)')
class WithdrawInternshipOfferView(WithdrawOfferView):
    validation_serializer_class = AlumnusManageInternshipOfferSerializer
```

- [ ] **Step 2: Verify imports**

```powershell
python -c "from internships.views.offers import AcceptInternshipOfferView, RejectInternshipOfferView, WithdrawInternshipOfferView, CreateInternshipOfferView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add internships/views/offers.py
git commit -m "refactor(internships): use generic views for offer management"
```

---

### Task 10: Update `internships/views/internships.py`

**Files:**
- Modify: `internships/views/internships.py`

- [ ] **Step 1: Use `queryset_by_role` in list/retrieve views and update status import**

Replace the file with:

```python
from django_q.tasks import async_task
from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view

from engagements.mixins import MarkEngagementCompletedMixin, MarkEngagementAcknowledgedMixin
from engagements.helpers import queryset_by_role

from internships.models import Internship, InternshipEngagement
from internships.serializers import InternshipSerializer, InternshipStatusSerializer, InternshipEngagementSerializer
from core.models import User
from feed.models import FeedEvent

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent


@extend_schema_view(
    list=extend_schema(summary="List internships (alumnus)"),
    create=extend_schema(summary="Create an internship (alumnus)"),
)
@extend_schema(tags=['Internships'])
class ListCreateInternshipView(generics.ListCreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]

    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus').order_by('-created_at')

    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        internship = serializer.save(alumnus=alumnus)

        async_task("feed.tasks.create_feed_event_task",
            event_type=FeedEvent.EventType.INTERNSHIP_CREATED,
            related_object_id=internship.id,
            related_model='internship',
            audience=FeedEvent.Audience.STUDENT,
            data={
                'title':   internship.title,
                'alumni': internship.alumnus.full_name,
                'work_mode': internship.work_mode,
                'engagement_type': internship.engagement_type,
                'stipend': str(internship.stipend),
                'is_paid': internship.is_paid,
                'available_slots': internship.available_slots,
                'remaining_slots': internship.remaining_slots,
                'created_at': internship.created_at.isoformat(),
            }
        )


@extend_schema_view(
    retrieve=extend_schema(summary="Get an internship by id (alumnus)"),
    update=extend_schema(summary="Update an internship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an internship by id (alumnus)"),
)
@extend_schema(tags=['Internships'])
class RetrieveUpdateDestroyInternshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternshipSerializer
    http_method_names = ['patch', 'get', 'delete']
    permission_classes = [IsAuthenticatedAlumnus]
    lookup_field = 'sqid'

    def get_queryset(self):
        user = self.request.user
        return Internship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema(tags=['Internships'], summary='Toggle internship active status (alumnus)')
class ToggleInternshipActiveView(generics.UpdateAPIView):
    queryset = Internship.objects.all()
    serializer_class = InternshipStatusSerializer
    http_method_names = ['patch']
    permission_classes = [IsAuthenticatedAlumnus]
    lookup_field = 'sqid'

    def perform_update(self, serializer):
        serializer.instance.toggle_active()


@extend_schema(tags=['Internship Engagements'], summary='List all internship engagements (alumnus and student)')
class ListInternshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipEngagement,
            alumnus_filter={"alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("internship", "student", "alumnus"),
        )


@extend_schema(tags=['Internship Engagements'], summary='Retrieve an internship engagement by id (alumnus and student)')
class RetrieveInternshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = InternshipEngagementSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            InternshipEngagement,
            alumnus_filter={"alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("internship", "student", "alumnus"),
        )


@extend_schema(tags=['Internship Engagements'], summary='Mark an internship engagement as completed (alumnus)')
class MarkInternshipCompletedView(MarkEngagementCompletedMixin, generics.UpdateAPIView):
    queryset = InternshipEngagement.objects.all()
    engagement_type = 'internship_engagement'
    serializer_class = InternshipEngagementSerializer


@extend_schema(tags=['Internship Engagements'], summary='Mark an internship engagement as acknowledged (student)')
class MarkInternshipAcknowledgedView(MarkEngagementAcknowledgedMixin, generics.UpdateAPIView):
    queryset = InternshipEngagement.objects.all()
    engagement_type = 'internship_engagement'
    serializer_class = InternshipEngagementSerializer
```

- [ ] **Step 2: Verify**

```powershell
python -c "from internships.views.internships import ListCreateInternshipView, ListInternshipEngagementsView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add internships/views/internships.py
git commit -m "refactor(internships): use queryset_by_role in list/retrieve views"
```

---

### Task 11: Simplify `internships/urls.py`

**Files:**
- Modify: `internships/urls.py`

- [ ] **Step 1: Replace with `generate_engagement_urls`**

```python
from django.urls import path

from engagements.helpers import generate_engagement_urls

from .views.applications import (
    ListInternshipApplicationsView,
    CreateInternshipApplicationView,
    UploadApplicationResumeView,
    AcceptInternshipApplicationView,
    RejectInternshipApplicationView,
    WithdrawInternshipApplicationView,
    RetrieveInternshipApplicationView,
)

from .views.offers import (
    ListInternshipOfferView,
    CreateInternshipOfferView,
    AcceptInternshipOfferView,
    RejectInternshipOfferView,
    WithdrawInternshipOfferView,
    RetrieveInternshipOfferView,
)

from .views.internships import (
    ListCreateInternshipView,
    ToggleInternshipActiveView,
    RetrieveInternshipEngagementView,
    ListInternshipEngagementsView,
    RetrieveUpdateDestroyInternshipView,
    MarkInternshipAcknowledgedView,
    MarkInternshipCompletedView,
)

urlpatterns = generate_engagement_urls(
    prefix="internship",
    entity_views={
        "list_create": ListCreateInternshipView,
        "rud": RetrieveUpdateDestroyInternshipView,
        "toggle_active": ToggleInternshipActiveView,
    },
    application_views={
        "create": CreateInternshipApplicationView,
        "list": ListInternshipApplicationsView,
        "retrieve": RetrieveInternshipApplicationView,
        "accept": AcceptInternshipApplicationView,
        "reject": RejectInternshipApplicationView,
        "withdraw": WithdrawInternshipApplicationView,
    },
    offer_views={
        "create": CreateInternshipOfferView,
        "list": ListInternshipOfferView,
        "retrieve": RetrieveInternshipOfferView,
        "accept": AcceptInternshipOfferView,
        "reject": RejectInternshipOfferView,
        "withdraw": WithdrawInternshipOfferView,
    },
    engagement_views={
        "list": ListInternshipEngagementsView,
        "retrieve": RetrieveInternshipEngagementView,
        "completed": MarkInternshipCompletedView,
        "acknowledged": MarkInternshipAcknowledgedView,
    },
    extra=[
        path('/upload-resume', UploadApplicationResumeView.as_view(), name='upload-application-resume'),
    ],
)
```

- [ ] **Step 2: Verify URL resolution**

```powershell
python manage.py check --deploy 2>&1 | Select-String "internship"
```

Expected: No errors related to internships URLs.

- [ ] **Step 3: Commit**

```powershell
git add internships/urls.py
git commit -m "refactor(internships): use URL generator for standard endpoints"
```

---

### Task 12: Update `internships/tests/`

**Files:**
- Modify: `internships/tests/test_serializers.py`
- Modify: `internships/tests/test_views.py`

- [ ] **Step 1: Update import in `test_serializers.py`**

Change line 4-6 from:
```python
from internships.models import (
    Internship, InternshipApplication, InternshipOffer,
    InternshipEngagement, InternshipStatus,
)
```
To:
```python
from internships.models import (
    Internship, InternshipApplication, InternshipOffer,
    InternshipEngagement,
)
from engagements.models import EngagementLifecycleStatus
```

Then replace all `InternshipStatus.PENDING` (10 occurrences) with `EngagementLifecycleStatus.PENDING`.

- [ ] **Step 2: Update import in `test_views.py`**

Change line 3-5 from:
```python
from internships.models import (
    Internship, InternshipEngagement, InternshipStatus,
)
```
To:
```python
from internships.models import (
    Internship, InternshipEngagement,
)
```

- [ ] **Step 3: Run the internship tests**

```powershell
python manage.py test internships
```

Expected: All tests pass (or same failures as before the refactor — tests may have pre-existing issues).

- [ ] **Step 4: Commit**

```powershell
git add internships/tests/
git commit -m "refactor(internships): update test imports to shared lifecycle status"
```

---

### Task 13: Delete `internships/mixins.py`

**Files:**
- Delete: `internships/mixins.py`

- [ ] **Step 1: Delete file and verify nothing breaks**

```powershell
Remove-Item -LiteralPath "internships\mixins.py"
```

```powershell
python -c "import internships.views.applications; import internships.views.offers; print('OK')"
```

Expected: `OK` (the mixins were only imported by the old view code, which we've replaced).

- [ ] **Step 2: Commit**

```powershell
git rm internships/mixins.py
git commit -m "refactor(internships): remove mixins.py (replaced by shared serializer factories)"
```

---

## Phase 3: Migrate `mentorships/`

### Task 14: Update `mentorships/models.py`

**Files:**
- Modify: `mentorships/models.py`

- [ ] **Step 1: Remove `MentorshipStatus`, inherit from bases**

Replace the file with:

```python
from django.db import models
from core.models import AlumniProfile, StudentProfile
from futaverse.models import BaseModel
from django.utils import timezone
from .lib import FocusArea, MentorshipCategory

from engagements.models import BaseEngagement, BaseApplication, BaseOffer, EngagementLifecycleStatus


class Mentorship(BaseModel):
    class WorkMode(models.TextChoices):
        REMOTE = 'Remote', 'Remote'
        HYBRID = 'Hybrid', 'Hybrid'
        ONSITE = 'Onsite', 'Onsite'

    alumnus = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorships')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=MentorshipCategory.choices)
    focus_areas = models.JSONField(default=list, blank=True)

    work_mode = models.CharField(choices=WorkMode.choices, max_length=20, default=WorkMode.REMOTE, blank=True)
    duration_weeks = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    available_slots = models.PositiveIntegerField(blank=True, null=True)
    remaining_slots = models.PositiveIntegerField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (mentorship)"

    def decrement_remaining_slots(self):
        if self.remaining_slots > 0:
            self.remaining_slots -= 1
            self.save(update_fields=['remaining_slots'])
            return self.remaining_slots
        return 0

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])

    @property
    def feed_targets(self):
        targets = []

        for area in self.focus_areas:
            targets.append({'target_type': 'skill', 'target_value': area})

        if self.category:
            targets.append({'target_type': 'category', 'target_value': self.category})

        return targets


class MentorshipApplication(BaseApplication):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_applications')

    cover_letter = models.TextField()

    def __str__(self):
        return f"Application of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipOffer(BaseOffer):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='offers')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_offers')

    def __str__(self):
        return f"Offer of {self.student.full_name} for {self.mentorship.title} (mentorship)"


class MentorshipRequest(BaseOffer):
    mentor = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentorship_requests')
    message = models.TextField()

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request by {self.student.full_name} to {self.mentor.full_name}"


class MentorshipEngagement(BaseEngagement):
    class Source(models.TextChoices):
        APPLICATION = "application", "Application"
        OFFER = "offer", "Offer"
        REQUEST = "request", "Request"

    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='engagements')

    @property
    def post_context(self):
        return {
            "type": "mentorship",
            "title": self.mentorship.title,
            "focus_areas": self.mentorship.focus_areas,
            "category": self.mentorship.category,
        }

    def __str__(self):
        return f"Engagement of {self.student.full_name} in {self.mentorship.title}"
```

- [ ] **Step 2: Verify**

```powershell
python -c "from mentorships.models import Mentorship, MentorshipApplication, MentorshipOffer, MentorshipRequest, MentorshipEngagement; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Generate and verify migration**

```powershell
python manage.py makemigrations mentorships
```

Review the generated migration. Verify: no `AddField` for existing columns, only `AlterField`.

- [ ] **Step 4: Apply migration**

```powershell
python manage.py migrate mentorships
```

- [ ] **Step 5: Commit**

```powershell
git add mentorships/models.py mentorships/migrations/
git commit -m "refactor(mentorships): inherit application/offer/request from shared abstract bases"
```

---

### Task 15: Update `mentorships/serializers.py`

**Files:**
- Modify: `mentorships/serializers.py`

- [ ] **Step 1: Replace management serializers with factory calls**

Replace the file with:

```python
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from core.serializers import StudentInfoSerializer, AlumniInfoSerializer
from core.models import StudentProfile

from .models import Mentorship, MentorshipOffer, MentorshipApplication, MentorshipEngagement
from engagements.models import EngagementLifecycleStatus

from futaverse.serializers import StrictFieldsMixin
from mentorships.lib import FocusArea, MentorshipCategory

from engagements.serializers import (
    make_student_manage_offer_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_alumnus_manage_application_serializer,
)


class MentorshipSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    focus_areas = serializers.ListField(child=serializers.ChoiceField(choices=FocusArea.choices), required=False)
    category = serializers.ChoiceField(choices=MentorshipCategory.choices)

    class Meta:
        model = Mentorship
        exclude = ['is_active', 'deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'updated_at', 'alumnus', 'remaining_slots']

    def create(self, validated_data):
        available_slots = validated_data.get('available_slots', None)
        validated_data['remaining_slots'] = available_slots
        return super().create(validated_data)


class MentorshipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentorship
        fields = ['sqid', 'is_active']
        read_only_fields = ['sqid']


class MentorshipOfferSerializer(serializers.ModelSerializer):
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid', write_only=True)
    student = serializers.SlugRelatedField(queryset=StudentProfile.objects.all(), slug_field='sqid', write_only=True)

    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        mentorship = validated_data['mentorship']
        student = validated_data['student']

        request = self.context["request"]
        if mentorship.alumnus != request.user.alumni_profile:
            raise serializers.ValidationError("You can only send offers for your own mentorships.")

        if not mentorship.is_active:
            raise serializers.ValidationError("This mentorship is inactive. You cannot send new offers.")

        if MentorshipOffer.objects.filter(mentorship=mentorship, student=student, status=EngagementLifecycleStatus.PENDING).exists():
            raise serializers.ValidationError({"detail": "You have already offered this mentorship to this student."})

        if MentorshipEngagement.objects.filter(mentorship=mentorship, student=student, status=MentorshipEngagement.EngagementStatus.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "You are already engaged in this mentorship."})

        return validated_data

    class Meta:
        model = MentorshipOffer
        exclude = ['deleted_at', 'is_deleted', 'id']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at']


class MentorshipApplicationSerializer(serializers.ModelSerializer):
    mentorship = serializers.SlugRelatedField(queryset=Mentorship.objects.all(), slug_field='sqid', write_only=True)

    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='mentorship.alumnus')

    class Meta:
        model = MentorshipApplication
        exclude = ['deleted_at', 'is_deleted', 'id', 'student']
        read_only_fields = ['sqid', 'created_at', 'status', 'responded_at', 'student_info', 'alumnus_info']

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        mentorship = validated_data['mentorship']
        student = self.context['request'].user.student_profile

        if not mentorship.is_active:
            raise serializers.ValidationError({"detail": "This mentorship is not active."})

        if MentorshipApplication.objects.filter(mentorship=mentorship, student=student).exists():
            raise serializers.ValidationError({"detail": "You have already applied for this mentorship."})

        return validated_data


class MentorshipEngagementSerializer(serializers.ModelSerializer):
    mentorship_info = MentorshipSerializer(source='mentorship', read_only=True)
    student_info = StudentInfoSerializer(read_only=True, source='student')
    alumnus_info = AlumniInfoSerializer(read_only=True, source='alumnus')

    class Meta:
        model = MentorshipEngagement
        exclude = ['deleted_at', 'is_deleted', 'id', 'mentorship', 'student', 'alumnus']
        read_only_fields = ['sqid', 'created_at']


StudentManageMentorshipOfferSerializer = make_student_manage_offer_serializer(
    MentorshipOffer, MentorshipEngagement, "mentorship"
)

AlumnusManageMentorshipOfferSerializer = make_alumnus_manage_offer_serializer(
    MentorshipOffer, "mentorship"
)

StudentManageMentorshipApplicationSerializer = make_student_manage_application_serializer(
    MentorshipApplication, MentorshipEngagement, "mentorship"
)

AlumnusManageMentorshipApplicationSerializer = make_alumnus_manage_application_serializer(
    MentorshipApplication, MentorshipEngagement, "mentorship"
)


class MentorshipEngagementFeedSerializer(serializers.ModelSerializer):
    mentorship_title = serializers.CharField(source='mentorship.title')
    mentor_name = serializers.CharField(source='alumnus.full_name')

    class Meta:
        model = MentorshipEngagement
        fields = ['sqid', 'mentorship_title', 'mentor_name', 'status']
```

- [ ] **Step 2: Verify**

```powershell
python -c "from mentorships.serializers import MentorshipSerializer, StudentManageMentorshipOfferSerializer, AlumnusManageMentorshipOfferSerializer; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add mentorships/serializers.py
git commit -m "refactor(mentorships): replace management serializers with factory calls"
```

---

### Task 16: Update `mentorships/views/applications.py`

**Files:**
- Modify: `mentorships/views/applications.py`

- [ ] **Step 1: Replace with generic view subclasses**

```python
from rest_framework import generics

from drf_spectacular.utils import extend_schema

from mentorships.models import MentorshipApplication, MentorshipEngagement
from mentorships.serializers import (
    MentorshipApplicationSerializer,
    StudentManageMentorshipApplicationSerializer,
    AlumnusManageMentorshipApplicationSerializer,
    MentorshipEngagementSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.helpers import queryset_by_role
from engagements.views import AcceptApplicationView, RejectApplicationView, WithdrawApplicationView


@extend_schema(tags=['Mentorship Applications'], summary='Apply for a mentorship (student)')
class CreateMentorshipApplicationView(generics.CreateAPIView):
    permission_classes = [IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer

    def perform_create(self, serializer):
        student = self.request.user.student_profile
        serializer.save(student=student)


@extend_schema(tags=['Mentorship Applications'], summary='List mentorship applications (alumnus and student)')
class ListMentorshipApplicationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipApplication,
            alumnus_filter={
                "mentorship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter={
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("mentorship", "student", "mentorship__alumnus"),
            order_by="-created_at",
        )


@extend_schema(tags=['Mentorship Applications'], summary='Retrieve a mentorship application by id (alumnus and student)')
class RetrieveMentorshipApplicationView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipApplicationSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipApplication,
            alumnus_filter={"mentorship__alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "mentorship__alumnus"),
        )


@extend_schema(tags=['Mentorship Applications'], summary='Accept a mentorship application (alumnus)')
class AcceptMentorshipApplicationView(AcceptApplicationView):
    application_model = MentorshipApplication
    engagement_model = MentorshipEngagement
    engagement_serializer_class = MentorshipEngagementSerializer
    validation_serializer_class = AlumnusManageMentorshipApplicationSerializer
    relation_name = "mentorship"


@extend_schema(tags=['Mentorship Applications'], summary='Reject a mentorship application (alumnus)')
class RejectMentorshipApplicationView(RejectApplicationView):
    validation_serializer_class = AlumnusManageMentorshipApplicationSerializer


@extend_schema(tags=['Mentorship Applications'], summary='Withdraw a mentorship application (student)')
class WithdrawMentorshipApplicationView(WithdrawApplicationView):
    validation_serializer_class = StudentManageMentorshipApplicationSerializer
```

- [ ] **Step 2: Verify**

```powershell
python -c "from mentorships.views.applications import AcceptMentorshipApplicationView, RejectMentorshipApplicationView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add mentorships/views/applications.py
git commit -m "refactor(mentorships): use generic views for application management"
```

---

### Task 17: Update `mentorships/views/offers.py`

**Files:**
- Modify: `mentorships/views/offers.py`

- [ ] **Step 1: Replace with generic view subclasses**

```python
from drf_spectacular.utils import extend_schema

from rest_framework import generics

from mentorships.models import MentorshipOffer, MentorshipEngagement
from mentorships.serializers import (
    MentorshipEngagementSerializer,
    MentorshipOfferSerializer,
    StudentManageMentorshipOfferSerializer,
    AlumnusManageMentorshipOfferSerializer,
)
from core.models import User

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from engagements.helpers import queryset_by_role
from engagements.views import AcceptOfferView, RejectOfferView, WithdrawOfferView


@extend_schema(tags=['Mentorship Offers'], summary='Create a mentorship offer (alumnus)')
class CreateMentorshipOfferView(generics.CreateAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus]


@extend_schema(tags=['Mentorship Offers'], summary='List mentorship offers (alumnus, student)')
class ListMentorshipOfferView(generics.ListAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipOffer,
            alumnus_filter={
                "mentorship__alumnus": self.request.user.alumni_profile,
                "status": "pending",
            },
            student_filter={
                "student": self.request.user.student_profile,
                "status": "pending",
            },
            select_related=("mentorship", "student"),
            order_by="-created_at",
        )


@extend_schema(tags=['Mentorship Offers'], summary='Retrieve a mentorship offer by id (alumnus and student)')
class RetrieveMentorshipOfferView(generics.RetrieveAPIView):
    serializer_class = MentorshipOfferSerializer
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipOffer,
            alumnus_filter={"mentorship__alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "mentorship__alumnus"),
        )


@extend_schema(tags=['Mentorship Offers'], summary='Accept a mentorship offer (student)')
class AcceptMentorshipOfferView(AcceptOfferView):
    offer_model = MentorshipOffer
    engagement_model = MentorshipEngagement
    engagement_serializer_class = MentorshipEngagementSerializer
    validation_serializer_class = StudentManageMentorshipOfferSerializer
    relation_name = "mentorship"


@extend_schema(tags=['Mentorship Offers'], summary='Reject a mentorship offer (student)')
class RejectMentorshipOfferView(RejectOfferView):
    validation_serializer_class = StudentManageMentorshipOfferSerializer


@extend_schema(tags=['Mentorship Offers'], summary='Withdraw a mentorship offer (alumnus)')
class WithdrawMentorshipOfferView(WithdrawOfferView):
    validation_serializer_class = AlumnusManageMentorshipOfferSerializer
```

- [ ] **Step 2: Verify**

```powershell
python -c "from mentorships.views.offers import AcceptMentorshipOfferView, RejectMentorshipOfferView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add mentorships/views/offers.py
git commit -m "refactor(mentorships): use generic views for offer management"
```

---

### Task 18: Update `mentorships/views/mentorships.py`

**Files:**
- Modify: `mentorships/views/mentorships.py`

- [ ] **Step 1: Use `queryset_by_role` in engagement views**

Replace the file with:

```python
from django_q.tasks import async_task

from rest_framework import generics
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from engagements.mixins import MarkEngagementCompletedMixin, MarkEngagementAcknowledgedMixin
from engagements.helpers import queryset_by_role

from mentorships.models import Mentorship, MentorshipEngagement
from mentorships.serializers import MentorshipSerializer, MentorshipStatusSerializer, MentorshipEngagementSerializer
from mentorships.lib import FocusArea, MentorshipCategory

from futaverse.permissions import IsAuthenticatedAlumnus, IsAuthenticatedStudent

from core.models import User
from feed.models import FeedEvent


@extend_schema_view(
    list=extend_schema(summary="List mentorships (alumnus)"),
    create=extend_schema(summary="Create an mentorship (alumnus)"),
)
@extend_schema(tags=['Mentorships'])
class ListCreateMentorshipView(generics.ListCreateAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]

    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')

    def perform_create(self, serializer):
        alumnus = self.request.user.alumni_profile
        mentorship = serializer.save(alumnus=alumnus)

        async_task("feed.tasks.create_feed_event_task",
            event_type=FeedEvent.EventType.MENTORSHIP_CREATED,
            related_object_id=mentorship.id,
            related_model='mentorship',
            audience=FeedEvent.Audience.STUDENT,
            data={
                'title': mentorship.title,
                'alumni': mentorship.alumnus.full_name,
                'category': mentorship.category,
                'available_slots': mentorship.available_slots,
                'remaining_slots': mentorship.remaining_slots,
                'created_at': mentorship.created_at.isoformat(),
            }
        )


@extend_schema_view(
    retrieve=extend_schema(summary="Get an mentorship by id (alumnus)"),
    update=extend_schema(summary="Update an mentorship by id (alumnus)"),
    destroy=extend_schema(summary="Delete an mentorship by id (alumnus)"),
)
@extend_schema(tags=['Mentorships'], summary='Retrieve (GET), update (PATCH) and delete (DELETE) a mentorship by id (alumnus)')
class RetrieveUpdateDestroyMentorshipView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MentorshipSerializer
    permission_classes = [IsAuthenticatedAlumnus]
    http_method_names = ['get', 'patch', 'delete']
    lookup_field = 'sqid'

    def get_queryset(self):
        user = self.request.user
        return Mentorship.objects.filter(alumnus=user.alumni_profile).select_related('alumnus')

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema(tags=['Mentorships'], summary='Toggle active status of a mentorship (alumnus)')
class ToggleMentorshipActiveView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedAlumnus]
    queryset = Mentorship.objects.all()
    serializer_class = MentorshipStatusSerializer
    http_method_names = ['patch']
    lookup_field = 'sqid'

    def perform_update(self, serializer):
        serializer.instance.toggle_active()


@extend_schema(tags=['Mentorship Engagements'], summary='List all mentorship engagements (alumnus and student)')
class ListMentorshipEngagementsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipEngagement,
            alumnus_filter={"alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "alumnus"),
        )


@extend_schema(tags=['Mentorship Engagements'], summary='Retrieve a mentorship engagement by id (alumnus and student)')
class RetrieveMentorshipEngagementView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]
    serializer_class = MentorshipEngagementSerializer
    lookup_field = 'sqid'

    def get_queryset(self):
        return queryset_by_role(
            self.request.user,
            MentorshipEngagement,
            alumnus_filter={"alumnus": self.request.user.alumni_profile},
            student_filter={"student": self.request.user.student_profile},
            select_related=("mentorship", "student", "alumnus"),
        )


@extend_schema(tags=['Mentorships'], summary='List mentorship categories and focus areas (alumnus and student)')
class MentorshipChoicesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedAlumnus | IsAuthenticatedStudent]

    def get(self, request):
        return Response({
            'categories':  [{'value': v, 'label': l} for v, l in MentorshipCategory.choices],
            'focus_areas': [{'value': v, 'label': l} for v, l in FocusArea.choices],
        })


@extend_schema(tags=['Mentorship Engagements'], summary='Mark a mentorship engagement as completed (alumnus)')
class MarkMentorshipCompletedView(MarkEngagementCompletedMixin, generics.UpdateAPIView):
    queryset = MentorshipEngagement.objects.all()
    engagement_type = 'mentorship_engagement'
    serializer_class = MentorshipEngagementSerializer


@extend_schema(tags=['Mentorship Engagements'], summary='Mark a mentorship engagement as acknowledged (student)')
class MarkMentorshipAcknowledgedView(MarkEngagementAcknowledgedMixin, generics.UpdateAPIView):
    queryset = MentorshipEngagement.objects.all()
    engagement_type = 'mentorship_engagement'
    serializer_class = MentorshipEngagementSerializer
```

- [ ] **Step 2: Verify**

```powershell
python -c "from mentorships.views.mentorships import ListCreateMentorshipView, ListMentorshipEngagementsView; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add mentorships/views/mentorships.py
git commit -m "refactor(mentorships): use queryset_by_role in engagement views"
```

---

### Task 19: Simplify `mentorships/urls.py`

**Files:**
- Modify: `mentorships/urls.py`

- [ ] **Step 1: Replace with `generate_engagement_urls`**

```python
from django.urls import path

from engagements.helpers import generate_engagement_urls

from .views.applications import (
    ListMentorshipApplicationsView,
    CreateMentorshipApplicationView,
    AcceptMentorshipApplicationView,
    RejectMentorshipApplicationView,
    WithdrawMentorshipApplicationView,
    RetrieveMentorshipApplicationView,
)

from .views.offers import (
    ListMentorshipOfferView,
    CreateMentorshipOfferView,
    AcceptMentorshipOfferView,
    RejectMentorshipOfferView,
    WithdrawMentorshipOfferView,
    RetrieveMentorshipOfferView,
)

from .views.mentorships import (
    ListCreateMentorshipView,
    ToggleMentorshipActiveView,
    RetrieveMentorshipEngagementView,
    ListMentorshipEngagementsView,
    RetrieveUpdateDestroyMentorshipView,
    MentorshipChoicesView,
    MarkMentorshipAcknowledgedView,
    MarkMentorshipCompletedView,
)

urlpatterns = generate_engagement_urls(
    prefix="mentorship",
    entity_views={
        "list_create": ListCreateMentorshipView,
        "rud": RetrieveUpdateDestroyMentorshipView,
        "toggle_active": ToggleMentorshipActiveView,
    },
    application_views={
        "create": CreateMentorshipApplicationView,
        "list": ListMentorshipApplicationsView,
        "retrieve": RetrieveMentorshipApplicationView,
        "accept": AcceptMentorshipApplicationView,
        "reject": RejectMentorshipApplicationView,
        "withdraw": WithdrawMentorshipApplicationView,
    },
    offer_views={
        "create": CreateMentorshipOfferView,
        "list": ListMentorshipOfferView,
        "retrieve": RetrieveMentorshipOfferView,
        "accept": AcceptMentorshipOfferView,
        "reject": RejectMentorshipOfferView,
        "withdraw": WithdrawMentorshipOfferView,
    },
    engagement_views={
        "list": ListMentorshipEngagementsView,
        "retrieve": RetrieveMentorshipEngagementView,
        "completed": MarkMentorshipCompletedView,
        "acknowledged": MarkMentorshipAcknowledgedView,
    },
    extra=[
        path('/choices', MentorshipChoicesView.as_view(), name='mentorship-choices'),
    ],
)
```

- [ ] **Step 2: Verify URL resolution**

```powershell
python manage.py check --deploy 2>&1 | Select-String "mentorship"
```

Expected: No errors related to mentorships URLs.

- [ ] **Step 3: Commit**

```powershell
git add mentorships/urls.py
git commit -m "refactor(mentorships): use URL generator for standard endpoints"
```

---

### Task 20: Update `mentorships/tests/`

**Files:**
- Modify: `mentorships/tests/test_serializers.py`

- [ ] **Step 1: Update import in `test_serializers.py`**

Change line 3-6 from:
```python
from mentorships.models import (
    Mentorship, MentorshipApplication, MentorshipOffer,
    MentorshipEngagement, MentorshipStatus,
)
```
To:
```python
from mentorships.models import (
    Mentorship, MentorshipApplication, MentorshipOffer,
    MentorshipEngagement,
)
from engagements.models import EngagementLifecycleStatus
```

Then replace all `MentorshipStatus.PENDING` (3 occurrences) with `EngagementLifecycleStatus.PENDING`.

- [ ] **Step 2: Run mentorship tests**

```powershell
python manage.py test mentorships
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```powershell
git add mentorships/tests/
git commit -m "refactor(mentorships): update test imports to shared lifecycle status"
```

---

## Phase 4: Final Verification

### Task 21: Run full test suite and check migrations

**Files:**
- None

- [ ] **Step 1: Run all tests**

```powershell
python manage.py test internships mentorships engagements
```

Expected: All tests pass.

- [ ] **Step 2: Verify no pending migrations**

```powershell
python manage.py makemigrations --check --dry-run
```

Expected: `No changes detected`

- [ ] **Step 3: Run Django system checks**

```powershell
python manage.py check --deploy
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit any remaining changes**

```powershell
git add -A
git commit -m "chore: final verification — tests pass, no pending migrations"
```
