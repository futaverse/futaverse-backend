# Internship & Mentorship Deduplication — Design Spec

**Date:** 2026-07-11
**Status:** Approved
**Scope:** `internships/`, `mentorships/`, `engagements/`

## Problem

The `internships` and `mentorships` apps share ~350 lines of near-duplicate code (~30% of combined total). Both implement identical workflows (Application/Offer → Engagement → Complete → Acknowledge) with copied models, serializers, views, and URL patterns that differ only in naming.

## Constraints

- Keep business logic and domain-specific fields inside each app
- Do not create a new "middle ground" app; extend the existing `engagements/` shared layer
- No ViewSets/routers (project convention)
- No `APPEND_SLASH` normalization (project convention)
- Maintain backward compatibility — all existing endpoints, response shapes, and permissions must stay identical

## Solution

Extend `engagements/` with abstract base models, generic view classes, serializer factories, and helper utilities. Each app's concrete classes inherit/instantiate from these with class-level configuration.

---

## 1. Shared Models (`engagements/models.py` additions)

### 1.1 `EngagementLifecycleStatus` enum

Replaces the two identical `InternshipStatus` and `MentorshipStatus` enums.

```python
class EngagementLifecycleStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"
```

### 1.2 `BaseApplication` abstract model

```python
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
```

### 1.3 `BaseOffer` abstract model

```python
class BaseOffer(BaseModel):
    status = models.CharField(
        choices=EngagementLifecycleStatus.choices,
        max_length=20,
        default=EngagementLifecycleStatus.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def accept(self): ...  # identical to BaseApplication.accept
    def reject(self): ...  # identical
    def withdraw(self): ...  # identical
```

Note: `updated_at` is NOT on `BaseOffer` — only `InternshipOffer` has it. Each concrete model adds `updated_at` if needed. `MentorshipRequest` also has its own `updated_at`.

### 1.4 App model changes

**`internships/models.py`:**
- Remove `InternshipStatus`
- `InternshipApplication`: inherit `BaseApplication`, add `internship` FK, `student` FK. `cover_letter` inherited (nullable — correct).
- `InternshipOffer`: inherit `BaseOffer`, add `internship` FK, `student` FK. Keep `updated_at`.
- `InternshipEngagement`: inherit `BaseEngagement` (unchanged). Source choices stay.

**`mentorships/models.py`:**
- Remove `MentorshipStatus`
- `MentorshipApplication`: inherit `BaseApplication`, add `mentorship` FK, `student` FK. Override `cover_letter` to `TextField()` (non-nullable).
- `MentorshipOffer`: inherit `BaseOffer`, add `mentorship` FK, `student` FK.
- `MentorshipRequest`: inherit `BaseOffer`, add `mentor` FK, `student` FK, `message` field, `updated_at`.
- `MentorshipEngagement`: inherit `BaseEngagement` (unchanged). Source choices — add `REQUEST`.

**`Internship` and `Mentorship` themselves:** Unchanged. Their fields are genuinely domain-specific.

Terminology note: "Application" and "Offer" in the abstract base refer to their role in the engagement lifecycle, not their domain (internship/mentorship). This is intentional — the parent FK field name differs per domain (`internship` vs `mentorship`).

### 1.5 ForeignKey `related_name` conventions

No changes needed to existing `related_name` values (`internship_applications`, `mentorship_applications`, etc.). The abstract base does not define parent or student FKs — each concrete model adds its own.

### 1.6 `InternshipStatus` / `MentorshipStatus` in existing code

Imports across the codebase (serializers, views, tasks, plugins, feed, reviews, admin) reference `InternshipStatus` and `MentorshipStatus`. These must be updated to `EngagementLifecycleStatus` from `engagements.models`. A `sed`-friendly rename: replace all occurrences.

---

## 2. Serializer Factories (`engagements/serializers.py` — new file)

Four factory functions that generate management serializers. Parameterized by model class, engagement model, and relation name.

### 2.1 `make_student_manage_offer_serializer`

For student accept/reject of offers. Validates:
- Offer ID required
- Student is the intended recipient
- Offer is PENDING
- Parent entity is active
- Student is not already engaged

### 2.2 `make_alumnus_manage_offer_serializer`

For alumnus withdraw of offers. Validates:
- Alumnus owns the parent entity
- Offer is PENDING
- Parent entity is active

