from unittest import mock

from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import StudentResume
from internships.models import Internship
from futaverse.tests_helpers import BaseAPITestCase

RESUME_URL = "http://example.com/resumes/resume.pdf"


def _resume_file(name="resume.pdf", content=b"fake-pdf-content", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


class StudentResumeEndpointTests(BaseAPITestCase):
    def setUp(self):
        self.student = self._create_student("stu@test.com")
        self.other_student = self._create_student("other@test.com")
        self.alumnus = self._create_alumnus("alum@test.com")

    def _upload_resume(self, user, file):
        headers = self._auth_header(user)
        with mock.patch("core.views.upload_file_to_supabase", return_value=RESUME_URL):
            return self.client.post("/api/students/resumes/upload", {"resume": file}, **headers, format="multipart")

    # --- UPLOAD ---
    def test_student_uploads_resume_returns_201(self):
        resp = self._upload_resume(self.student, _resume_file())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["resume"], RESUME_URL)

    def test_uploaded_resume_returns_sqid_and_filename(self):
        resp = self._upload_resume(self.student, _resume_file("my_resume.pdf"))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("sqid", resp.data)
        self.assertEqual(resp.data["filename"], "my_resume.pdf")

    def test_no_resume_file_returns_400(self):
        headers = self._auth_header(self.student)
        resp = self.client.post("/api/students/resumes/upload", {}, **headers, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_pdf_returns_400(self):
        resp = self._upload_resume(self.student, _resume_file("resume.txt", b"text", "text/plain"))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversized_file_returns_400(self):
        big = _resume_file("big.pdf", b"x" * (5 * 1024 * 1024 + 1))
        resp = self._upload_resume(self.student, big)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_can_upload_multiple_resumes(self):
        self._upload_resume(self.student, _resume_file("one.pdf"))
        self._upload_resume(self.student, _resume_file("two.pdf"))
        self.assertEqual(StudentResume.objects.filter(student=self.student.student_profile).count(), 2)

    def test_alumnus_cannot_upload(self):
        headers = self._auth_header(self.alumnus)
        resp = self.client.post("/api/students/resumes/upload", {"resume": _resume_file()}, **headers, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_upload(self):
        resp = self.client.post("/api/students/resumes/upload", {"resume": _resume_file()}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- LIST ---
    def test_student_lists_own_resumes(self):
        self._upload_resume(self.student, _resume_file("one.pdf"))
        self._upload_resume(self.student, _resume_file("two.pdf"))
        headers = self._auth_header(self.student)
        resp = self.client.get("/api/students/resumes", **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_student_does_not_see_other_resumes(self):
        self._upload_resume(self.other_student, _resume_file("other.pdf"))
        headers = self._auth_header(self.student)
        resp = self.client.get("/api/students/resumes", **headers)
        self.assertEqual(len(resp.data), 0)

    # --- DELETE ---
    def test_student_deletes_own_resume(self):
        upload_resp = self._upload_resume(self.student, _resume_file())
        headers = self._auth_header(self.student)
        resp = self.client.delete(f"/api/students/resumes/{upload_resp.data['sqid']}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        list_resp = self.client.get("/api/students/resumes", **headers)
        self.assertEqual(len(list_resp.data), 0)

    def test_student_cannot_delete_other_resume(self):
        upload_resp = self._upload_resume(self.other_student, _resume_file())
        headers = self._auth_header(self.student)
        resp = self.client.delete(f"/api/students/resumes/{upload_resp.data['sqid']}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_is_soft(self):
        upload_resp = self._upload_resume(self.student, _resume_file())
        headers = self._auth_header(self.student)
        self.client.delete(f"/api/students/resumes/{upload_resp.data['sqid']}", **headers)

        resume = StudentResume.all_objects.get(sqid=upload_resp.data["sqid"])
        self.assertTrue(resume.is_deleted)
        self.assertIsNotNone(resume.deleted_at)

    def test_delete_referenced_resume_keeps_application_access(self):
        internship = Internship.objects.create(
            alumnus=self.alumnus.alumni_profile,
            title="SE Intern", description="desc", work_mode="Remote",
            engagement_type="Full-time", location="Lagos", duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            is_paid=True, stipend=100000, levels=[300],
            company="TC", company_type="Tech", industry="Tech",
            available_slots=5, remaining_slots=5,
            require_resume=False,
        )
        upload_resp = self._upload_resume(self.student, _resume_file())
        headers = self._auth_header(self.student)
        self.client.post("/api/internships/application", {
            "internship": internship.sqid,
            "resume": upload_resp.data["sqid"],
        }, **headers, format="json")

        resp = self.client.delete(f"/api/students/resumes/{upload_resp.data['sqid']}", **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        resume = StudentResume.all_objects.get(sqid=upload_resp.data["sqid"])
        self.assertTrue(resume.is_deleted)

        alum_headers = self._auth_header(self.alumnus)
        list_resp = self.client.get("/api/internships/applications", **alum_headers)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(list_resp.data[0]["resume_info"]["sqid"], upload_resp.data["sqid"])
        self.assertEqual(list_resp.data[0]["resume_info"]["resume"], RESUME_URL)