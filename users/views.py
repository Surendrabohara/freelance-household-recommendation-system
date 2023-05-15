from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib import messages
from .forms import (
    CustomerRegistrationForm,
    WorkerRegistrationForm,
    CustomerUpdateForm,
    WorkerUpdateForm,
)
from .models import User, Customer, Worker, HourlyRateApproval
from .tokens import account_activation_token
from django.http import HttpResponseRedirect
from tasks.models import Task
from django.contrib.auth.decorators import login_required
from tasks.forms import TaskCreateForm
from django.db.models import Avg, Count, Q
from tasks.models import TaskNotification


def base_view(request):
    if hasattr(request.user, "customer"):
        # Retrieve the latest task notifications
        task_notifications = TaskNotification.objects.filter(
            customer=request.user.customer
        ).order_by("-created_time")[:5]

        context = {
            "task_notifications": task_notifications,
        }
        return render(request, "users/home.html", context)
    return render(request, "users/home.html")


class CustomerRegistrationView(CreateView):
    """
    A view that handles customer registration.

    Allows new users to register as customers by submitting a registration form.
    Upon successful submission, an activation email is sent to the customer's email address
    with an activation link to complete the registration process.

    Attributes:
    -----------
    model: django.db.models.Model
        The model that the view will use to create a new object (in this case, User).
    form_class: django.forms.ModelForm
        The form class that the view will use to handle form submission.
    template_name: str
        The name of the template that the view will use to render the HTML response.
    success_url: django.urls.reverse_lazy
        The URL to redirect to after a successful form submission.

    Methods:
    --------
    form_valid(form: django.forms.ModelForm) -> django.http.HttpResponseRedirect
        Handles form submission when the form data is valid.
        Sends an activation email to the customer's email address with an activation link.
        Optionally, sends a notification email to the admin.
        Redirects to the success URL with a success message.
    """

    model = User
    form_class = CustomerRegistrationForm
    template_name = "users/customer_registration.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Send email to the customer with the activation link
        mail_subject = "Activate your account"
        message = render_to_string(
            "users/activation_email.txt",
            {
                "user": self.object,
                "domain": self.request.META["HTTP_HOST"],
                "uid": urlsafe_base64_encode(force_bytes(self.object.pk)),
                "token": account_activation_token.make_token(self.object),
            },
        )
        to_email = form.cleaned_data.get("email")
        send_mail(
            mail_subject,
            message,
            settings.EMAIL_HOST_USER,
            [to_email],
            fail_silently=False,
        )

        # Optionally, send notification email to admin (not implemented)

        messages.success(
            self.request,
            "Please confirm your email address to complete the registration.",
        )
        return response


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to handle updating the customer profile information.

    Attributes:
        model (Customer): The model to use for this view.
        form_class (CustomerUpdateForm): The form class to use for this view.
        template_name (str): The name of the template to render.
        success_url (str): The URL to redirect to upon successfully updating the profile.

    Methods:
        get_object(): Returns the object to update. In this case, it returns the customer object of the currently logged in user.
        get_form_kwargs(): Returns the keyword arguments for instantiating the form. In this case, it adds the customer object as an instance parameter to the keyword arguments.
    """

    model = Customer
    form_class = CustomerUpdateForm
    template_name = "users/customer_update.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self):
        return self.request.user.customer

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.get_object()})
        return kwargs


class WorkerRegistrationView(CreateView):
    """
    A view that allows a user to register as a worker.

    Uses the `WorkerRegistrationForm` to create a new user and worker instance.
    Sends an email to the user with the activation link to confirm their email address.
    Sets `approved_by_admin` to False by default for the worker instance.

    Template: `users/worker_registration.html`

    Attributes:
        model: The model class that the view will create a new instance of.
        form_class: The form class that the view will use to create a new instance of `User`.
        template_name: The name of the template to render.
        success_url: The URL to redirect to after a successful form submission.

    Methods:
        form_valid(form): Called when a valid form is submitted. Sends an email to the user with the activation link to confirm their email address.
    """

    model = User
    form_class = WorkerRegistrationForm
    template_name = "users/worker_registration.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Set approved_by_admin to False by default
        worker = self.object.worker
        worker.approved_by_admin = False
        worker.save()

        # Send email to the worker with the activation link
        mail_subject = "Activate your account"
        message = render_to_string(
            "users/activation_email.txt",
            {
                "user": self.object,
                "domain": self.request.META["HTTP_HOST"],
                "uid": urlsafe_base64_encode(force_bytes(self.object.pk)),
                "token": account_activation_token.make_token(self.object),
            },
        )
        to_email = form.cleaned_data.get("email")
        send_mail(
            mail_subject,
            message,
            settings.EMAIL_HOST_USER,
            [to_email],
            fail_silently=False,
        )

        messages.success(
            self.request,
            "Please confirm your email address to complete the registration.",
        )
        return response


class WorkerUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allows a logged-in worker to update their profile information.

    Attributes:
    -----------
    model: Worker
        The model to use for updating the worker's profile.
    form_class: WorkerUpdateForm
        The form class to use for updating the worker's profile.
    template_name: str
        The name of the template to use for rendering the update form.
    success_url: str
        The URL to redirect to after the update form is successfully submitted.
    worker_hourly_rate: float
        The current hourly rate of the worker, used to detect changes in the hourly rate.

    Methods:
    --------
    get_object()
        Returns the current logged-in worker object.
    get_form_kwargs()
        Returns the keyword arguments for instantiating the update form.
    form_valid(form)
        Processes the submitted update form data and saves the worker profile updates.
        Sends a success message to the worker.

    """

    model = Worker
    form_class = WorkerUpdateForm
    template_name = "users/worker_update.html"
    success_url = reverse_lazy("users:profile")
    worker_hourly_rate = None

    def get_object(self):
        return self.request.user.worker

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        worker = self.get_object()
        self.worker_hourly_rate = worker.hourly_rate
        kwargs.update({"instance": worker})
        return kwargs

    def form_valid(self, form):
        worker = self.get_object()

        # Assign the new hourly rate to the HourlyRateApproval model
        new_hourly_rate = form.cleaned_data.get("hourly_rate")
        if new_hourly_rate != self.worker_hourly_rate:
            hourly_rate_approval = HourlyRateApproval.objects.create(
                worker=worker, hourly_rate=new_hourly_rate
            )

        # Set the hourly rate of the form to the old worker hourly rate
        form.instance.hourly_rate = self.worker_hourly_rate

        # Save the form to update the worker's profile picture and other fields
        response = super().form_valid(form)

        # Save the worker object to update other fields
        worker.save()

        # Show a success message
        messages.success(
            self.request,
            "Your profile has been updated. However, your hourly rate change request is pending approval by an admin.",
        )

        return response


