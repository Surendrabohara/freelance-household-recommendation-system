from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from users.models import Customer, Worker
from tasks.models import Task
from tasks.forms import TaskCreateForm
import pytz
from unittest import mock
import uuid


class TaskCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer_user = User.objects.create_user(
            username="customer", password="password"
        )
        self.worker_user = User.objects.create_user(
            username="worker", password="password"
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        self.worker = Worker.objects.create(user=self.worker_user, hourly_rate=10)
        self.url = reverse("tasks:task_create")

    def test_task_create_view(self):
        self.client.login(username="customer", password="password")
        start_time = datetime.now(pytz.utc) + timedelta(hours=2)
        end_time = datetime.now(pytz.utc) + timedelta(hours=4)
        data = {
            "title": "Test Task",
            "description": "This is a test task.",
            "start_time": start_time,
            "end_time": end_time,
            "location": "Test location",
        }
        form = TaskCreateForm(data)
        self.assertTrue(form.is_valid())
        with mock.patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("abcdefg")
            response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.first()
        self.assertEqual(task.customer, self.customer)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "This is a test task.")
        self.assertEqual(task.start_time, start_time)
        self.assertEqual(task.end_time, end_time)
        self.assertEqual(task.location, "Test location")
        self.assertEqual(task.status, "requested")
        self.assertEqual(task.request_id, "abcdefg")
        self.assertEqual(task.hourly_rate, self.worker.hourly_rate)
        self.assertEqual(task.total_cost, None)
        self.assertEqual(task.rating, None)
        self.assertEqual(task.review, "")
        self.assertEqual(task.worker, self.worker)


class TaskUpdateViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a customer user
        self.customer_user = User.objects.create_user(
            username="customer", password="testpassword"
        )
        self.customer = Customer.objects.create(user=self.customer_user)

        # Create a worker user
        self.worker_user = User.objects.create_user(
            username="worker", password="testpassword"
        )
        self.worker = Worker.objects.create(user=self.worker_user, hourly_rate=20)

        # Create a task
        self.task = Task.objects.create(
            customer=self.customer,
            title="Test Task",
            description="Test task description",
            location="Test Location",
            hourly_rate=20,
            start_time="2023-05-01 08:00:00",
            end_time="2023-05-01 10:00:00",
            status="requested",
        )

    def test_task_update_view(self):
        # Login as worker
        self.client.force_login(self.worker_user)

        # Update the task status to "in-progress"
        url = reverse("tasks:task_update", kwargs={"pk": self.task.pk})
        data = {
            "status": "in-progress",
            "start_time": "2023-05-01 08:00:00",
            "end_time": "2023-05-01 10:00:00",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tasks:task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "in-progress")
        self.assertEqual(self.task.worker, self.worker)
        self.assertEqual(self.task.start_time.year, 2023)
        self.assertEqual(self.task.end_time.year, 2023)

        # Update the task status to "completed"
        url = reverse("tasks:task_update", kwargs={"pk": self.task.pk})
        data = {"status": "completed"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tasks:task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

        # Update the task status to "rejected"
        url = reverse("tasks:task_update", kwargs={"pk": self.task.pk})
        data = {"status": "rejected"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tasks:task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "rejected")