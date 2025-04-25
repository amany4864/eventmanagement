from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPES = (
        ('organizer', 'Event Organizer'),
        ('attendee', 'Event Attendee')
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='attendee')
    phone = models.CharField(max_length=15, blank=True)
    
    def is_organizer(self):
        return self.user_type == 'organizer'