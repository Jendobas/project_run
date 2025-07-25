# Generated by Django 5.2 on 2025-07-13 16:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_run", "0003_alter_run_athlete_alter_run_status"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="AthleteInfo",
            fields=[
                (
                    "user_id",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="athlete_info",
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("goals", models.TextField(default=None)),
                ("weight", models.IntegerField(default=None)),
            ],
        ),
    ]
