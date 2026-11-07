from django.http import Http404
from django.shortcuts import render
from core.pagination import paginate
QUESTIONS = []
for number in range(1, 36):
    QUESTIONS.append(
        {
            "id": number,
            "title": f"How to build a moon park? #{number}",
            "text": (
                "Guys, I have a problem with a moon park. "
                "Cannot find black-jack..."
            ),
            "rating": number % 10,
            "answers_count": 4,
            "tags": ["black-jack", "bender"],
            "author_avatar": "core/img/avatar.png"
        }
    )
def index(request):
    questions = sorted(
        QUESTIONS,
        key=lambda question: question["id"],
        reverse=True,
    )

    page_obj = paginate(questions, request)

    return render(
        request,
        "questions/index.html",
        {
            "questions": page_obj.object_list,
            "page_obj": page_obj,
        },
    )


def hot(request):
    questions = sorted(
        QUESTIONS,
        key=lambda question: (
            question["rating"],
            question["id"],
        ),
        reverse=True,
    )

    page_obj = paginate(questions, request)

    return render(
        request,
        "questions/hot.html",
        {
            "questions": page_obj.object_list,
            "page_obj": page_obj,
        },
    )
def tag(request, tag_name):
    questions = []

    for question in QUESTIONS:
        if tag_name in question["tags"]:
            questions.append(question)

    questions = sorted(
        questions,
        key=lambda question: question["id"],
        reverse=True,
    )

    page_obj = paginate(questions, request)

    return render(
        request,
        "questions/tag.html",
        {
            "questions": page_obj.object_list,
            "page_obj": page_obj,
            "tag_name": tag_name,
        },
    )
def question(request, question_id):
    question_data = None

    for item in QUESTIONS:
        if item["id"] == question_id:
            question_data = item
            break

    if question_data is None:
        raise Http404("Вопрос не найден")

    answers = []

    for number in range(1, question_data["answers_count"] + 1):
        answers.append(
            {
                "id": number,
                "text": (
                    f"Answer #{number} to question #{question_id}. "
                    "Start with a small working example "
                    "and check the documentation."
                ),
                "rating": 5,
                "author_avatar": "core/img/avatar.png",
            }
        )

    page_obj = paginate(answers, request, per_page=3)

    return render(
        request,
        "questions/question.html",
        {
            "question": question_data,
            "answers": page_obj.object_list,
            "page_obj": page_obj,
        },
    )
def ask(request):
    return render(request, "questions/ask.html")