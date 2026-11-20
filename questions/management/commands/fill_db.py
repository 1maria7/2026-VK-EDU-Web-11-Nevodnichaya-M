
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from core.models import Profile
from questions.models import (
    Answer,
    AnswerLike,
    Question,
    QuestionLike,
    Tag,
)


BATCH_SIZE = 1000
ANSWERS_PER_QUESTION = 10

class Command(BaseCommand):
    help = "Fill the database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "ratio",
            type=int,
            help="Data generation ratio",
        )

    def handle(self, *args, **options):
        ratio = options["ratio"]

        if ratio <= 0:
            raise CommandError(
                "Ratio must be a positive integer."
            )
        if ratio == 1:
            raise CommandError(
                "At least 2 users are required to generate "
                "200 unique ratings for 110 objects."
            )

        fake = Faker("en_US")
        User = get_user_model()
        run_id = uuid4().hex[:12]

        user_ids = []
        tag_ids = []

        # Generate users and profiles
        for start in range(0, ratio, BATCH_SIZE):
            users = []

            for number in range(
                start, min(start + BATCH_SIZE, ratio)
            ):
                username = f"test_{run_id}_{number}"

                user = User(
                    username=username,
                    email=f"{username}@example.com",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                )
                user.set_unusable_password()
                users.append(user)

            with transaction.atomic():
                User.objects.bulk_create(
                    users,
                    batch_size=BATCH_SIZE,
                )

                profiles = [
                    Profile(user_id=user.pk)
                    for user in users
                ]

                Profile.objects.bulk_create(
                    profiles,
                    batch_size=BATCH_SIZE,
                )

            user_ids.extend(user.pk for user in users)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(user_ids)} users and profiles."
            )
        )

        # Generate tags
        for start in range(0, ratio, BATCH_SIZE):
            tags = []

            for number in range(
                start, min(start + BATCH_SIZE, ratio)
            ):
                tag_name = (
                    f"{fake.word()[:18]}_{run_id}_{number}"
                )
                tags.append(Tag(name=tag_name))

            Tag.objects.bulk_create(
                tags,
                batch_size=BATCH_SIZE,
            )

            tag_ids.extend(tag.pk for tag in tags)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(tag_ids)} tags."
            )
        )
        question_count = ratio * 10
        created_questions = 0
        created_answers = 0
        created_likes = 0

        QuestionTag = Question.tags.through

        for start in range(0, question_count, BATCH_SIZE):
            questions = []

            for number in range(
                start,
                min(start + BATCH_SIZE, question_count),
            ):
                question = Question(
                    title=fake.sentence(nb_words=6)[:200],
                    text=fake.paragraph(nb_sentences=5),
                    author_id=user_ids[
                        (number // 10) % len(user_ids)
                    ],
                    rating=1 if number % 2 == 0 else -1,
                    answers_count=ANSWERS_PER_QUESTION,
                )
                questions.append(question)

            with transaction.atomic():
                Question.objects.bulk_create(
                    questions,
                    batch_size=BATCH_SIZE,
                )

                question_tags = []

                for number, question in enumerate(
                    questions, start=start
                ):
                    question_tags.append(
                        QuestionTag(
                            question_id=question.pk,
                            tag_id=tag_ids[
                                number % len(tag_ids)
                            ],
                        )
                    )

                QuestionTag.objects.bulk_create(
                    question_tags,
                    batch_size=BATCH_SIZE,
                )
                answers = []

                for question in questions:
                    for answer_number in range(ANSWERS_PER_QUESTION):
                        answer = Answer(
                            question_id=question.pk,
                            author_id=user_ids[
                                (question.pk + answer_number)
                                % len(user_ids)
                            ],
                            text=fake.paragraph(nb_sentences=3),
                            rating=(
                                1 if answer_number == 0
                                else 2 if answer_number % 2 else 0
                            ),
                            is_correct=(answer_number == 0),
                        )
                        answers.append(answer)

                Answer.objects.bulk_create(
                    answers,
                    batch_size=BATCH_SIZE,
                )
                # Generate question likes
                question_likes = []

                for number, question in enumerate(
                    questions, start=start
                ):
                    question_likes.append(
                        QuestionLike(
                            user_id=user_ids[
                                number % len(user_ids)
                            ],
                            question_id=question.pk,
                            value=question.rating,
                        )
                    )

                QuestionLike.objects.bulk_create(
                    question_likes,
                    batch_size=BATCH_SIZE,
                )

                # лайки
                answer_likes = []

                for index, answer in enumerate(answers):
                    question_offset, answer_number = divmod(
                        index, ANSWERS_PER_QUESTION
                    )

                    first_user_index = (
                        start + question_offset + answer_number
                    ) % len(user_ids)

                    answer_likes.append(
                        AnswerLike(
                            user_id=user_ids[first_user_index],
                            answer_id=answer.pk,
                            value=1,
                        )
                    )

                    if answer_number != 0:
                        second_user_index = (
                            first_user_index + 1
                        ) % len(user_ids)

                        answer_likes.append(
                            AnswerLike(
                                user_id=user_ids[second_user_index],
                                answer_id=answer.pk,
                                value=(
                                    1 if answer_number % 2 else -1
                                ),
                            )
                        )

                AnswerLike.objects.bulk_create(
                    answer_likes,
                    batch_size=BATCH_SIZE,
                )

            created_questions += len(questions)
            created_answers += len(answers)
            created_likes += len(question_likes) + len(answer_likes)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_questions} questions."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_answers} answers."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_likes} likes."
            )
        )