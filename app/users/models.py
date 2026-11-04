from enum import unique

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from utils.role import Role


class UserManager(BaseUserManager):
    use_in_migrations = True

    def createUser(self, email, role, password=None, **extra):
        if not email:
            raise ValueError("Email Field is Missing")
        user = self.model(email=self.normalize_email(email), role=role **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def createSuperUser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("role", Role.Admin)
        return self.createUser(email, Role.Admin, password, **extra)

class User(AbstractUser):
    username = None # type: ignore
    first_name = None # type: ignore
    last_name = None # type: ignore
    email = models.EmailField(blank=False, unique=True)
    name = models.CharField(blank=False)
    role = models.CharField(blank=False, choices=Role.choices, default=Role.Writer)
    image_url = models.URLField(blank=False, default="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80")
    verificationCode = models.CharField()
    verified = models.BooleanField(default=False)
    

