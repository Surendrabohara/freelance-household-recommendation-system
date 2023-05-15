from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Customer, Worker, HourlyRateApproval
from django.core.exceptions import ValidationError


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.is_customer = True
        if commit:
            user.save()
            Customer.objects.create(user=user)
        return user


class WorkerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    location = forms.CharField(max_length=255, required=True)
    skills = forms.CharField(max_length=255, required=True)
    hourly_rate = forms.FloatField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "location",
            "skills",
            "hourly_rate",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if not phone_number.isdigit():
            raise ValidationError("Invalid phone number.")
        return phone_number

    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data["hourly_rate"]
        if hourly_rate < 0:
            raise ValidationError("Hourly rate cannot be negative.")
        return hourly_rate

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.is_worker = True
        if commit:
            user.save()
            worker = Worker.objects.create(
                user=user,
                location=self.cleaned_data["location"],
                skills=self.cleaned_data["skills"],
                hourly_rate=self.cleaned_data["hourly_rate"],
            )
            hourly_rate_approval = HourlyRateApproval.objects.create(
                worker=worker, hourly_rate=self.cleaned_data["hourly_rate"]
            )
        return user


class CustomerUpdateForm(forms.ModelForm):
    email = forms.EmailField(disabled=True)
    phone_number = forms.CharField(max_length=15, required=True)
    location = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Customer
        fields = (
            "location",
            "profile_picture",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.fields["email"].initial = user.email
        self.fields["phone_number"].initial = user.phone_number
        self.fields["location"].initial = self.instance.location

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if not phone_number.isdigit():
            raise ValidationError("Invalid phone number.")
        return phone_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.location = self.cleaned_data["location"]
        if commit:
            instance.save()
            instance.user.phone_number = self.cleaned_data["phone_number"]
            instance.user.save()
        return instance


class WorkerUpdateForm(forms.ModelForm):
    email = forms.EmailField(disabled=True)
    phone_number = forms.CharField(max_length=15, required=True)
    location = forms.CharField(max_length=255, required=True)
    skills = forms.CharField(max_length=255, required=True)
    hourly_rate = forms.FloatField(required=True)

    class Meta:
        model = Worker
        fields = (
            "location",
            "skills",
            "hourly_rate",
            "is_available",
            "profile_picture",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.fields["email"].initial = user.email
        self.fields["phone_number"].initial = user.phone_number
        self.fields["location"].initial = self.instance.location
        self.fields["skills"].initial = self.instance.skills
        self.fields["hourly_rate"].initial = self.instance.hourly_rate

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if not phone_number.isdigit():
            raise ValidationError("Invalid phone number.")
        return phone_number

    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data["hourly_rate"]
        if hourly_rate < 0:
            raise ValidationError("Hourly rate cannot be negative.")
        return hourly_rate
