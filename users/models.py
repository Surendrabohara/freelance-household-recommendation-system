from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    is_customer = models.BooleanField(default=False)
    is_worker = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions granted to each of their groups."
        ),
        related_query_name="custom_user",
        related_name="%(app_label)s_%(class)s_related",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_query_name="custom_user",
        related_name="%(app_label)s_%(class)s_related",
    )


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        default="https://cdn4.iconfinder.com/data/icons/small-n-flat/24/user-512.png",
    )


class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    skills = models.CharField(max_length=255)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    email_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    approved_by_admin = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        default="https://cdn4.iconfinder.com/data/icons/small-n-flat/24/user-512.png",
    )


class HourlyRateApproval(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Hourly rate approval for {self.worker.user.username}"
