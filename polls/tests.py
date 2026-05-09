from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question


def create_question(question_text: str, days: int) -> Question:
    """days 日後（負なら過去）の公開日時で質問を作成。"""
    return Question.objects.create(
        question_text=question_text,
        pub_date=timezone.now() + timedelta(days=days),
    )


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """ was_published_recently() は公開日時が未来の質問に対して False を返すべき。"""
        future_question = Question(pub_date=timezone.now() + timedelta(days=30))
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """ was_published_recently() は公開日時が1日より前の質問に対して False を返すべき。"""
        old_question = Question(pub_date=timezone.now() - timedelta(days=1, seconds=1))
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """ was_published_recently() は公開日時が現在から1日以内の質問に対して True を返すべき。"""
        recent = Question(pub_date=timezone.now() - timedelta(hours=23, minutes=59))
        self.assertIs(recent.was_published_recently(), True)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "まだ質問はありません。")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question_is_displayed(self):
        question = create_question("過去の質問", days=-1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [question])

    def test_future_question_is_not_displayed(self):
        create_question("未来の質問", days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "まだ質問はありません。")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_only_past_when_both_exist(self):
        past = create_question("過去", days=-1)
        create_question("未来", days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(response.context["latest_question_list"], [past])


class QuestionDetailViewTests(TestCase):
    def test_future_question_returns_404(self):
        future = create_question("未来", days=5)
        response = self.client.get(reverse("polls:detail", args=(future.id,)))
        self.assertEqual(response.status_code, 404)

    def test_past_question_is_displayed(self):
        past = create_question("過去", days=-1)
        response = self.client.get(reverse("polls:detail", args=(past.id,)))
        self.assertContains(response, past.question_text)
