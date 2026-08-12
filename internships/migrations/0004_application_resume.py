import django.db.models.deletion
from django.db import migrations, models


def backfill_application_resume(apps, schema_editor):
    ApplicationResume = apps.get_model('internships', 'ApplicationResume')
    StudentResume = apps.get_model('core', 'StudentResume')

    for old_resume in ApplicationResume.objects.select_related('application').all():
        if old_resume.application is None:
            continue

        filename = old_resume.resume.rsplit('/', 1)[-1]
        if not filename:
            filename = 'resume.pdf'

        new_resume = StudentResume.objects.create(
            student=old_resume.application.student,
            resume=old_resume.resume,
            filename=filename,
        )
        old_resume.application.resume = new_resume
        old_resume.application.save(update_fields=['resume'])


class Migration(migrations.Migration):

    dependencies = [
        ('internships', '0003_alter_internship_company_and_more'),
        ('core', '0008_studentresume_many'),
    ]

    operations = [
        migrations.AddField(
            model_name='internshipapplication',
            name='resume',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='applications', to='core.studentresume'),
        ),
        migrations.RunPython(backfill_application_resume, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='applicationresume',
            name='application',
        ),
        migrations.RemoveField(
            model_name='applicationresume',
            name='student',
        ),
        migrations.DeleteModel(
            name='ApplicationResume',
        ),
    ]