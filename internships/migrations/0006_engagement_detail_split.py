import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def split_engagement_rows(apps, schema_editor):
    InternshipEngagement = apps.get_model("internships", "InternshipEngagement")
    InternshipApplication = apps.get_model("internships", "InternshipApplication")
    InternshipOffer = apps.get_model("internships", "InternshipOffer")
    Engagement = apps.get_model("engagements", "Engagement")
    ContentType = apps.get_model("contenttypes", "ContentType")

    old_content_type = ContentType.objects.get_for_model(InternshipEngagement)
    new_content_type = ContentType.objects.get_for_model(Engagement)

    Review = apps.get_model("reviews", "Review")
    Post = apps.get_model("posts", "Post")

    try:
        Schedule = apps.get_model("django_q", "Schedule")
    except LookupError:
        Schedule = None

    now = django.utils.timezone.now()

    # Historical models carry plain unfiltered managers (custom managers are
    # not serialized into migrations), so .objects includes soft-deleted rows.
    for old in InternshipEngagement.objects.iterator():
        application = None
        offer = None

        if old.source == "application":
            application = InternshipApplication.objects.filter(pk=old.source_id).first()
        elif old.source == "offer":
            offer = InternshipOffer.objects.filter(pk=old.source_id).first()

        origin_missing = (old.source in ("application", "offer")) and application is None and offer is None

        engagement = Engagement.objects.create(
            engagement_type="internship_engagement",
            student_id=old.student_id,
            alumnus_id=old.alumnus_id,
            status=old.status,
        )

        old.engagement_id = engagement.pk
        old.application_id = application.pk if application else None
        old.offer_id = offer.pk if offer else None
        old.save(update_fields=["engagement", "application", "offer"])

        Review.objects.filter(
            source_content_type=old_content_type, source_object_id=old.pk
        ).update(source_content_type=new_content_type, source_object_id=engagement.pk)

        Post.objects.filter(
            content_type=old_content_type, object_id=old.pk
        ).update(content_type=new_content_type, object_id=engagement.pk)

        if old.is_deleted or origin_missing:
            engagement.is_deleted = True
            engagement.deleted_at = old.deleted_at or now
            engagement.save(update_fields=["is_deleted", "deleted_at"])
            if origin_missing:
                old.is_deleted = True
                old.deleted_at = now
                old.save(update_fields=["is_deleted", "deleted_at"])

    if Schedule is not None:
        Schedule.objects.filter(
            func="engagements.tasks.auto_acknowledge_engagement"
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("internships", "0005_alter_internship_duration_weeks"),
        ("engagements", "0001_initial"),
        ("reviews", "0001_initial"),
        ("posts", "0002_alter_post_post_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="internshipengagement",
            name="engagement",
            field=models.OneToOneField(
                null=True, blank=True,
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
        migrations.RunPython(split_engagement_rows, migrations.RunPython.noop),
        migrations.RemoveField(model_name="internshipengagement", name="student"),
        migrations.RemoveField(model_name="internshipengagement", name="alumnus"),
        migrations.RemoveField(model_name="internshipengagement", name="source"),
        migrations.RemoveField(model_name="internshipengagement", name="source_id"),
        migrations.RemoveField(model_name="internshipengagement", name="status"),
        migrations.RemoveField(model_name="internshipengagement", name="updated_at"),
        migrations.AddConstraint(
            model_name="internshipengagement",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(("application__isnull", False), ("offer__isnull", True))
                    | models.Q(("application__isnull", True), ("offer__isnull", False))
                    | models.Q(("is_deleted", True))
                ),
                name="internship_engagement_single_origin",
            ),
        ),
        migrations.AlterField(
            model_name="internshipengagement",
            name="engagement",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="internship_detail",
                to="engagements.engagement",
            ),
        ),
    ]
