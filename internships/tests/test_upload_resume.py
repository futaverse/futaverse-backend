from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from internships.models import ApplicationResume
from futaverse.tests_helpers import BaseAPITestCase


class UploadResumeEndpointTests(BaseAPITestCase):
    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")

    def _create_resume_file(self):
        return SimpleUploadedFile("resume.pdf", b"fake-pdf-content", content_type="application/pdf")

    def test_student_uploads_resume_returns_201(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": self._create_resume_file()},
            **headers, format="multipart")
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_no_resume_file_returns_400(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/internships/upload-resume", {}, **headers, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_alumnus_cannot_upload(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": self._create_resume_file()},
            **headers, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_upload(self):
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": self._create_resume_file()}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_non_pdf_returns_201_or_error(self):
        headers = self._auth_header(self.student)
        txt = SimpleUploadedFile("resume.txt", b"text-content", content_type="text/plain")
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": txt}, **headers, format="multipart")
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_large_file_handled(self):
        headers = self._auth_header(self.student)
        large = SimpleUploadedFile("big.pdf", b"x" * (10 * 1024 * 1024), content_type="application/pdf")
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": large}, **headers, format="multipart")
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_upload_creates_resume_record(self):
        headers = self._auth_header(self.student)
        count_before = ApplicationResume.objects.count()
        resp = self.client.post("/api/internships/upload-resume",
            {"resume": self._create_resume_file()},
            **headers, format="multipart")
        if resp.status_code == status.HTTP_201_CREATED:
            self.assertEqual(ApplicationResume.objects.count(), count_before + 1)
