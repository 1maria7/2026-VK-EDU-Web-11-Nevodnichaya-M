from pathlib import Path
from uuid import uuid4
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Name",
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "first_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            Profile.objects.create(user=user)

        return user

class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email",
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="NickName",
    )
    avatar = forms.ImageField(
        required=False,
        label="Upload avatar",
    )

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name")
        labels = {
            "username": "Login",
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")

        if not avatar:
            return avatar

        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Avatar must be smaller than 5 MB."
            )

        extension = Path(avatar.name).suffix.lower()

        if (
            extension not in {".jpg", ".jpeg", ".png"}
            or avatar.image.format not in {"JPEG", "PNG"}
        ):
            raise forms.ValidationError(
                "Only JPG and PNG images are allowed."
            )

        return avatar

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        if not commit:
            return user

        user.save()

        profile, _ = Profile.objects.get_or_create(
            user=user
        )

        avatar = self.cleaned_data.get("avatar")

        if avatar:
            extension = Path(avatar.name).suffix.lower()
            avatar.name = f"{uuid4().hex}{extension}"

            profile.avatar = avatar
            profile.save(update_fields=["avatar"])

        return user