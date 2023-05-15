from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from users.models import Customer, Worker
from django.core.validators import MinValueValidator


class Task(models.Model):
    STATUS_CHOICES = [
        ("requested", _("Requested")),
        ("in-progress", _("In progress")),
        ("completed", _("Completed")),
        ("rejected", _("Rejected")),
        ("vanished", _("Vanished")),
    ]
    request_id = models.CharField(max_length=50, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)
    last_updated_time = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="requested"
    )
    rating = models.IntegerField(blank=True, null=True)
    review = models.TextField(blank=True)
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_time"]


class TaskNotification(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="task_notifications"
    )

    def __str__(self):
        return self.message
