from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('byabulimi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='farmer',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True, # This prevents the crash if old data exists
                on_delete=django.db.models.deletion.CASCADE,
                related_name='farmer',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]