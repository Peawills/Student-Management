from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import ParentProfile, PortalMessage, Student


class UserProfileForm(forms.ModelForm):
    """Form for updating basic user information."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class ParentProfileForm(forms.ModelForm):
    """Form for updating parent-specific profile information."""

    class Meta:
        model = ParentProfile
        fields = ["phone_number", "address", "occupation"]
        widgets = {
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """A custom password change form with Bootstrap classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter your old password"}
        )
        self.fields["new_password1"].widget = forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter a new password"}
        )
        self.fields["new_password2"].widget = forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm new password"}
        )


class PortalMessageForm(forms.ModelForm):
    """Form for composing a new message."""

    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Queryset is set in the view
        widget=forms.Select(attrs={"class": "form-select"}),
        label="To (Staff Member)",
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),  # Queryset is set in the view for parents
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Regarding Student",
        required=False,
    )

    class Meta:
        model = PortalMessage
        fields = ["recipient", "student", "subject", "message"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        # Pop the 'user' argument to use for filtering
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            # Populate the recipient list with all staff users
            self.fields["recipient"].queryset = User.objects.filter(
                is_staff=True
            ).order_by("first_name", "last_name")

            # If the user is a parent, populate the student list with their children
            if hasattr(user, "parent_profile"):
                self.fields["student"].queryset = user.parent_profile.students.all()
                self.fields["student"].required = True
            else:
                # If the user is a student, hide the 'student' field
                # as the message is implicitly about them.
                if "student" in self.fields:
                    del self.fields["student"]


class ReplyMessageForm(forms.ModelForm):
    """Form for replying to a message."""

    class Meta:
        model = PortalMessage
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Write your reply..."}
            )
        }
        labels = {"message": ""}


class ParentInvitationForm(forms.Form):
    """Form for a parent to accept an invitation and create an account."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Choose a username"}
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Create a password"}
        ),
        label="Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm your password"}
        ),
        label="Confirm Password",
    )

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2