import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("internships", "0005_alter_internship_duration_weeks"),
        ("engagements", "0001_initial"),
    ]

    operations = [
        # Dev data is disposable (decision 2026-08-13): wipe existing rows so
        # the non-null engagement column can be added to an empty table.
        migrations.RunSQL(
            sql="DELETE FROM internships_internshipengagement",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(model_name="internshipengagement", name="student"),
        migrations.RemoveField(model_name="internshipengagement", name="alumnus"),
        migrations.RemoveField(model_name="internshipengagement", name="source"),
        migrations.RemoveField(model_name="internshipengagement", name="source_id"),
        migrations.RemoveField(model_name="internshipengagement", name="status"),
        migrations.RemoveField(model_name="internshipengagement", name="updated_at"),
        migrations.AddField(
            model_name="internshipengagement",
            name="engagement",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="internship_detail",
                to="engagements.engagement",
            ),
        ),
        migrations.AddField(
            model_name="internshipengagement",
            name="application",
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="engagements",
                to="internships.internshipapplication",
            ),
        ),
        migrations.AddField(
            model_name="internshipengagement",
            name="offer",
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="engagements",
                to="internships.internshipoffer",
            ),
        ),
        migrations.AddConstraint(
            model_name="internshipengagement",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(("application__isnull", False), ("offer__isnull", True))
                    | models.Q(("application__isnull", True), ("offer__isnull", False))
                ),
                name="internship_engagement_single_origin",
            ),
        ),
    ]
