# Generated by Django 5.1.1 on 2024-09-23 08:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notes", "0002_rename_users_note_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="note",
            name="is_reminded",
            field=models.BooleanField(default=False),
        ),
    ]
