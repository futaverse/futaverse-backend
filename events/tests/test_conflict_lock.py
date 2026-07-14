from rest_framework import status

from futaverse.tests_helpers import BaseAPITestCase
from events.models import Event


class ConflictErrorClassTests(BaseAPITestCase):
    def test_conflict_error_class_exists(self):
        from events.views import ConflictError
        self.assertTrue(issubclass(ConflictError, Exception))

    def test_conflict_error_has_409_status(self):
        from events.views import ConflictError
        err = ConflictError({"detail": "test"})
        self.assertEqual(err.status_code, 409)


class EventUpdateConflictTests(BaseAPITestCase):
    """Locks in B7: UpdateEventView must raise ConflictError on cache lock."""

    def setUp(self):
        self.alumnus = self._create_alumnus("alum@test.com")
        self.event = Event.objects.create(
            creator=self.alumnus,
            title="Test Event",
            description="d",
            category="workshop",
            mode="physical",
            date="2026-06-01",
            start_time="10:00:00",
            duration_mins=60,
        )

    def test_concurrent_update_returns_409(self):
        from django.core.cache import cache
        cache.set(f"info_update_{self.event.sqid}", True, timeout=5)

        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(
            f"/api/events/update/{self.event.sqid}",
            {"title": "New Title"},
            **headers,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        cache.delete(f"info_update_{self.event.sqid}")

    def test_concurrent_mode_update_returns_409(self):
        from django.core.cache import cache
        cache.set(f"mode_update_{self.event.sqid}", True, timeout=10)

        headers = self._auth_header(self.alumnus)
        resp = self.client.patch(
            f"/api/events/update/{self.event.sqid}/mode",
            {"mode": "virtual", "platform": "jitsi"},
            **headers,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        cache.delete(f"mode_update_{self.event.sqid}")
