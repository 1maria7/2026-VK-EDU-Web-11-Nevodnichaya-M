
from django.contrib import admin

from .models import (
    Answer,
    AnswerLike,
    Question,
    QuestionLike,
    Tag,
)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ("author",)
    show_change_link = True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "author",
        "rating",
        "answers_count",
        "created_at",
    )
    search_fields = ("title", "text", "author__username")
    list_filter = ("created_at",)
    list_select_related = ("author",)
    raw_id_fields = ("author", "tags")
    inlines = (AnswerInline,)


class TagFirstLetterFilter(admin.SimpleListFilter):
    title = "Первая буква"
    parameter_name = "letter"

    def lookups(self, request, model_admin):
        return [(letter, letter.upper()) for letter in "abcdefghijklmnopqrstuvwxyz"]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__istartswith=self.value())
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    list_filter = (TagFirstLetterFilter,)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "author",
        "rating",
        "is_correct",
        "created_at",
    )
    search_fields = (
        "text",
        "question__title",
        "author__username",
    )
    list_filter = ("is_correct", "created_at")
    list_select_related = ("question", "author")
    raw_id_fields = ("question", "author")


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "value")
    search_fields = ("user__username", "question__title")
    list_filter = ("value",)
    list_select_related = ("user", "question")
    raw_id_fields = ("user", "question")


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "answer", "value")
    search_fields = ("user__username", "answer__text")
    list_filter = ("value",)
    list_select_related = ("user", "answer")
    raw_id_fields = ("user", "answer")
