
from django.conf import settings
from django.db import models
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "questions:tag",
            kwargs={"tag_name": self.name},
        )


class QuestionManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("author", "author__profile")
            .prefetch_related("tags")
        )


    def newest(self):
        return self.get_queryset().order_by(
            "-created_at", "-id"
        )

    def hot(self):
        return self.get_queryset().order_by(
            "-rating", "-created_at", "-id"
        )

    def by_tag(self, tag_name):
        return (
            self.get_queryset()
            .filter(tags__name=tag_name)
            .order_by("-created_at", "-id")
        )


class Question(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
    )
    text = models.TextField(
        verbose_name="Текст вопроса",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Автор",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="questions",
        blank=True,
        verbose_name="Теги",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата создания",
    )
    rating = models.IntegerField(
        default=0,
        verbose_name="Рейтинг",
    )
    answers_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество ответов",
    )

    objects = QuestionManager()

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        indexes = [
            models.Index(
                fields=["-rating", "-created_at"],
                name="question_hot_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "questions:question",
            kwargs={"question_id": self.pk},
        )


class AnswerManager(models.Manager):
    def for_question(self, question):
        return (
            self.get_queryset()
            .filter(question=question)
            .select_related("author", "author__profile")
            .order_by("created_at", "id")
        )

class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Автор",
    )
    text = models.TextField(
        verbose_name="Текст ответа",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата создания",
    )
    rating = models.IntegerField(
        default=0,
        verbose_name="Рейтинг",
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Правильный ответ",
    )
    objects = AnswerManager()
    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ №{self.pk} к вопросу №{self.question_id}"


class QuestionLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_likes",
        verbose_name="Пользователь",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Вопрос",
    )
    value = models.SmallIntegerField(
        choices=[
            (1, "Лайк"),
            (-1, "Дизлайк"),
        ],
        verbose_name="Оценка",
    )

    class Meta:
        verbose_name = "Оценка вопроса"
        verbose_name_plural = "Оценки вопросов"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question"],
                name="unique_question_like",
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="valid_question_like_value",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}: {self.question_id} ({self.value})"


class AnswerLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answer_likes",
        verbose_name="Пользователь",
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Ответ",
    )
    value = models.SmallIntegerField(
        choices=[
            (1, "Лайк"),
            (-1, "Дизлайк"),
        ],
        verbose_name="Оценка",
    )

    class Meta:
        verbose_name = "Оценка ответа"
        verbose_name_plural = "Оценки ответов"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "answer"],
                name="unique_answer_like",
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="valid_answer_like_value",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}: {self.answer_id} ({self.value})"