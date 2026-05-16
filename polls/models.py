import datetime
from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField("質問文", max_length=200)
    pub_date = models.DateTimeField("公開日時")
    cover_image = models.ImageField(
        upload_to="polls/covers/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "質問"
        verbose_name_plural = "質問"

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        """公開日時が現在から1日以内の質問に対して True を返す。"""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    choice_text = models.CharField("選択肢", max_length=200)
    votes = models.IntegerField("投票数", default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "選択肢"
        verbose_name_plural = "選択肢"

    def __str__(self):
        return self.choice_text
