from django.db import models
# of Django's default user model so we don't have to build them from scratch.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Overriding the default email field to make it unique.
    # We set unique=True so that two different users cannot register with the exact same email.
    email = models.EmailField(unique=True)
    # mark users who can sell on-site
    is_seller = models.BooleanField(default=False)

    # Setting the USERNAME_FIELD to 'email'.
    # This is a special Django setting that tells Django: "When someone logs in,
    # use the email field as their unique username identifier."
    USERNAME_FIELD = 'email'

    # Defining REQUIRED_FIELDS.
    # We add 'username' here so that Django still prompts for a username when creating a superuser.
    REQUIRED_FIELDS = ['username']
