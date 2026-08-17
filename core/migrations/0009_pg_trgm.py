from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_studentresume_many"),
    ]

    operations = [
        TrigramExtension(),
    ]
