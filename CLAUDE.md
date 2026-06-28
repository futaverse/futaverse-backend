# Django REST Framework Style Guide

## Philosophy

I build production Django REST framework APIs with a **service-oriented, layer-separated architecture**. I prioritize explicit over implicit: views are small and focused, business logic lives in services, data retrieval is isolated in selectors, and validation happens in serializers. My models are thin—they hold state and computed properties but rarely contain business logic.

This is not a "best practices" guide; it's how **I** write code to keep it maintainable, testable, and sane as the codebase grows.

---

## Project & App Structure

**Directory Layout:**
```
project-backend/
├── project/                # Project settings, permissions, utilities
│   ├── models.py           # BaseModel with soft-delete + sqid (or similar)
│   ├── permissions.py      # Role-based permission classes
│   ├── views.py            # Base view classes (PublicGenericAPIView)
│   └── lib.py              # String-to-model mappings (MODELS dict)
├── core/                   # User management & authentication
├── <app_a>/                # Feature domain (internships, mentorships, etc.)
├── <app_b>/                # Feature domain
├── <service_app>/          # Cross-cutting service (notifications, payments)
└── <domain_app>/           # Domain-specific logic (reviews, ratings)
```

**App Organization:**
I keep each app consistent:
- `models.py` — Data models (inherit from BaseModel)
- `views.py` — API endpoints (inherit from generics or PublicGenericAPIView)
- `serializers.py` — Request/response validation
- `urls.py` — URL routing (path + name)
- `services.py` (when needed) — Business logic functions
- `selectors.py` (when needed) — Complex data retrieval
- `permissions.py` (when needed) — Role-based access control
- `plugins.py` (when needed) — Polymorphic behavior registry

---

## Models

**Base Class Pattern:**
```python
from project.models import BaseModel

class <Model>(BaseModel):
    # BaseModel provides:
    # - sqid (or pk alias): Encoded ID via django-sqids (or similar)
    # - is_deleted, deleted_at: Soft delete
    # - created_at: Auto timestamp
    # - objects: Manager that filters is_deleted=False
    # - all_objects: Manager returning all records
    
    class Meta:
        abstract = True  # For abstract bases only
```

**Enums (TextChoices/IntegerChoices):**
I nest enums as inner classes:
```python
class <Model>(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
    
    class Mode(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        HYBRID = 'hybrid', 'Hybrid'
        ONSITE = 'onsite', 'Onsite'
    
    status = models.CharField(choices=Status.choices, max_length=20)
    mode = models.CharField(choices=Mode.choices, max_length=20)
```

**Field Defaults & Validators:**
I use `default=` for simple values, callables for dynamic defaults:
```python
start_date = models.DateTimeField(default=timezone.now)
duration_mins = models.IntegerField(default=60, validators=[MinValueValidator(0)])
discount_percent = models.DecimalField(
    max_digits=5, decimal_places=2, default=0,
    validators=[MinValueValidator(0), MaxValueValidator(100)]
)
```

**Properties for Computed Values:**
```python
@property
def discounted_price(self):
    discount = self.discount_percent
    if discount and discount > 0:
        discount_amount = (discount / Decimal("100")) * self.price
        return self.price - discount_amount
    return self.price

@property
def is_active(self):
    return self.status == self.Status.ACTIVE
```

**State Transition Methods:**
I use explicit methods for state changes:
```python
def accept(self):
    self.status = self.Status.ACCEPTED
    self.responded_at = timezone.now()
    self.save(update_fields=['status', 'responded_at'])

def update_status(self, status):
    self.status = status
    self.save(update_fields=['status', 'updated_at'])
```

**Factory Methods (Classmethods):**
```python
@classmethod
def create_with_defaults(cls, user, **kwargs):
    """Create instance with sensible defaults"""
    defaults = {
        "is_active": True,
        "created_by": user,
    }
    defaults.update(kwargs)
    return cls.objects.create(**defaults)

@classmethod
def generate_verification_token(cls, user, expiry_minutes=10):
    """Create or replace token for a user"""
    token = generate_token()
    expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)
    instance, _ = cls.objects.update_or_create(
        user=user,
        defaults={
            "token": token,
            "expiry": expiry_time,
            "verified": False
        }
    )
    return instance
```

