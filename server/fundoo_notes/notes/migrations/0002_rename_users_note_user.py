# Generated by Django 5.1.1 on 2024-09-12 09:39

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("notes", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="note",
            old_name="users",
            new_name="user",
        ),
    ]
