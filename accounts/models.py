from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomerProfile(models.Model):
    """
    Extends Django's built-in User model with customer-specific attributes
    such as phone number and address.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, help_text="Customer contact phone number")
    address = models.TextField(blank=True, help_text="Delivery or pickup contact address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def full_name(self):
        name = self.user.get_full_name()
        return name if name else self.user.username


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Ensures a CustomerProfile exists whenever a new User is created.
    """
    if created:
        CustomerProfile.objects.get_or_create(user=instance)