**__str__ Methods:**
I include context/role information:
```python
def __str__(self):
    return f"{self.name} ({self.role})"

def __str__(self):
    return f"{self.title} - {self.owner.email}"
```

**Multi-Step Validation Methods:**
I return tuples `(success: bool, message: str)`:
```python
def verify(self, token):
    if self.verified:
        return False, "Token already used"
    if self.is_expired():
        return False, "Token has expired"
    if self.token != token:
        return False, "Invalid token"
    
    self.verified = True
    self.save(update_fields=["verified"])
    return True, "Token verified successfully"
```

**RelatedName Pattern:**
I use `%(app_label)s_*` for polymorphic relationships:
```python
user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='%(app_label)s_engagements'  # becomes app_engagements
)
```

---

## Serializers

**Validation in validate() Method:**
I put all custom validation in `validate()`, never in field-level validators:
```python
class Create<Model>Serializer(serializers.Serializer):
    field_a = serializers.CharField()
    field_b = serializers.SlugField()
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate(self, attrs):
        user = self.context["request"].user
        related_object = get_object_or_404(<Model>, slug=attrs['field_b'])
        
        if related_object.status != <Model>.Status.ACTIVE:
            raise ValidationError("Related object not active.")
        
        # Store validated objects as instance attributes for use in create()
        self.user = user
        self.related_object = related_object
        
        return attrs
```

**Storing Validated State:**
I store lookups as instance attributes for use in `create/update`:
```python
def validate(self, attrs):
    # ... validation ...
    self.user = user
    self.instance_obj = instance_obj
    return validated_data
```

**Custom create() Methods:**
I handle nested object creation explicitly:
```python
def create(self, validated_data):
    related_data = validated_data.pop('related_object_data')
    image_data = related_data.pop('image', None)
    
    validated_data['owner'] = self.context['request'].user
    instance = <Model>.objects.create(**validated_data)
    
    <RelatedModel>.objects.create(parent=instance, **related_data)
    
    if image_data:
        image_data.owner = instance
        image_data.save()
    
    return instance
```

**Custom update() Methods:**
I call service functions:
```python
def update(self, instance, validated_data):
    return service_update_model(
        model_instance=instance,
        data=validated_data.get("data"),
        metadata=validated_data.get("metadata"),
    )
```

**Field Types & Relationships:**
```python
# List fields
tags = serializers.ListField(child=serializers.CharField(), required=False)

# Slug relationships (FK by field, not ID)
image = serializers.SlugRelatedField(
    queryset=Image.objects.all(),
    required=False,
    slug_field='slug'
)

# Computed fields
owner_info = OwnerDetailSerializer(source="owner", read_only=True)

# Method fields (read-only)
thumbnail_url = serializers.SerializerMethodField(read_only=True)

def get_thumbnail_url(self, obj):
    return obj.image.url if obj.image else None
```

**Excluding/Including Fields:**
I'm explicit:
```python
class Meta:
    model = <Model>
    exclude = ['owner', 'id', 'is_deleted', 'deleted_at']

# OR

class Meta:
    model = <Model>
    fields = ['slug', 'name', 'created_at', 'owner_info']
    read_only_fields = fields
```

---

## Views & ViewSets

**No ViewSets/Routers:**
I use explicit class-based views, never DRF's ViewSets + routers:
```python
# ❌ NOT MY PATTERN
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'models', <Model>ViewSet)

# ✅ MY PATTERN
path('api/models', CreateModelView.as_view(), name='create-model')
path('api/models/<slug:slug>', RetrieveModelView.as_view(), name='retrieve-model')
```

**Base Classes:**
```python
# Public endpoint (no auth required)
class PublicListView(APIView):
    permission_classes = [AllowAny]

# Authenticated endpoint
class CreateModelView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

# Role-based authenticated endpoint
class AdminView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedAdmin | IsAuthenticatedOwner]

# Public mixin (for signup, login, etc.)
from project.views import PublicGenericAPIView

class SignupView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = SignupSerializer
```

