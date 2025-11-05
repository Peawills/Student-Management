from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Designates whether this user can access the admin site.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "is_staff",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_staff = self.cleaned_data["is_staff"]
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    is_staff = forms.BooleanField(
        required=False,
        help_text="Designates whether this user can access the admin site.",
    )
    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(),
        required=False,
        help_text="Leave blank to keep current password",
    )
    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(),
        required=False,
        help_text="Leave blank to keep current password",
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_staff")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Only validate passwords if they're provided
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match!")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_staff = self.cleaned_data["is_staff"]

        # Only update password if provided
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user
