# main/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or save the UserProfile whenever a User instance is created or updated.
    """
    if created:
        # Create a new UserProfile when a User is created
        UserProfile.objects.create(user=instance)
    else:
        # Save the existing UserProfile when a User is updated
        instance.userprofile.save()