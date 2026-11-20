import re

from django import forms
from django.db import transaction
from django.db.models import F

from .models import (
    Answer,
    AnswerLike,
    Question,
    QuestionLike,
    Tag,
)


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=100,
        required=True,
        label="Tags",
    )

    class Meta:
        model = Question
        fields = ("title", "text", "tags")

    def __init__(self, *args, author=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if not 5 <= len(title) <= 100:
            raise forms.ValidationError(
                "Title must contain between 5 and 100 characters."
            )

        return title

    def clean_text(self):
        text = self.cleaned_data["text"].strip()

        if not 10 <= len(text) <= 5000:
            raise forms.ValidationError(
                "Text must contain between 10 and 5000 characters."
            )

        return text

    def clean_tags(self):
        raw_tags = self.cleaned_data["tags"]

        tags = [
            tag.strip().lower()
            for tag in raw_tags.split(",")
        ]

        if any(not tag for tag in tags):
            raise forms.ValidationError(
                "Tags must not be empty."
            )

        for tag in tags:
            if not re.fullmatch(r"[a-z0-9-]+", tag):
                raise forms.ValidationError(
                    "Use English letters, numbers and hyphens in tags."
                )

        max_length = Tag._meta.get_field("name").max_length

        if any(len(tag) > max_length for tag in tags):
            raise forms.ValidationError(
                f"Each tag must contain at most {max_length} characters."
            )

        if len(tags) != len(set(tags)):
            raise forms.ValidationError(
                "Duplicate tags are not allowed."
            )

        return tags

    @transaction.atomic
    def save(self, commit=True):
        if self.author is None or not self.author.is_authenticated:
            raise ValueError("Question author is required.")

        question = super().save(commit=False)
        question.author = self.author

        if commit:
            question.save()

            tag_objects = []

            for tag_name in self.cleaned_data["tags"]:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name
                )
                tag_objects.append(tag)

            question.tags.set(tag_objects)

        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("text",)

    def __init__(self, *args, question=None, author=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.author = author

    def clean_text(self):
        text = self.cleaned_data["text"].strip()

        if not text:
            raise forms.ValidationError(
                "Answer cannot be empty."
            )

        if len(text) > 5000:
            raise forms.ValidationError(
                "Answer must contain at most 5000 characters."
            )

        return text

    @transaction.atomic
    def save(self, commit=True):
        if self.question is None:
            raise ValueError("Question is required.")

        if self.author is None or not self.author.is_authenticated:
            raise ValueError("Answer author is required.")

        answer = super().save(commit=False)
        answer.question = self.question
        answer.author = self.author

        if commit:
            answer.save()

            Question.objects.filter(
                pk=self.question.pk
            ).update(
                answers_count=F("answers_count") + 1
            )

        return answer

class QuestionLikeForm(forms.ModelForm):
    class Meta:
        model = QuestionLike
        fields = ("value",)

    def __init__(self, *args, user=None, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.question = question

    def clean(self):
        cleaned_data = super().clean()

        if self.user is None or not self.user.is_authenticated:
            raise forms.ValidationError(
                "Log in to vote."
            )

        if self.question is None:
            raise forms.ValidationError(
                "Question is required."
            )

        if QuestionLike.objects.filter(
            user=self.user,
            question=self.question,
        ).exists():
            raise forms.ValidationError(
                "You have already voted for this question."
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        like = super().save(commit=False)
        like.user = self.user
        like.question = self.question

        if commit:
            like.save()
            Question.objects.filter(
                pk=self.question.pk
            ).update(
                rating=F("rating") + like.value
            )

        return like


class AnswerLikeForm(forms.ModelForm):
    class Meta:
        model = AnswerLike
        fields = ("value",)

    def __init__(self, *args, user=None, answer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.answer = answer

    def clean(self):
        cleaned_data = super().clean()

        if self.user is None or not self.user.is_authenticated:
            raise forms.ValidationError(
                "Log in to vote."
            )

        if self.answer is None:
            raise forms.ValidationError(
                "Answer is required."
            )

        if AnswerLike.objects.filter(
            user=self.user,
            answer=self.answer,
        ).exists():
            raise forms.ValidationError(
                "You have already voted for this answer."
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        like = super().save(commit=False)
        like.user = self.user
        like.answer = self.answer

        if commit:
            like.save()
            Answer.objects.filter(
                pk=self.answer.pk
            ).update(
                rating=F("rating") + like.value
            )

        return like


class CorrectAnswerForm(forms.ModelForm):
    is_correct = forms.TypedChoiceField(
        choices=(
            ("true", "Correct"),
            ("false", "Not correct"),
        ),
        coerce=lambda value: value == "true",
        label="Correct answer",
    )

    class Meta:
        model = Answer
        fields = ("is_correct",)

    def __init__(self, *args, user=None, answer=None, **kwargs):
        if answer is not None:
            kwargs["instance"] = answer

        super().__init__(*args, **kwargs)

        self.user = user
        self.answer = answer

    def clean(self):
        cleaned_data = super().clean()

        if self.answer is None:
            raise forms.ValidationError(
                "Answer is required."
            )

        question_id = self.data.get("question_id")

        if not question_id or str(self.answer.question_id) != str(question_id):
            raise forms.ValidationError(
                "Answer does not belong to the specified question."
            )

        if self.user is None or not self.user.is_authenticated:
            raise forms.ValidationError(
                "Log in to mark correct answers."
            )

        if self.answer.question.author_id != self.user.pk:
            raise forms.ValidationError(
                "Only the question author can mark correct answers."
            )

        return cleaned_data