**perform_create/perform_update Pattern:**
```python
class CreateModelView(generics.CreateAPIView):
    def perform_create(self, serializer):
        self.instance = create_model_service(**serializer.validated_data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            <Model>Serializer(self.instance).data,
            status=status.HTTP_201_CREATED
        )
```

**Overriding POST/PATCH/GET Methods:**
I customize when needed:
```python
def post(self, request):
    # Pre-checks
    email = request.data.get('email')
    stale_user = User.objects.filter(email=email, is_active=False).first()
    if stale_user:
        stale_user.delete()
    
    return super().post(request)
```

**Transaction Safety:**
```python
@transaction.atomic
def perform_create(self, serializer):
    with transaction.atomic():
        instance = serializer.save()
        related = create_related_object(instance)
    
    send_email_notification(instance)

# Cleanup after successful transaction
with transaction.atomic():
    instance = serializer.save()
    transaction.on_commit(lambda: cache.delete(f"user_{instance.id}"))
```

**Response Modification:**
I reshape data before returning:
```python
def post(self, request, *args, **kwargs):
    response = super().post(request, *args, **kwargs)
    
    if response.status_code == status.HTTP_200_OK:
        # Add custom fields
        response.data["custom_field"] = compute_custom_value()
        response.data["metadata"] = {"version": "1.0"}
    
    return response
```

**get_queryset Optimization:**
I always use `select_related` or `prefetch_related`:
```python
def get_queryset(self):
    return <Model>.objects.filter(
        owner=self.request.user
    ).select_related("owner", "category").prefetch_related(
        "tags"
    ).order_by("-created_at")
```

**@extend_schema for Documentation:**
```python
@extend_schema(
    tags=["Models"],
    summary="Create a model",
    description="Create a new model with validation",
)
class CreateModelView(generics.CreateAPIView):
    ...
```

---

## URL Configuration

**Pattern:**
```python
from django.urls import path
from .views import CreateModelView, ListModelsView

urlpatterns = [
    path('/models', ListModelsView.as_view(), name='list-models'),
    path('/models/create', CreateModelView.as_view(), name='create-model'),
]
```

**Naming Convention:**
- Endpoint names use kebab-case: `create-model`, `verify-email`, `reset-password`
- Paths start with `/`
- Explicit view names for reverse lookups

**Project-Level Routing:**
I organize under `/api/` prefix:
```python
urlpatterns = [
    path('api/auth', include('auth.urls')),
    path('api/<domain>', include('<domain>.urls')),
    path('api/payments', include('payments.urls')),
]
```

---

## Services & Business Logic

**services.py Pattern:**
I keep business logic out of views and serializers. I create a `services.py` file:

```python
# <app>/services.py
from django.utils import timezone
from datetime import timedelta

def create_model(
    owner,
    name,
    related_object,
    metadata=None,
    description=""
):
    """Create a model with side effects"""
    instance = <Model>.objects.create(
        owner=owner,
        name=name,
        related=related_object,
        metadata=metadata,
        description=description,
        expires_at=timezone.now() + timedelta(days=7),
    )
    
    instance.refresh_from_db()
    recalculate_owner_stats(owner)  # Side effect
    
    return instance

def update_model(instance, metadata=None, description=None):
    """Update model and related state"""
    if description is not None:
        instance.description = description
    
    if metadata is not None:
        instance.metadata = metadata
    
    instance.save(update_fields=["description", "metadata", "updated_at"])
    
    instance.refresh_from_db()
    recalculate_owner_stats(instance.owner)
    
    return instance

def recalculate_owner_stats(owner):
    """Update owner's cached stats"""
    stats_data = <Model>.objects.filter(owner=owner).aggregate(
        total_count=Count("id"),
        avg_rating=Avg("rating")
    )
    
    profile = owner.profile
    if profile:
        profile.__class__.objects.filter(pk=profile.pk).update(
            model_count=stats_data.get("total_count", 0),
            avg_rating=stats_data.get("avg_rating")
        )
```

**Calling from Views/Serializers:**
```python
# In view
def perform_create(self, serializer):
    self.instance = create_model(**serializer.validated_data)

# In serializer
def update(self, instance, validated_data):
    return update_model(
        instance=instance,
        metadata=validated_data.get("metadata"),
        description=validated_data.get("description"),
    )
```

