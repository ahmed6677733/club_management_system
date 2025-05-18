from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Member

@receiver(pre_save, sender=Member)
def generate_membership_id(sender, instance, **kwargs):
    if not instance.membership_id:
        instance.membership_id = instance.generate_membership_id()