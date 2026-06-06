# main_users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class MainUserManager(BaseUserManager):
    """Custom manager for MainUser, using email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        # Set default profile picture if not provided
        if 'profile_picture' not in extra_fields:
            extra_fields['profile_picture'] = 'profile_pictures/default_profile_picture.jpg'
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class MainUser(AbstractUser):
    """Custom user model using email as the unique identifier."""
    username = None  # Remove the username field
    email = models.EmailField(unique=True)  # Use email as the unique identifier
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default_profile_picture.jpg', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)  # Placeholder for country
    language = models.CharField(max_length=50, blank=True, null=True)  # Placeholder for language

    USERNAME_FIELD = 'email'  # Set email as the unique identifier for authentication
    REQUIRED_FIELDS = []  # No additional required fields besides email

    objects = MainUserManager()  # Link the custom manager

    def __str__(self):
        return self.email
    
    @property
    def profile_picture_url(self):
        """Return the profile picture URL, using default if not set."""
        if self.profile_picture:
            try:
                return self.profile_picture.url
            except (ValueError, AttributeError):
                pass
        # Return default profile picture
        return '/main_media/profile_pictures/default_profile_picture.jpg'
