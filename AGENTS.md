# FutaVerse Backend — Agent Instructions

## Quick Start

```powershell
cp .env.example .env          # no .env.example exists — copy from an existing .env instead
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
| Run tests | `python manage.py test <app> --settings=test_settings` (no `--parallel` on Windows — crashes) |
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

Only **django-q** is configured (django-q2, `Q_CLUSTER` in settings, ORM broker). Celery is **not** installed:
- `python manage.py qcluster` runs the worker
- Used for: auto-acknowledge, notification sending, feed event creation, impression recording
- `ENVIRONMENT` (development/staging/production) switches auto-ack delays and DEBUG/SSL behavior

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

Each app has a test package (`<app>/tests/`, built on `futaverse/tests_helpers.py:BaseAPITestCase`). Several apps also carry stub top-level `tests.py` files — an app must not have both `tests.py` and a `tests/` package or test discovery crashes. **Baseline status: ~100 of 183 tests fail — do not assume green.**

**Always use SQLite for tests.** Tests must never hit the production PostgreSQL database. Always run tests with:
```
python manage.py test <app> --settings=test_settings
```
This uses the SQLite file `test_db.sqlite3` defined in `test_settings.py` at the project root (file-based, not in-memory).

## Dependencies (key)

- Django 5.x, DRF, djangorestframework-simplejwt
- drf-spectacular (schema/docs), django-cors-headers
- django-sqids (SqidsField); soft delete is a hand-rolled `ActiveManager` in `futaverse/models.py` (no django-soft-delete package)
- django-q (task queue); redis (cache + eventstream)
- django-eventstream (SSE), daphne (ASGI)
- boto3 (S3 storage), cloudinary, paystackapi
- sib-api-v3-sdk (Brevo email), google-auth, google-api-python-client

## Gotchas

- `.env` contains live credentials — never commit it
- `db.sqlite3` is committed to the repo (stale local DB)
- No `opencode.json` config exists
- `requirements.txt` is committed as a normal text file (no LFS) — claims of binary tracking are wrong
- `ENVIRONMENT` must be set to `production` on Render (render.yaml) — `development` is the local default
- Apps with a top-level `tests.py` stub AND a `tests/` package break `manage.py test` discovery — keep exactly one


## Instructions
- Never write a spectacular extend_schema to use inline response and request schemas whenever there is a need to add a manual request/response shape. Always use a serializer where possible. The serializer records the shape of the response/request.