class CustomLoginView(LoginView):
    """A view that handles user authentication.

    Inherits from Django's built-in `LoginView` and customizes its behavior.
    This view allows users to log in to the website by providing their username
    and password.

    If the login is successful, the view redirects the user to the homepage.
    If the login fails, the view displays an error message and prompts the user
    to try again.

    Additionally, this view performs some extra checks before allowing the user
    to log in. If the user is a customer and their email has not been verified,
    the view displays a warning message and does not allow the login to proceed.
    If the user is a worker and their email has not been verified, or if their
    account is pending approval from the admin, the view displays a warning
    message and does not allow the login to proceed.

    Attributes:
        template_name (str): The name of the template that this view uses to
            render the login form.

    Methods:
        get_success_url(): Returns the URL to which the view should redirect
            the user after a successful login.
        form_valid(form): Processes a valid login form submission and logs the
            user in.
    """

    template_name = "users/login.html"

    def get_success_url(self):
        return reverse_lazy("users:home")

    def form_valid(self, form):
        username = self.request.POST["username"]
        password = self.request.POST["password"]
        user = authenticate(self.request, username=username, password=password)

        if user is not None and user.is_active:
            if user.is_customer and not user.customer.email_verified:
                messages.warning(
                    self.request, "Please verify your email address before logging in."
                )
                return self.form_invalid(form)
            elif user.is_worker and not user.worker.email_verified:
                messages.warning(
                    self.request, "Please verify your email address before logging in."
                )
                return self.form_invalid(form)
            elif user.is_worker and not user.worker.approved_by_admin:
                messages.warning(
                    self.request, "Your account is pending approval from the admin."
                )
                return self.form_invalid(form)
            else:
                login(self.request, user)
                messages.success(self.request, "Logged in successfully.")
                return redirect(self.get_success_url())
        else:
            messages.warning(self.request, "Invalid username or password.")
            return redirect(self.form_invalid(form))