**Key Principles:**
- Accept all needed data as parameters (not self.instance)
- Return the updated object
- Handle side effects (cache updates, notifications, etc.)
- Use `refresh_from_db()` after creation/updates to get fresh state
- For bulk updates, use `.update()` directly on queryset (no save)

---

## Selectors & Data Retrieval

**selectors.py Pattern:**
I isolate complex queries:

```python
# <app>/selectors.py
from rest_framework.exceptions import NotFound

def get_model(model_id):
    """Get a single model by ID. Raise NotFound if missing."""
    try:
        return <Model>.objects.get(pk=model_id)
    except <Model>.DoesNotExist:
        raise NotFound("Model not found.")

def get_model_for_owner(model_slug, owner):
    """Get a model for a specific owner. Return None if not found."""
    try:
        return <Model>.objects.get(slug=model_slug, owner=owner)
    except <Model>.DoesNotExist:
        return None

def list_models_with_filters(owner, status=None, limit=None):
    """List models with optional filters"""
    qs = <Model>.objects.filter(owner=owner)
    
    if status:
        qs = qs.filter(status=status)
    
    qs = qs.select_related("owner", "category")
    
    if limit:
        qs = qs[:limit]
    
    return qs
```

**Patterns:**
- Raise `NotFound` for object retrieval errors
- Return `None` for optional lookups
- Include query optimizations (`select_related`, `prefetch_related`)
- One function per query pattern

---

## Error Handling & Responses

**Validation Errors:**
I raise `ValidationError` in serializers:
```python
if instance.status != <Model>.Status.ACTIVE:
    raise ValidationError("Model is not active.")

if owner == modifier:
    raise serializers.ValidationError("You cannot modify your own model.")
```

**Not Found Errors:**
I use `get_object_or_404` in validation or selectors:
```python
def validate(self, attrs):
    model = get_object_or_404(<Model>, slug=attrs['slug'])
    # or
    model_class = MODELS.get(model_type)
    model = get_object_or_404(model_class, slug=attrs['slug'])
```

**HTTP Response Format:**
I use consistent response structures:
```python
# Success
Response(
    {"detail": "Action completed successfully"},
    status=status.HTTP_200_OK
)

# Or with data
Response(
    {
        "data": {"token": str(token)},
        "detail": "Authentication successful",
        "status": "success"
    },
    status=status.HTTP_200_OK
)

# Error
Response(
    {"detail": message, "status": "error"},
    status=status.HTTP_400_BAD_REQUEST
)
```

**External Service Errors:**
```python
try:
    data = fetch_from_external_service()
    cache.set(cache_key, data, 86400)
except Exception as e:
    return Response(
        {"error": "Failed to fetch data from external service"},
        status=status.HTTP_502_BAD_GATEWAY
    )
```

---

## Permissions & Access Control

**Role-Based Permission Classes:**
```python
# project/permissions.py
class IsAuthenticatedOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.OWNER

class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.USER
```

**Using Permissions:**
```python
# Single permission
permission_classes = [IsAuthenticated]

# OR permission
permission_classes = [IsAuthenticatedOwner | IsAuthenticatedUser]
```

**Object-Level Permissions:**
```python
class IsModelOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner
```

**Set via UpdateAPIView:**
```python
class UpdateModelView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedOwner | IsAuthenticatedAdmin]
    lookup_field = "slug"
```

---

## Plugin/Registry Pattern

I use this for polymorphic behavior (different types of models, metrics, etc.):

```python
# <app>/plugins.py
class BaseModelPlugin:
    metrics_serializer = None
    
    def compute_aggregate(self, metrics: dict) -> Decimal:
        if not metrics:
            return Decimal("0.00")
        values = [Decimal(str(v)) for v in metrics.values()]
        return (sum(values) / len(values)).quantize(Decimal("0.01"))

class OwnerRatesUserPlugin(BaseModelPlugin):
    metrics_serializer = OwnerRatesUserMetricsSerializer

class UserRatesOwnerPlugin(BaseModelPlugin):
    metrics_serializer = UserRatesOwnerMetricsSerializer

class ModelType:
    OWNER_RATES_USER = "owner_rates_user"
    USER_RATES_OWNER = "user_rates_owner"

MODEL_PLUGIN_REGISTRY = {
    ModelType.OWNER_RATES_USER: OwnerRatesUserPlugin(),
    ModelType.USER_RATES_OWNER: UserRatesOwnerPlugin(),
}
```

