# Generated by Django 5.1.5 on 2025-03-24 09:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_feename_membership'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membershiptype',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='membershiptype',
            name='registration_fee',
        ),
    ]
