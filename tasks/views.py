from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.models import Group
from .models import Task, TaskNotification
from .forms import TaskCreateForm, TaskStatusUpdateForm
from users.models import Worker
from django.utils.decorators import method_decorator
from django.core import serializers
from decimal import Decimal
from django.db.models import Q, Count, Avg
from django.utils import timezone
import uuid
from tasks.recommendations import pearson_correlation_coefficient


class TaskCreateView(CreateView):
    """
    View for creating a new task. Inherits from Django's CreateView class.
    Allows a customer to create a new task by providing the task details.
    Uses the TaskCreateForm form to get the details of the task.
    On successful submission of the form, assigns the task to a worker based on their skills,
    ratings, and availability using a custom algorithm.
    Sends a request to the top 5 matching workers based on their skills and ratings.
    If no matching workers are found, uses the Pearson correlation coefficient to find
    similar workers and sends the request to them.
    """

    model = Task
    form_class = TaskCreateForm
    template_name = "tasks/task_create.html"
    success_url = reverse_lazy("tasks:task_list")

    def form_valid(self, form):
        """
        If the form is valid, creates a new task instance with the provided form data.
        Finds a matching worker based on their skills, ratings, and availability using a custom algorithm.
        Sends a task request to the top 5 matching workers.
        """
        # Set the customer for the task
        form.instance.customer = self.request.user.customer

        # Get the start and end times for the task
        start_time = form.cleaned_data.get("start_time")
        end_time = form.cleaned_data.get("end_time")

        # Get the available workers for the given time range
        available_workers = Worker.objects.filter(is_available=True)

        # Check for conflicting tasks with in-progress status
        conflicting_tasks = Task.objects.filter(
            worker__in=available_workers,
            status="in-progress",
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).distinct()

        # Exclude the workers with conflicting tasks
        available_workers = available_workers.exclude(
            id__in=[task.worker.id for task in conflicting_tasks]
        )

        # Get the related workers based on their skills and ratings
        query = form.cleaned_data.get("title")
        matching_workers = available_workers.filter(skills__icontains=query)

        # Initialize top_worker to None as a fallback
        top_worker = None

        if matching_workers.exists():
            # Get the top 5 related workers based on their ratings and completed tasks
            related_workers = (
                matching_workers.annotate(
                    rating=Avg("task__rating"),
                    tasks_completed=Count("task", filter=Q(task__status="completed")),
                )
                .order_by("-tasks_completed", "-rating")
                .filter(skills__icontains=query)[:5]
            )

        else:
            # If no worker with matching skills, use Pearson correlation coefficient
            print("No related workers found, so using Pearson coefficient")
            # If no worker with matching skills, use the first available worker as fallback
            top_worker = (
                available_workers.annotate(
                    rating=Avg("task__rating"),
                    tasks_completed=Count("task", filter=Q(task__status="completed")),
                )
                .order_by("-tasks_completed", "-rating")
                .first()
            )
            print(top_worker)
            # Call the function to generate task recommendations using Pearson correlation coefficient
            related_workers = pearson_correlation_coefficient(
                top_worker.id, available_workers, n=5
            )

        # Generate a new request ID
        request_id = str(uuid.uuid4())

        # Send the task request to the related workers
        top_five_workers = []
        related_workers_count = 0
        for worker in related_workers:
            task = form.save(commit=False)
            task.pk = None  # Create a new task instance
            task.worker = worker
            task.request_id = request_id  # Set the request ID
            task.hourly_rate = worker.hourly_rate
            task.save()
            top_five_workers.append(worker.user.username)
            related_workers_count += 1

        # Print the list of related workers who have been sent the task request
        if related_workers_count > 0:
            print(
                f"{related_workers_count} related workers have been sent the task request"
            )
            print(f"{top_five_workers}")
            messages.success(self.request, "Task created successfully!")
        else:
            print("No related workers found for the task request")
            messages.success(
                self.request, "No related workers found for the task request"
            )

        return super().form_valid(form)


