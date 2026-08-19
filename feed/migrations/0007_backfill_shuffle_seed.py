# Generated manually on 2026-08-19
# Backfills shuffle_seed for all FeedEvents that have NULL (created before
# the shuffle_seed field was added). Each gets a random float so that within
# score buckets events are interleaved rather than clustered by event_type.

import random

from django.db import migrations


def backfill_shuffle_seed(apps, schema_editor):
    FeedEvent = apps.get_model("feed", "FeedEvent")
    updated = FeedEvent.objects.filter(shuffle_seed__isnull=True).update(
        shuffle_seed=random.random()
    )
    print(f"  Backfilled shuffle_seed for {updated} FeedEvents")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("feed", "0006_make_all_events_public"),
    ]

    operations = [
        migrations.RunPython(backfill_shuffle_seed, noop),
    ]
