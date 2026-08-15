import cloudinary
from rest_framework import status

from core.models import User, StudentProfile, AlumniProfile, UserProfileImage
from futaverse.tests_helpers import BaseAPITestCase


class MeViewTests(BaseAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cloudinary.config(cloud_name="test", api_key="test", api_secret="test")

    def test_student_gets_full_profile(self):
        student = self._create_student()
        UserProfileImage.objects.create(user=student, image="profile_images/test.jpg")

        resp = self.client.get("/api/auth/me", **self._auth_header(student))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "success")
        data = resp.data["data"]
        self.assertEqual(data["email"], "student@test.com")
        self.assertEqual(data["role"], User.Role.STUDENT)
        self.assertEqual(data["sqid"], student.sqid)
        self.assertIn("created_at", data)
        profile = data["profile"]
        self.assertEqual(profile["firstname"], "Test")
        self.assertEqual(profile["lastname"], "Student")
        self.assertEqual(profile["department"], "Computer Science")
        self.assertEqual(profile["level"], 300)
        self.assertEqual(profile["skills"], ["python", "django"])
        self.assertTrue(profile["profile_img_url"].endswith("test.jpg"))
        self.assertEqual(profile["resumes"], [])

    def test_student_gets_resumes(self):
        student = self._create_student()
        StudentProfile.objects.get(user=student).resumes.create(
            resume="https://example.com/resume.pdf",
            filename="cv.pdf",
        )

        resp = self.client.get("/api/auth/me", **self._auth_header(student))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resumes = resp.data["data"]["profile"]["resumes"]
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]["filename"], "cv.pdf")
        self.assertEqual(resumes[0]["resume"], "https://example.com/resume.pdf")

    def test_alumnus_gets_full_profile(self):
        alumnus = self._create_alumnus()
        UserProfileImage.objects.create(user=alumnus, image="profile_images/alumni.jpg")

        resp = self.client.get("/api/auth/me", **self._auth_header(alumnus))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["email"], "alumnus@test.com")
        self.assertEqual(data["role"], User.Role.ALUMNI)
        self.assertEqual(data["sqid"], alumnus.sqid)
        profile = data["profile"]
        self.assertEqual(profile["firstname"], "Test")
        self.assertEqual(profile["lastname"], "Alumnus")
        self.assertEqual(profile["current_job_title"], "Software Engineer")
        self.assertEqual(profile["current_company"], "Tech Corp")
        self.assertEqual(profile["years_of_exp"], 5)
        self.assertEqual(profile["grad_year"], "2020")
        self.assertTrue(profile["profile_img_url"].endswith("alumni.jpg"))
        self.assertNotIn("resumes", profile)
        self.assertNotIn("level", profile)

    def test_unauthenticated_request_is_rejected(self):
        resp = self.client.get("/api/auth/me")

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
