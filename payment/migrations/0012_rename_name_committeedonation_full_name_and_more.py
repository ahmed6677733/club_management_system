# Generated by Django 5.1.5 on 2025-04-13 11:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0011_committeedonation_bank_detail_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='committeedonation',
            old_name='name',
            new_name='full_name',
        ),
        migrations.RenameField(
            model_name='committeedonation',
            old_name='phone',
            new_name='phone_number',
        ),
    ]
