from django.db import models

class Role(models.TextChoices):
    Writer = "writer"
    Editor = "editor"
    Admin = "admin"
