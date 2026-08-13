import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mentorships", "0004_delete_mentorshiprequest"),
        ("engagements", "0001_initial"),
    ]

    operations = [
        # Dev data is disposable (decision 2026-08-13): wipe existing rows so
        # the non-null engagement column can be added to an empty table.
        migrations.RunSQL(
            sql="DELETE FROM mentorships_mentorshipengagement",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(model_name="mentorshipengagement", name="student"),
        migrations.RemoveField(model_name="mentorshipengagement", name="alumnus"),
        migrations.RemoveField(model_name="mentorshipengagement", name="source"),
        migrations.RemoveField(model_name="mentorshipengagement", name="source_id"),
        migrations.RemoveField(model_name="mentorshipengagement", name="status"),
        migrations.RemoveField(model_name="mentorshipengagement", name="updated_at"),
        migrations.AddField(
            model_name="mentorshipengagement",
            name="engagement",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mentorship_detail",
                to="engagements.engagement",
            ),
        ),
        migrations.AddField(
            model_name="mentorshipengagement",
            name="application",
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="engagements",
                to="mentorships.mentorshipapplication",
            ),
        ),
        migrations.AddField(
            model_name="mentorshipengagement",
            name="offer",
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="engagements",
                to="mentorships.mentorshipoffer",
            ),
        ),
        migrations.AddConstraint(
            model_name="mentorshipengagement",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(("application__isnull", False), ("offer__isnull", True))
                    | models.Q(("application__isnull", True), ("offer__isnull", False))
                ),
                name="mentorship_engagement_single_origin",
            ),
        ),
    ]