### 2.3 `make_student_manage_application_serializer`

For student withdraw of applications. Validates:
- Student owns the application
- Application is PENDING
- Parent entity is active
- Student is not already engaged

### 2.4 `make_alumnus_manage_application_serializer`

For alumnus accept/reject of applications. Validates:
- Alumnus owns the parent entity
- Application is PENDING
- Parent entity is active
- Student is not already engaged

### Usage in each app

```python
# internships/serializers.py
from engagements.serializers import (
    make_student_manage_offer_serializer,
    make_alumnus_manage_offer_serializer,
    make_student_manage_application_serializer,
    make_alumnus_manage_application_serializer,
)

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
```

Same pattern in `mentorships/serializers.py` with `"mentorship"`.

### Seriazlier that stay in each app

The following stay because their fields/validation differ enough:
- `InternshipSerializer` / `MentorshipSerializer`
- `InternshipStatusSerializer` / `MentorshipStatusSerializer`
- `InternshipApplicationSerializer` / `MentorshipApplicationSerializer`
- `InternshipOfferSerializer` / `MentorshipOfferSerializer`
- `InternshipEngagementSerializer` / `MentorshipEngagementSerializer`
- `ApplicationResumeSerializer`
- `InternshipEngagementFeedSerializer` / `MentorshipEngagementFeedSerializer`

---

## 3. Generic Views (`engagements/views.py` additions)

Six concrete generic view classes. Each is a DRF `APIView` subclass configurable via class attributes.

### 3.1 View catalog

| Class | Permission | Method | Action |
|---|---|---|---|
| `AcceptApplicationView` | `IsAuthenticatedAlumnus` | POST | Creates engagement, calls `accept()`, decrements slots |
| `RejectApplicationView` | `IsAuthenticatedAlumnus` | POST | Calls `reject()` |
| `WithdrawApplicationView` | `IsAuthenticatedStudent` | POST | Calls `withdraw()` |
| `AcceptOfferView` | `IsAuthenticatedStudent` | POST | Creates engagement, calls `accept()`, decrements slots |
| `RejectOfferView` | `IsAuthenticatedStudent` | POST | Calls `reject()` |
| `WithdrawOfferView` | `IsAuthenticatedAlumnus` | POST | Calls `withdraw()` |

### 3.2 Class configuration

Each generic view expects these class attributes:

```python
class AcceptApplicationView(APIView):
    application_model = None       # e.g., InternshipApplication
    engagement_model = None        # e.g., InternshipEngagement
    engagement_serializer_class = None
    validation_serializer_class = None
    relation_name = None           # "internship" or "mentorship"
```

`relation_name` is used to:
- Resolve the parent FK: `getattr(application, self.relation_name)` → `application.internship` or `application.mentorship`
- Create the engagement FK: `{self.relation_name: parent_entity}`

### 3.3 App view changes

Each app's views become thin subclasses:

```python
# internships/views/applications.py
class AcceptInternshipApplicationView(AcceptApplicationView):
    application_model = InternshipApplication
    engagement_model = InternshipEngagement
    engagement_serializer_class = InternshipEngagementSerializer
    validation_serializer_class = AlumnusManageInternshipApplicationSerializer
    relation_name = "internship"
```

The following views stay in their apps (domain-specific logic):
- `ListCreateInternshipView` / `ListCreateMentorshipView` — `perform_create` builds different feed data
- `RetrieveUpdateDestroyInternshipView` / `RetrieveUpdateDestroyMentorshipView` — minimal boilerplate
- `ToggleInternshipActiveView` / `ToggleMentorshipActiveView` — trivial
- `ListInternshipApplicationsView` / `ListMentorshipApplicationsView` — different `select_related` paths
- `RetrieveInternshipApplicationView` / `RetrieveMentorshipApplicationView` — same
- `CreateInternshipApplicationView` / `CreateMentorshipApplicationView` — domain-specific validation
- `ListInternshipOfferView` / `ListMentorshipOfferView` — different `select_related` paths
- `RetrieveInternshipOfferView` / `RetrieveMentorshipOfferView` — same
- `CreateInternshipOfferView` / `CreateMentorshipOfferView` — domain-specific validation
- `ListInternshipEngagementsView` / `ListMentorshipEngagementsView` — different `select_related` paths
- `RetrieveInternshipEngagementView` / `RetrieveMentorshipEngagementView` — same
- `MarkInternshipCompletedView` / `MarkMentorshipCompletedView` — already uses shared mixin
- `MarkInternshipAcknowledgedView` / `MarkMentorshipAcknowledgedView` — already uses shared mixin

