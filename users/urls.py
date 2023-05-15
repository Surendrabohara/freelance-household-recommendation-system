from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.base_view, name="home"),
    path(
        "register/customer/",
        views.CustomerRegistrationView.as_view(),
        name="customer_registration",
    ),
    path(
        "register/worker/",
        views.WorkerRegistrationView.as_view(),
        name="worker_registration",
    ),
    path(
        "update/customer/", views.CustomerUpdateView.as_view(), name="customer_update"
    ),
    path("update/worker/", views.WorkerUpdateView.as_view(), name="worker_update"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path(
        "activate/<str:uidb64>/<str:token>/",
        views.ActivateAccountView.as_view(),
        name="activate_account",
    ),
    path(
        "activate-worker/<uidb64>/<token>/",
        views.ActivateWorkerView.as_view(),
        name="activate_worker",
    ),
    path(
        "worker-profile/<int:pk>/",
        views.WorkerProfileView.as_view(),
        name="worker_profile",
    ),
]
