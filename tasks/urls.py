from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    path("<int:pk>/update/", views.TaskUpdateView.as_view(), name="task_update"),
    path("<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("", views.TaskListView.as_view(), name="task_list"),
    path("<int:pk>/accept/", views.task_accept, name="task_accept"),
    path("<int:pk>/reject/", views.task_reject, name="task_reject"),
    path("<int:pk>/complete/", views.task_complete, name="task_complete"),
    path("<int:pk>/rate/", views.task_rate, name="task_rate"),
    path("create/", views.TaskCreateView.as_view(), name="task_create_button"),
]
