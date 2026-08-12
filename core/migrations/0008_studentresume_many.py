import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_alumniprofile_current_company_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentresume',
            name='filename',
            field=models.CharField(default='resume.pdf', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='studentresume',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resumes', to='core.studentprofile'),
        ),
    ]