
from django.shortcuts import get_object_or_404, render

from core.pagination import paginate
from .models import Answer, Question, Tag


def index(request):
    page_obj = paginate(Question.objects.newest(), request)

    return render(request, "questions/index.html", {
        "questions": page_obj.object_list,
        "page_obj": page_obj,
    })


def hot(request):
    page_obj = paginate(Question.objects.hot(), request)

    return render(request, "questions/hot.html", {
        "questions": page_obj.object_list,
        "page_obj": page_obj,
    })


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    page_obj = paginate(
        Question.objects.by_tag(tag_obj.name), request
    )

    return render(request, "questions/tag.html", {
        "questions": page_obj.object_list,
        "page_obj": page_obj,
        "tag_name": tag_obj.name,
    })


def question(request, question_id):
    question_obj = get_object_or_404(Question, pk=question_id)
    page_obj = paginate(
        Answer.objects.for_question(question_obj),
        request,
        per_page=3,
    )

    return render(request, "questions/question.html", {
        "question": question_obj,
        "answers": page_obj.object_list,
        "page_obj": page_obj,
    })


def ask(request):
    return render(request, "questions/ask.html")
