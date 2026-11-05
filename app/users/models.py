from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from utils.role import Role


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email field is missing")
        extra.setdefault("role", Role.Writer)
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.Admin)
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    email = models.EmailField(unique=True) 
    username = models.CharField(max_length=150, unique=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.Writer)
    image_url = models.URLField(
        max_length=500,
        default="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
    )
    verification_code = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 

    objects = UserManager() # type: ignore

    def __str__(self):
        return self.email