class CustomLogoutView(LogoutView):
    """
    View for logging out the user and redirecting them to the home page.
    """

    next_page = reverse_lazy("users:home")


class ActivateAccountView(View):
    def get(self, request, *args, **kwargs):
        uidb64 = kwargs["uidb64"]
        token = kwargs["token"]
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            if user.is_customer:
                user.customer.email_verified = True
                user.is_active = True
                user.customer.save()
                user.save()
                messages.success(
                    request, "Your account has been activated successfully."
                )
                return redirect("users:login")
            elif user.is_worker:
                user.worker.email_verified = True
                user.is_active = True
                user.worker.save()
                user.save()
                messages.success(
                    request, "Your account has been activated successfully."
                )
                return redirect("users:login")
        else:
            print("Invalid activation link")
            messages.error(request, "Invalid activation link.")
            return redirect("users:login")


class ActivateWorkerView(View):
    """
    View to activate a user account using the activation link sent to their email.
    Checks if the user exists and the activation token is valid. If valid, sets the
    user's email_verified attribute to True and redirects to the login page with a
    success message. If invalid, displays an error message and redirects to the login page.
    """

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs["uidb64"]
        token = kwargs["token"]
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            worker = Worker.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Worker.DoesNotExist):
            worker = None

        if worker is not None and default_token_generator.check_token(
            worker.user, token
        ):
            worker.email_verified = True
            worker.user.is_active = True
            worker.save()
            worker.user.save()
            messages.success(request, "Worker account has been activated successfully.")
            return redirect("users:login")
        else:
            messages.error(request, "Invalid activation link.")
            return redirect("users:login")


class UserProfileView(LoginRequiredMixin, DetailView):
    """View for displaying the profile of the logged in user.

    Attributes:
        template_name (str): The name of the template to be rendered.

    Methods:
        get_object(): Returns the user object of the currently logged in user.
        get_context_data(**kwargs): Adds additional context to be passed to the template,
            such as the customer or worker object associated with the user.

    """

    template_name = "users/user_profile.html"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_customer:
            context["customer"] = user.customer
        elif user.is_worker:
            context["worker"] = user.worker
        return context


class WorkerProfileView(LoginRequiredMixin, DetailView):
    """
    A view that displays the profile of a specific worker. Only accessible to logged-in users.
    Inherits from Django's built-in DetailView.

    Attributes:
        model: The Django model to use for retrieving the worker object.
        template_name: The name of the template to render.
    """

    model = Worker
    template_name = "users/worker_profile.html"

    def get_context_data(self, **kwargs):
        """
        Adds additional context data to be used in the template. Calculates the average rating and
        the number of completed tasks for the worker.

        Returns:
            A dictionary containing the context data.
        """
        context = super().get_context_data(**kwargs)
        worker = get_object_or_404(Worker, pk=self.kwargs["pk"])

        # Calculate the average rating for the worker
        avg_rating = Task.objects.filter(
            worker=worker, status="completed", rating__isnull=False
        ).aggregate(Avg("rating"))["rating__avg"]
        context["avg_rating"] = round(avg_rating, 1) if avg_rating else None

        # Count the number of completed tasks for the worker
        completed_tasks_count = Task.objects.filter(
            worker=worker, status="completed"
        ).count()
        context["completed_tasks_count"] = (
            completed_tasks_count if completed_tasks_count > 0 else None
        )

        return context