def is_worker(user):
    return user.is_authenticated and user.is_worker


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allows updating the status of a `Task` instance. The `Task` model represents a task that can be created by a customer and accepted by a worker.

    Attributes:
        model (Task): The `Task` model to use for the view.
        form_class (TaskStatusUpdateForm): The form to use to update the task status.
        template_name (str): The name of the template to use for rendering the view.
        success_url (str): The URL to redirect to after a successful update.

    Methods:
        form_valid(form): Processes the form after validation, assigns the task to a worker, and creates a notification message. If the task status is "in-progress", it assigns the task to the current user (worker), sets the start time, end time, and total cost of the task, updates other tasks with the same `request_id` to "vanished", and creates a notification message. If the status is "completed" or "rejected", it updates the task status and creates a notification message.
        get_form(form_class=None): Returns an instance of the form to be used in this view. If called from a requested status, it shows only in-progress and rejected options. If called from an in-progress status, it shows only the completed option.
        get_context_data(**kwargs): Adds a boolean value to the context that indicates whether to show the update status field on the template.
    """

    model = Task
    form_class = TaskStatusUpdateForm
    template_name = "tasks/task_update.html"
    success_url = reverse_lazy("tasks:task_list")

    def form_valid(self, form):
        task = form.save(commit=False)
        if task.status == "in-progress":
            # Assign task to worker
            worker = self.request.user.worker
            task.worker = worker
            task.hourly_rate = worker.hourly_rate
            task.start_time = task.start_time.replace(tzinfo=None)
            task.end_time = task.end_time.replace(tzinfo=None)
            task.total_cost = (
                Decimal((task.end_time - task.start_time).total_seconds() / 3600)
                * task.hourly_rate
            )
            task.save()

            # Update other tasks with same request_id to "vanished"
            Task.objects.filter(request_id=task.request_id).exclude(id=task.id).update(
                status="vanished"
            )

            # Create notification message
            TaskNotification.objects.create(
                task=task,
                message=f"Worker - {task.worker.user.username} has accepted the task:'{task.title}'",
                created_time=timezone.now(),
                customer=task.customer,
            )
        else:
            task.save()
            # Create notification message
            message = None
            if task.status == "completed":
                messages.success(
                    self.request, _("Task status set to completed successfully.")
                )
                message = f"Worker - {task.worker.user.username} has completed the task:'{task.title}'"
            elif task.status == "rejected":
                messages.success(
                    self.request, _("Task status set to rejected successfully.")
                )
                message = f"Worker - {task.worker.user.username} has rejected the task:'{task.title}'"
            if message:
                TaskNotification.objects.create(
                    task=task,
                    message=message,
                    created_time=timezone.now(),
                    customer=task.customer,
                )

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        task = self.get_object()
        if self.request.GET.get("from_requested") == "true":
            # If called from requested status, show only in-progress and rejected options
            form.fields["status"].choices = [
                ("in-progress", "In Progress"),
                ("rejected", "Rejected"),
            ]
        elif task.status == "in-progress":
            # If called from in-progress status, show only completed option
            form.fields["status"].choices = [("completed", "Completed")]
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        if task.status == "completed":
            context["show_update_status"] = False
        else:
            context["show_update_status"] = True
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """
    The TaskDetailView class-based view displays the details of a particular task to a logged-in user. It inherits from Django's DetailView and requires the user to be authenticated. The view renders the tasks/task_detail.html template and uses the Task model to retrieve the details of the task.

    Attributes:

    model: The Task model used to retrieve the details of the task.
    template_name: The template used to render the view.
    Methods:

    get_object(): Overrides the method from DetailView and returns the Task object corresponding to the primary key value captured from the URL.
    get_context_data(**kwargs): Overrides the method from DetailView and adds additional context to the view. The method retrieves the Task object for the view, then retrieves the customer and worker associated with the task. The context dictionary contains the task object and the associated customer and worker objects. The method returns the updated context dictionary.

    """

    model = Task
    template_name = "tasks/task_detail.html"


class TaskListView(LoginRequiredMixin, ListView):
    """
    A view that displays a list of tasks based on the user's role (customer or worker).

    Attributes:
        model (Task): The model used by this view.
        template_name (str): The name of the template used to render the view.
        context_object_name (str): The name of the context variable containing the list of tasks.

    Methods:
        get_queryset(): Returns the list of tasks based on the user's role (customer or worker).
        get_context_data(**kwargs): Adds additional context variables based on the user's role.

    """

    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        """
        Returns the list of tasks based on the user's role (customer or worker).

        Returns:
            QuerySet: The list of tasks.

        """
        user = self.request.user
        if user.is_customer:
            tasks = Task.objects.filter(customer=user.customer).order_by(
                "-created_time"
            )
        elif user.is_worker:
            tasks = Task.objects.filter(worker=user.worker).order_by("-created_time")
        else:
            tasks = Task.objects.none()
        return tasks

    def get_context_data(self, **kwargs):
        """
        Adds additional context variables based on the user's role.

        Returns:
            dict: A dictionary containing the additional context variables.

        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_customer:
            customer = user.customer
            requested_tasks = Task.objects.filter(customer=customer, status="requested")

            request_ids = []
            unique_requested_tasks = []
            for task in requested_tasks:
                if task.request_id not in request_ids:
                    request_ids.append(task.request_id)
                    unique_requested_tasks.append(task)

            context["requested_tasks"] = unique_requested_tasks

            context["rejected_tasks"] = Task.objects.filter(
                customer=customer, status="rejected"
            )
            context["completed_tasks"] = Task.objects.filter(
                customer=customer, status="completed"
            )
            context["in_progress_tasks"] = Task.objects.filter(
                customer=customer, status="in-progress"
            )
        elif user.is_worker:
            worker = user.worker
            context["requested_tasks"] = Task.objects.filter(
                worker=worker, status="requested"
            )
            context["rejected_tasks"] = Task.objects.filter(
                worker=worker, status="rejected"
            )
            context["completed_tasks"] = Task.objects.filter(
                worker=worker, status="completed"
            )
            context["in_progress_tasks"] = Task.objects.filter(
                worker=worker, status="in-progress"
            )
        return context


@login_required
def task_accept(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.worker is not None:
        messages.warning(request, _("Task is already assigned to a worker."))
    else:
        task.worker = request.user.worker
        task.status = "in-progress"
        task.save()
        messages.success(request, _("Task accepted successfully."))
    return redirect("users:home")


@login_required
def task_reject(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.worker is not None:
        task.worker = None
        task.status = "requested"
        task.save()
        messages.success(request, _("Task rejected successfully."))
    else:
        messages.warning(request, _("Task is not assigned to any worker."))
    return redirect("users:home")


@login_required
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.worker is not None and task.worker == request.user.worker:
        task.status = "completed"
        task.save()
        messages.success(request, _("Task completed successfully."))
    else:
        messages.warning(request, _("Task is not assigned to you."))
    return redirect("users:home")


@login_required
def task_rate(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.status == "completed" and task.customer.user == request.user:
        if request.method == "POST":
            rating = request.POST.get("rating")
            review = request.POST.get("review")
            task.rating = rating
            task.review = review
            task.save()
            messages.success(request, _("Task rated successfully."))
            return redirect("users:home")
        elif task.rating is not None:
            return render(request, "tasks/task_rating.html", {"task": task})
        else:
            return render(request, "tasks/task_rate.html", {"task": task})
    else:
        messages.warning(request, _("Task is not completed or not assigned to you."))
        return redirect("users:home")
