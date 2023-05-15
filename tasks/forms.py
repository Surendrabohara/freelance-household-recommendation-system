from django import forms
from .models import Task


class TaskCreateForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        required=True,
    )

    end_time = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        required=True,
    )

    title = forms.CharField(required=True)
    description = forms.CharField(
        required=True, widget=forms.Textarea(attrs={"rows": 5})
    )
    location = forms.CharField(required=True)

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "start_time",
            "end_time",
            "location",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "eg - cleaning"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "eg - cleaning my flat having 4 rooms",
                }
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "eg - kathmandu"}
            ),
        }


class TaskStatusUpdateForm(forms.ModelForm):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("in-progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)

    class Meta:
        model = Task
        fields = ["status"]
        labels = {"status": "Status"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the current status of the task
        current_status = self.instance.status
        # Define the valid status transitions
        valid_transitions = {
            "requested": ["in-progress", "rejected"],
            "in-progress": ["completed"],
        }
        # Update the choices for the status field based on the current status
        self.fields["status"].choices = [
            (choice, label)
            for choice, label in self.fields["status"].choices
            if choice in valid_transitions[current_status]
        ]
