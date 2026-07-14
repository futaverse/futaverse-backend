# FutaVerse Backend — Agent Instructions

## Quick Start

```powershell
cp .env.example .env          # or use existing .env
docker compose up             # starts redis, web (dev server), qcluster
# OR without Docker:
python -m venv venv; venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
# start django-q in a separate terminal:
python manage.py qcluster
```

## Key Commands

| Purpose | Command |
|---------|---------|
| Run dev server | `python manage.py runserver 0.0.0.0:8000` |
| Run migrations | `python manage.py migrate` |
| Create migrations | `python manage.py makemigrations` |
| Run qcluster worker | `python manage.py qcluster` |
| Create superuser | `python manage.py createsuperuser` |
| Run tests | `python manage.py test <app> --settings=test_settings --keepdb --parallel` |
| Shell | `python manage.py shell` |

## Style Guide

`CLAUDE.md` contains the complete DRF style guide — read it first. Key rules: no ViewSets/routers, thin views with services/selectors, all validation in `validate()`, `select_related`/`prefetch_related` always.

## Architecture

- **Project:** `futaverse/` (settings, base models, permissions, utilities)
- **10 apps:** `core`, `internships`, `mentorships`, `events`, `payments`, `feed`, `posts`, `notifications`, `engagements`, `reviews`
- **Auth:** JWT (simplejwt, 60min access, 1d refresh, rotation + blacklist), `AUTH_USER_MODEL = "core.User"`
- **Roles:** `STUDENT`, `ALUMNI`, `STAFF`, `ADMIN` — checked via `IsAuthenticatedStudent` / `IsAuthenticatedAlumnus` in `futaverse.permissions`
- **Public endpoints** use `PublicGenericAPIView` mixin from `futaverse.views`
- **IDs:** `SqidsField` (7-char min) on all models via `BaseModel` — not UUIDs, not auto-increment
- **Soft delete:** `BaseModel` provides `is_deleted`, `deleted_at`, `objects` (filters deleted), `all_objects` (unfiltered)
- **`APPEND_SLASH=False`** — URL patterns must match exactly (no trailing slash normalization)

## Key Patterns

- **Model registry:** `futaverse.lib.MODELS` maps string keys to model classes (used for cross-app lookups)
- **Engagement plugin system:** `engagements/plugins.py` maps `InternshipEngagement` / `MentorshipEngagement` to serializers + templates
- **Review plugin system:** `reviews/plugins.py` with `ENGAGEMENT_REVIEW_PLUGIN` registry for polymorphic metrics
- **Feed targeting:** objects expose `feed_targets` property → `create_feed_event_task` converts to `FeedEvent` + `FeedTarget` rows
- **Feed pagination:** cursor-based (20/page), not page-based
- **Event update locking:** cache-based lock prevents concurrent event updates
- **Google OAuth:** stored in `User.google_credentials` JSON field, refreshed automatically; raises `GoogleAuthRequired` if expired

## Task Queues

Both **django-q** and **Celery** are configured. django-q is the primary active queue:
- `python manage.py qcluster` runs the worker
- Used for: auto-acknowledge, notification sending, feed event creation, impression recording
- Celery is configured but not actively used in app code

## API Docs

- Swagger UI: `GET /`
- Redoc: `GET /api/redoc`
- Raw schema: `GET /api/raw`

## Deployment

- **Platform:** Render (web + worker services)
- **Runtime:** `python-3.11.9` (Render) / `python:3.13-slim` (Docker)
- **Start commands:** `gunicorn futaverse.wsgi:application` (web), `python manage.py qcluster` (worker)
- **DB:** PostgreSQL (Neon + Supabase connection pooling)
- **Storage:** Supabase S3 (`storages.backends.s3.S3Storage`)
- **Images:** Cloudinary for profile photos
- **Email:** Brevo SMTP relay
- **CORS:** All origins allowed, credentials enabled

## Testing

Test files exist per app but are mostly stubs (empty `TestCase` classes). No test suite is actively maintained. Running `python manage.py test` will run all of them.

**Always use SQLite for tests.** Tests must never hit the production PostgreSQL database. Always run tests with:
```
python manage.py test <app> --settings=test_settings
```
This uses the in-memory SQLite configuration in `test_settings.py` at the project root.

## Dependencies (key)

- Django 5.x, DRF, djangorestframework-simplejwt
- drf-spectacular (schema/docs), django-cors-headers
- django-sqids (SqidsField), django-soft-delete (ActiveManager)
- django-q (task queue), celery + redis
- django-eventstream (SSE), daphne (ASGI)
- boto3 (S3 storage), cloudinary, paystackapi
- sib-api-v3-sdk (Brevo email), google-auth, google-api-python-client

## Gotchas

- `.env` contains live credentials — never commit it
- `db.sqlite3` is committed to the repo (stale local DB)
- No `opencode.json` config exists
- `requirements.txt` is committed as a binary file (git LFS or similar)
