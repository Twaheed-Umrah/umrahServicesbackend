# Generated by Django 5.2.3 on 2025-06-30 19:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiries', '0007_remove_contactus_notes_remove_contactus_processed_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactus',
            name='api_key',
            field=models.ForeignKey(blank=True, help_text='API key used to submit this contact form', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_submissions', to='enquiries.apikey'),
        ),
        migrations.AlterField(
            model_name='contactus',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='contactus',
            name='email',
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='contactus',
            name='submitted_by_user',
            field=models.ForeignKey(blank=True, help_text='User who owns the API key used for submission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_submissions', to=settings.AUTH_USER_MODEL),
        ),
    ]
