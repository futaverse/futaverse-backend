# Further Discussion Items

Items from the tightening pass that need design discussion before implementation.

---

## 1. Sentry / Observability

No observability story yet. Logger hooks are clean and ready for `sentry_sdk.init()`. The four silent-failure paths (auto-acknowledge, feed event creation, impressions, notifications) need Sentry or structured logging.

## 2. Rate Limiting on Public Auth Endpoints

`signup`, `login`, `verify OTP`, `forgot password` are public and have no DRF throttle classes. Vulnerable to credential-stuffing and OTP brute-force bots. Add `AnonRateThrottle` or `ScopedRateThrottle` for the auth scope.

## 3. Test Coverage Gaps

- **payments**, **feed**, **notifications**, **reviews** have zero test files
- Payment webhook idempotency and HMAC validation are untested
- Engagement lifecycle race conditions (manual ack vs auto-ack) are untested

Other apps have tests but the "no test suite is actively maintained" note in AGENTS.md means we should verify they actually pass after the import fix.

## 4. Resume Storage Paths

Two separate resume paths exist:
- `StudentResume` (1:1 to `StudentProfile`) — in `core/models.py`
- `ApplicationResume` (1:1 to `InternshipApplication`) — in `internships/models.py`

This is intentional (general profile resume vs per-application resume) but the upload logic is duplicated. Worth considering a shared upload service.

## 5. Slotted Engagement Types

Both `Internship` and `Mentorship` have `available_slots` / `remaining_slots` / `decrement_remaining_slots()`. The slot logic is duplicated. Consider extracting to a `SlottedMixin` in the engagements abstraction layer.

## 6. Unwired `MentorshipRequest`

`MentorshipRequest` model exists in `mentorships/models.py` but has no views, serializers, or URL routes. The REQUEST source type on `MentorshipEngagement` acknowledges its existence, but it's not implemented.

## 7. `User.role` STAFF / ADMIN

The `STAFF` and `ADMIN` enum values exist on `User.Role` but no permission classes use them. Either wire them up with admin views or remove the enum values to avoid confusion.

## 8. CORS Restriction

`CORS_ALLOW_ALL_ORIGINS = True` + `CORS_ALLOW_CREDENTIALS = True` is permissive. A known-origins list is commented out in `settings.py:166-174`. Restrict before going to production.
