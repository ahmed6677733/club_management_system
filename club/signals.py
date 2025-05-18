from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import date
from .models import Committee

@receiver(pre_save, sender=Committee)
def auto_deactivate_committee(sender, instance, **kwargs):
    if instance.end_date and instance.end_date < date.today():
        instance.is_active = False