**Usage in Serializers:**
```python
plugin = MODEL_PLUGIN_REGISTRY.get(model_type)
metrics_serializer = plugin.metrics_serializer(data=metrics)
metrics_serializer.is_valid(raise_exception=True)
validated_metrics = metrics_serializer.validated_data
aggregate = plugin.compute_aggregate(validated_metrics)
```

---

## Async & Background Tasks

I use `django-q` for task scheduling:

```python
# <app>/tasks.py
from django_q.tasks import async_task, schedule, Schedule
from django.utils import timezone
from datetime import timedelta

def auto_complete_model(model_slug, model_type):
    model = MODELS.get(model_type).objects.get(slug=model_slug)
    
    model.update_status(<Model>.Status.COMPLETED)
    
    async_task(
        "notifications.tasks.send_notification",
        user_ids=[model.owner.id],
        title='Model Auto-Completed',
        content=f'Your model has been auto-completed.'
    )

def schedule_model_workflow(model_data):
    slug = model_data.get("slug")
    model_type = model_data.get("model_type")
    
    # Immediate async task
    async_task(
        "notifications.tasks.send_notification",
        user_ids=[owner_id],
        title='Model Status Changed',
        content=f'Your model status has changed.'
    )
    
    # Schedule for future
    schedule(
        "<app>.tasks.auto_complete_model",
        model_slug=slug,
        model_type=model_type,
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(seconds=40),
        name=f'auto_complete_{slug}'
    )
```

---

## Querysets & ORM Usage

**Always Optimize Queries:**
```python
# In get_queryset()
def get_queryset(self):
    return <Model>.objects.filter(
        owner=self.request.user
    ).select_related("owner", "category").prefetch_related(
        "tags"
    ).order_by("-created_at")

# For multiple related objects
.select_related("user", "profile", "settings")

# For reverse relations
.prefetch_related("comments", "likes")
```

**Aggregation:**
```python
stats = <Model>.objects.filter(owner=owner).aggregate(
    total_count=Count("id"),
    avg_rating=Avg("rating"),
    max_views=Max("view_count")
)
```

**Bulk Updates:**
I use `.update()` on queryset instead of loop + save:
```python
profile.__class__.objects.filter(pk=profile.pk).update(
    avg_rating=avg_rating,
    total_models=total_count
)
```

**Filtering in Validation:**
```python
existing = <Model>.objects.filter(
    owner=owner,
    related=related_obj,
    status=<Model>.Status.ACTIVE
).exists()

if existing:
    raise ValidationError({"detail": "You already have an active model for this."})
```

---

## Naming Conventions

**Models:**
- PascalCase: `User`, `UserProfile`, `ModelApplication`
- Generic models get descriptive suffixes: `*Profile`, `*Application`, `*Engagement`

**Model Fields:**
- snake_case: `first_name`, `phone_number`, `created_at`
- Use `_at` for timestamps: `created_at`, `updated_at`, `responded_at`, `deleted_at`
- Use `_id` for raw ForeignKey: `user_id` (but prefer relation name: `user`)
- Boolean fields start with `is_`: `is_active`, `is_deleted`, `is_paid`, `is_verified`

**View Classes:**
- PascalCase ending in `View`: `CreateUserView`, `ListModelsView`, `UpdateModelView`
- Descriptive names: `CreateModelView` (not `ModelCreateView`)

**URL Endpoint Names:**
- kebab-case: `create-model`, `verify-email`, `list-models`, `update-model`
- Match pattern to intent

**Functions/Methods:**
- snake_case: `create_model()`, `get_model()`, `recalculate_stats()`
- Verb-first for services: `create_*`, `update_*`, `delete_*`
- Verb-first for selectors: `get_*`, `list_*`, `count_*`

