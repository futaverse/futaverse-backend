# Generated manually on 2026-08-19
# Fixes shuffle_seed backfill: migration 0007 applied random.random() once per
# Python call, giving every row the SAME value. This uses PostgreSQL's RANDOM()
# which is evaluated per-row, giving each event a unique tiebreaker.

from django.db import migrations


def fix_shuffle_seed(apps, schema_editor):
    schema_editor.execute("UPDATE feed_feedevent SET shuffle_seed = RANDOM()")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("feed", "0007_backfill_shuffle_seed"),
    ]

    operations = [
        migrations.RunPython(fix_shuffle_seed, noop),
    ]
