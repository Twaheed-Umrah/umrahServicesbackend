# Generated by Django 5.2.3 on 2025-07-02 16:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('visa', '0002_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visaapplication',
            name='embassy_fee',
        ),
        migrations.RemoveField(
            model_name='visaapplication',
            name='service_fee',
        ),
    ]
