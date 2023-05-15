from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "customer_username",
        "worker_username",
        "status",
        "created_time",
    )
    list_filter = ("status",)
    search_fields = ("title", "description")
    date_hierarchy = "created_time"
    actions = ["mark_as_in_progress", "mark_as_completed", "mark_as_rejected"]

    def mark_as_in_progress(self, request, queryset):
        queryset.update(status="in-progress")

    mark_as_in_progress.short_description = "Mark selected tasks as in-progress"

    def mark_as_completed(self, request, queryset):
        queryset.update(status="completed")

    mark_as_completed.short_description = "Mark selected tasks as completed"

    def mark_as_rejected(self, request, queryset):
        queryset.update(status="rejected")

    mark_as_rejected.short_description = "Mark selected tasks as rejected"

    def customer_username(self, obj):
        return obj.customer.user.username

    customer_username.admin_order_field = "customer__user__username"
    customer_username.short_description = "Customer Username"

    def worker_username(self, obj):
        if obj.worker:
            return obj.worker.user.username
        else:
            return "-"

    worker_username.admin_order_field = "worker__user__username"
    worker_username.short_description = "Worker Username"
