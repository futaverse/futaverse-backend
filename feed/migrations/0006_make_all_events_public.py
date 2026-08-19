# Generated manually on 2026-08-19

from django.db import migrations


def make_all_events_public(apps, schema_editor):
    FeedEvent = apps.get_model("feed", "FeedEvent")
    FeedEvent.objects.filter(audience__in=["student", "alumni"]).update(audience="public")


def revert(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("feed", "0005_remove_feedevent_feed_feedev_score_672c5d_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(make_all_events_public, revert),
    ]