**Private/Internal:**
- Prefix with `_`: `_process_data()` (for methods not part of public API)
- No prefix for "public" methods (called from outside the module)

**Constants:**
- UPPER_SNAKE_CASE: `MODELS`, `PLUGIN_REGISTRY`, `DEFAULT_TIMEOUT`

**Cache Keys:**
- Use `_` separators with domain: `user_profile_123`, `pending_token_{user_id}`

---

## Import Style

**Order (PEP 8):**
```python
# 1. Standard library
from datetime import timedelta
from decimal import Decimal
import uuid

# 2. Third-party (Django, DRF, etc.)
from django.db import models, transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError, NotFound

# 3. Local/project
from core.models import User, UserProfile
from project.models import BaseModel
from project.permissions import IsAuthenticated
from project.lib import MODELS
from <app>.models import <Model>
from <app>.services import create_model
```

**Imports in Views:**
```python
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import <Model>
from .serializers import <Model>Serializer, Create<Model>Serializer
from .services import create_model
from project.permissions import IsAuthenticatedOwner
```

**Never:**
- `from . import *` (implicit imports)
- Circular imports (structure to avoid them)
- Late imports unless necessary (performance reasons)

---

## What I Never Do (Anti-patterns)

1. **No ViewSets/Routers**
   - ❌ `ViewSet` + `DefaultRouter`
   - ✅ Explicit `View` classes with `path()`

2. **No Generic Serializer Fields**
   - ❌ `serializers.CharField()` for everything
   - ✅ `SlugRelatedField`, `SerializerMethodField`, explicit relationships

3. **No Fat Views**
   - ❌ Business logic in `perform_create`
   - ✅ Service functions for logic, views only orchestrate

4. **No N+1 Queries**
   - ❌ `<Model>.objects.all()` without select_related
   - ✅ Always include `select_related`, `prefetch_related` in get_queryset

5. **Limited Signals**
   - ❌ Using signals for business logic
   - ✅ Explicit service calls, signals only for truly decoupled events

6. **No Field-Level Validation**
   - ❌ `CharField(min_length=8)` for password validation
   - ✅ All validation in serializer's `validate()` method

7. **No Magic Strings**
   - ❌ Hardcoded model types
   - ✅ Use `MODELS` dict, type constants, nested enums

8. **No Response Data Guessing**
   - ❌ Inconsistent response structure across endpoints
   - ✅ Explicit Response() with status code

9. **No Bare Exception Handling**
   - ❌ `except Exception:`
   - ✅ Catch specific exceptions: `<Model>.DoesNotExist`, `ValidationError`

10. **No Comment Spam**
    - ❌ Over-commenting obvious code
    - ✅ Comments only for non-obvious WHY (constraints, workarounds)

---

## Reference Snippets

### Snippet 1: Complete Model with Properties & Methods
```python
class <Model>(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='models')
    related = models.ForeignKey(<RelatedModel>, on_delete=models.CASCADE, related_name='related_models')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        choices=<Status>.choices,
        max_length=20,
        default=<Status>.PENDING
    )
    
    responded_at = models.DateTimeField(auto_now=True)

    def withdraw(self):
        self.status = <Status>.WITHDRAWN
        self.save(update_fields=['status'])
      
    def accept(self):
        self.status = <Status>.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

    def __str__(self):
        return f"{self.name} by {self.owner.email}"
```

### Snippet 2: Serializer with Complex Validation
```python
class Create<Model>Serializer(serializers.Serializer):
    model_type = serializers.ChoiceField(choices=['type_a', 'type_b'])
    related_slug = serializers.SlugField()
    metadata = serializers.JSONField(required=False, default=dict)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        user = self.context["request"].user
        model_type = attrs.pop('model_type')
        related_slug = attrs.pop('related_slug')
        
        model_class = MODELS.get(model_type)
        related = get_object_or_404(model_class, slug=related_slug)
        
        if related.status != <Model>.Status.ACTIVE:
            raise ValidationError("Related model is not active.")
        
        if user == related.owner:
            raise ValidationError("You cannot interact with your own model.")
        
        plugin = MODEL_PLUGIN_REGISTRY.get(model_type)
        metadata = attrs.get("metadata", {})
        metrics_serializer = plugin.metrics_serializer(data=metadata)
        metrics_serializer.is_valid(raise_exception=True)
        
        validated_data = super().validate(attrs)
        validated_data["metadata"] = metrics_serializer.validated_data
        validated_data["user"] = user
        validated_data["related"] = related
        
        return validated_data
```

