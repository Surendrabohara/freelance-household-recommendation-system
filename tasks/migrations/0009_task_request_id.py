# Generated by Django 3.2 on 2023-04-23 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_alter_task_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='request_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
