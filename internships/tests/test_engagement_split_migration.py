from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class EngagementDetailSplitMigrationTests(TransactionTestCase):
    migrate_from = [("internships", "0005_alter_internship_duration_weeks")]
    migrate_to = [("internships", "0006_engagement_detail_split")]

    def _old_state_apps(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        return executor.loader.project_state(self.migrate_from).apps

    def _migrate_forward(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        return executor.loader.project_state(self.migrate_to).apps

    def _seed_old_row(self, apps, *, source, source_id):
        User = apps.get_model("core", "User")
        StudentProfile = apps.get_model("core", "StudentProfile")
        AlumniProfile = apps.get_model("core", "AlumniProfile")
        Internship = apps.get_model("internships", "Internship")
        InternshipEngagement = apps.get_model("internships", "InternshipEngagement")

        student_user = User.objects.create(email="s@t.com", password="p", role="student", is_active=True)
        alumnus_user = User.objects.create(email="a@t.com", password="p", role="alumni", is_active=True)
        student = StudentProfile.objects.create(
            user=student_user, phone_num="0801", gender="male", firstname="S", lastname="T",
            address="X", state="Lagos", country="NG", department="CS", faculty="Eng",
            level=300, cgpa=4.0, skills=[], expected_grad_year="2027",
        )
        alumnus = AlumniProfile.objects.create(
            user=alumnus_user, phone_num="0802", gender="male", firstname="A", lastname="B",
            address="Y", state="Ogun", country="NG", department="CS", faculty="Eng",
            grad_year="2020", current_job_title="SE", current_company="TC",
            industry="Tech", years_of_exp=3,
        )
        internship = Internship.objects.create(
            alumnus=alumnus, title="T", description="d", work_mode="Remote",
            engagement_type="Full-time", location="Remote", duration_weeks=12,
            start_date="2026-01-01", end_date="2026-03-31",
            company="TC", company_type="Tech", industry="Tech",
        )
        return InternshipEngagement.objects.create(
            internship=internship, student=student, alumnus=alumnus,
            source=source, source_id=source_id, status="active",
        )

    def test_split_creates_shared_engagement_row(self):
        apps = self._old_state_apps()
        old_row = self._seed_old_row(apps, source="application", source_id=999999)
        new_apps = self._migrate_forward()

        Engagement = new_apps.get_model("engagements", "Engagement")
        InternshipEngagement = new_apps.get_model("internships", "InternshipEngagement")

        new_row = InternshipEngagement.objects.get(pk=old_row.pk)
        self.assertIsNotNone(new_row.engagement)
        self.assertEqual(new_row.engagement.engagement_type, "internship_engagement")
        self.assertEqual(new_row.engagement.status, "active")
        self.assertEqual(new_row.engagement.student_id, old_row.student_id)
        self.assertEqual(new_row.engagement.alumnus_id, old_row.alumnus_id)
        self.assertEqual(Engagement.objects.count(), 1)

    def test_unresolvable_origin_soft_deletes_both_rows(self):
        apps = self._old_state_apps()
        old_row = self._seed_old_row(apps, source="offer", source_id=999999)
        new_apps = self._migrate_forward()

        InternshipEngagement = new_apps.get_model("internships", "InternshipEngagement")
        new_row = InternshipEngagement.objects.get(pk=old_row.pk)
        self.assertTrue(new_row.is_deleted)
        self.assertIsNotNone(new_row.deleted_at)
        self.assertTrue(new_row.engagement.is_deleted)
        self.assertIsNone(new_row.application_id)
        self.assertIsNone(new_row.offer_id)
