from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.csrf import csrf_failure as default_csrf_failure

from core.pagination import paginate

from .forms import AnswerForm, AnswerLikeForm, CorrectAnswerForm, QuestionForm, QuestionLikeForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag

def add_vote_state(objects, user, like_model, target_field):
    objects = list(objects)

    for obj in objects:
        obj.user_vote = None

    if not user.is_authenticated or not objects:
        return objects

    object_ids = [obj.pk for obj in objects]

    votes = dict(
        like_model.objects.filter(
            user=user,
            **{f"{target_field}_id__in": object_ids},
        ).values_list(
            f"{target_field}_id",
            "value",
        )
    )

    for obj in objects:
        obj.user_vote = votes.get(obj.pk)
    return objects

def index(request):
    page_obj = paginate(Question.objects.newest(), request)

    return render(request, "questions/index.html", {
        "questions": add_vote_state(
            page_obj.object_list,
            request.user,
            QuestionLike,
            "question",
        ),
        "page_obj": page_obj,
    })


def hot(request):
    page_obj = paginate(Question.objects.hot(), request)

    return render(request, "questions/hot.html", {
        "questions": add_vote_state(
            page_obj.object_list,
            request.user,
            QuestionLike,
            "question",
        ),
        "page_obj": page_obj,
    })


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)

    page_obj = paginate(
        Question.objects.by_tag(tag_obj.name),
        request,
    )

    return render(request, "questions/tag.html", {
        "questions": add_vote_state(
            page_obj.object_list,
            request.user,
            QuestionLike,
            "question",
        ),
        "page_obj": page_obj,
        "tag_name": tag_obj.name,
    })


def question(request, question_id):
    question_obj = get_object_or_404(
        Question,
        pk=question_id,
    )

    if request.method == "POST" and not request.user.is_authenticated:
        return redirect_to_login(
            request.get_full_path(),
            login_url="core:login",
        )

    answer_form = AnswerForm(
        request.POST if request.method == "POST" else None,
        question=question_obj,
        author=request.user,
    )

    if request.method == "POST" and answer_form.is_valid():
        answer = answer_form.save()

        answer_position = Answer.objects.filter(
            question=question_obj,
        ).filter(
            Q(created_at__lt=answer.created_at)
            | Q(
                created_at=answer.created_at,
                pk__lte=answer.pk,
            )
        ).count()

        page_number = (answer_position - 1) // 3 + 1

        return redirect(
            f"{question_obj.get_absolute_url()}"
            f"?page={page_number}#answer-{answer.pk}"
        )

    page_obj = paginate(
        Answer.objects.for_question(question_obj),
        request,
        per_page=3,
    )

    add_vote_state(
        [question_obj],
        request.user,
        QuestionLike,
        "question",
    )

    return render(request, "questions/question.html", {
        "question": question_obj,
        "answers": add_vote_state(
            page_obj.object_list,
            request.user,
            AnswerLike,
            "answer",
        ),
        "page_obj": page_obj,
        "answer_form": answer_form,
    })


@login_required(login_url="core:login")
def ask(request):
    form = QuestionForm(
        request.POST if request.method == "POST" else None,
        author=request.user,
    )

    if request.method == "POST" and form.is_valid():
        question = form.save()
        return redirect(question.get_absolute_url())

    return render(request, "questions/ask.html", {
        "form": form,
    })


def vote_question(request, question_id):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Log in to vote."},
            status=401,
        )

    question_obj = get_object_or_404(
        Question,
        pk=question_id,
    )

    form = QuestionLikeForm(
        request.POST,
        user=request.user,
        question=question_obj,
    )

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    try:
        form.save()
    except IntegrityError:
        return JsonResponse(
            {
                "error": (
                    "You have already voted "
                    "for this question."
                )
            },
            status=409,
        )

    question_obj.refresh_from_db(fields=["rating"])

    return JsonResponse({
        "rating": question_obj.rating,
    })


def vote_answer(request, answer_id):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Log in to vote."},
            status=401,
        )

    answer_obj = get_object_or_404(
        Answer,
        pk=answer_id,
    )

    form = AnswerLikeForm(
        request.POST,
        user=request.user,
        answer=answer_obj,
    )

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    try:
        form.save()
    except IntegrityError:
        return JsonResponse(
            {
                "error": (
                    "You have already voted "
                    "for this answer."
                )
            },
            status=409,
        )

    answer_obj.refresh_from_db(fields=["rating"])

    return JsonResponse({
        "rating": answer_obj.rating,
    })


def set_correct_answer(request, answer_id):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Log in to mark correct answers."},
            status=401,
        )

    answer_obj = get_object_or_404(
        Answer.objects.select_related("question"),
        pk=answer_id,
    )

    if answer_obj.question.author_id != request.user.pk:
        return JsonResponse(
            {
                "error": (
                    "Only the question author "
                    "can mark correct answers."
                )
            },
            status=403,
        )

    form = CorrectAnswerForm(
        request.POST,
        user=request.user,
        answer=answer_obj,
    )

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    answer = form.save()

    return JsonResponse({
        "answer_id": answer.pk,
        "is_correct": answer.is_correct,
    })


def csrf_failure(request, reason=""):
    ajax_views = {
        "questions:vote_question",
        "questions:vote_answer",
        "questions:set_correct_answer",
    }

    resolver_match = getattr(
        request,
        "resolver_match",
        None,
    )

    if resolver_match and resolver_match.view_name in ajax_views:
        return JsonResponse(
            {
                "error": (
                    "CSRF verification failed. "
                    "Refresh the page and try again."
                )
            },
            status=403,
        )

    return default_csrf_failure(
        request,
        reason=reason,
    )