Unique views staying:
- `UploadApplicationResumeView` (internships)
- `MentorshipChoicesView` (mentorships)

---

## 4. Queryset Helper (`engagements/helpers.py` — new file)

```python
def queryset_by_role(user, model_class, *, alumnus_filter, student_filter,
                     select_related=(), order_by=None):
    """
    Returns a role-scoped queryset.

    alumnus_filter: dict of filter kwargs for ALUMNI role
    student_filter: dict of filter kwargs for STUDENT role
    """
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
```

Used by the List/Retrieve views that stay in each app to reduce the `if/elif/else` repetition.

---

## 5. URL Helper (`engagements/helpers.py`)

```python
def generate_engagement_urls(*, prefix, entity_patterns, application_patterns,
                              offer_patterns, engagement_patterns, extra=None):
    """Returns a list of path() objects following the standard URL structure."""
```

Cuts each app's `urls.py` from ~35 lines to ~15 lines of declarative configuration.

---

## 6. What Does NOT Change

- All existing URL paths, HTTP methods, and response shapes
- All permissions (same class, same behavior)
- `feed_targets` and `post_context` properties
- `perform_create` in ListCreate views (feed event data is domain-specific)
- `EngagementLifecycleStatus` replaces the two status enums but the values are identical — no data migration needed, only code migration
- `InternshipEngagement` and `MentorshipEngagement` models
- `ApplicationResume` model
- `MentorshipRequest` model (reuses `BaseOffer` for lifecycle methods only)
- `engagements/plugins.py` — already well-structured, just update status enum import
- Review plugin system

---

## 7. Migration Strategy

1. Create abstract models in `engagements/` — no migration (abstract)
2. Run `makemigrations` for `internships` and `mentorships` — Django detects parent class change, creates migration step that adds base fields (already exist, should be `AlterField` only)
3. **Verify migration output is safe** — no `AddField` operations for columns that already exist, no `DeleteField` operations. If Django generates anything other than `AlterField`, manually adjust the migration file.
4. Update all imports across both apps + plugins + test files
5. Run `python manage.py migrate` in Docker to verify

`db.sqlite3` is committed to the repo (stale). Test migration on a fresh DB in Docker.

---

## 8. Files Touched

| File | Change |
|---|---|
| `engagements/models.py` | Add `EngagementLifecycleStatus`, `BaseApplication`, `BaseOffer` |
| `engagements/serializers.py` | **New** — 4 factory functions |
| `engagements/views.py` | **New** (or append to existing) — 6 generic view classes |
| `engagements/helpers.py` | **New** — `queryset_by_role`, `generate_engagement_urls` |
| `internships/models.py` | Remove `InternshipStatus`; `InternshipApplication` / `InternshipOffer` inherit abstract bases |
| `internships/serializers.py` | Replace 4 management serializers with factory calls; update status import |
| `internships/views/applications.py` | Replace `Accept/Reject/Withdraw` views with subclass declarations |
| `internships/views/offers.py` | Replace `Accept/Reject/Withdraw` views with subclass declarations |
| `internships/views/internships.py` | Update status import; use `queryset_by_role` in list views |
| `internships/tests/` | Update `InternshipStatus` references to `EngagementLifecycleStatus` |
| `internships/mixins.py` | **Delete** — `OfferValidationMixin` and `ApplicationValidationMixin` replaced by factory serializers |
| `internships/urls.py` | Simplify with `generate_engagement_urls` |
| `mentorships/models.py` | Remove `MentorshipStatus`; `MentorshipApplication` / `MentorshipOffer` / `MentorshipRequest` inherit bases |
| `mentorships/serializers.py` | Same pattern as internships |
| `mentorships/views/applications.py` | Same pattern |
| `mentorships/views/offers.py` | Same pattern |
| `mentorships/views/mentorships.py` | Update status import; use `queryset_by_role` |
| `mentorships/tests/` | Update `MentorshipStatus` references to `EngagementLifecycleStatus` |
| `mentorships/urls.py` | Simplify with `generate_engagement_urls` |
| `engagements/plugins.py` | Update status enum import |