### Snippet 3: Service Function with Side Effects
```python
def create_model(
    user,
    related_model,
    name,
    metadata=None,
    description=""
):
    instance = <Model>.objects.create(
        owner=user,
        related=related_model,
        name=name,
        metadata=metadata,
        description=description,
        expires_at=timezone.now() + timedelta(days=7),
    )

    instance.refresh_from_db()
    recalculate_user_stats(user)  # Side effect: update user stats

    return instance
```

### Snippet 4: View with Transaction & Response Reshaping
```python
@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Send notification
        send_notification(
            subject="New Login",
            body="There was a login attempt on your account.",
            recipient=request.data.get("email"),
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Set secure cookie
            set_refresh_cookie(response)
            
            # Reshape response data
            user = User.objects.get(email=request.data.get("email"))
            response.data["data"]["role"] = user.role
            response.data["data"]["user_id"] = user.id
            response.data["data"]["profile_slug"] = user.profile.slug
        
        return response
```

### Snippet 5: Optimized get_queryset
```python
@extend_schema(tags=["Models"], summary="List models for a user")
class ListUserModelsView(generics.ListAPIView):
    serializer_class = <Model>Serializer
    permission_classes = [IsAuthenticatedOwner | IsAuthenticatedUser]
    
    def get_queryset(self):
        user_slug = self.kwargs.get("slug")
        user_role = self.request.query_params.get("role")
        
        if not user_role or user_role not in [User.Role.OWNER, User.Role.USER]:
            raise ValidationError({"detail": "Role parameter required."})
        
        user_profile = get_object_or_404(UserProfile, slug=user_slug)
        
        return <Model>.objects.filter(
            owner=user_profile.user
        ).select_related("owner", "related").prefetch_related(
            "tags"
        ).order_by("-created_at")
```

---

## When to Break These Rules

Every style guide needs escape hatches. I break these patterns when:

**When ViewSets make sense:**
- Building a simple CRUD API where endpoints have minimal customization
- The project is small and doesn't need to grow much
- Team velocity matters more than explicitness (though this is rare)

**When signals are the right tool:**
- Truly decoupled apps that shouldn't import each other (e.g., logging, analytics)
- The logic should fire regardless of how the model is created (API, admin, management command)
- Multiple apps react independently to the same event

**When to put validation in fields:**
- Simple format validation that's reusable across serializers (e.g., URL validation)
- The rule is truly about the field itself, not business logic

**When to combine services:**
- Very simple operations that don't warrant a separate function
- Small projects where the overhead isn't justified
- Helper utilities that are just data transformations

**When soft deletes don't fit:**
- Compliance/regulatory: must actually delete (GDPR, healthcare)
- Performance-critical queries where soft deletes add complexity
- No audit trail needed

**When to use ViewSets + Routers after all:**
- Late in a large, stable project where endpoints are truly standard
- When the codebase is read-only or rarely changes

The principle: **understand the rule before you break it.** If you can't articulate why the general pattern is wrong for your case, follow the pattern.

---

## Key Mental Models

**Service Layer Design:**
Services take fully-qualified data and return domain objects. They're the business logic layer. Views/serializers orchestrate; services execute.

**Explicit Over Implicit:**
I'd rather write 10 lines of obvious code than 2 lines of clever code. Surprises are bugs waiting to happen.

**Querysets are free:**
Optimizing a queryset costs nothing but saves everything. Always `select_related` your foreign keys.

**Side effects are real:**
Services handle them (cache invalidation, notifications, stats recalculation). Views should never know about them—that's the service's contract.

**Validation is a serializer's job:**
By the time a service is called, the data is clean. No defensive programming in services.

**Names are contracts:**
`get_model()` returns a model or raises NotFound. `list_models()` returns a queryset. Breaking that contract is a bug.
