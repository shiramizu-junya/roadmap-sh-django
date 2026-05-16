from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Question, Choice


def index(request):
    """直近に公開された質問を最大 5 件表示。"""
    latest_question_list = Question.objects.filter(
        pub_date__lte=timezone.now()
    ).order_by("-pub_date")[:5]
    return render(
        request,
        "polls/index.html",
        {"latest_question_list": latest_question_list},
    )


def detail(request, question_id):
    """質問の詳細と投票フォーム。"""
    question = get_object_or_404(
        Question.objects.filter(pub_date__lte=timezone.now()),
        pk=question_id,
    )
    return render(request, "polls/detail.html", {"question": question})


def results(request, question_id):
    """投票結果。"""
    question = get_object_or_404(Question, pk=question_id)
    other_questions = Question.objects.exclude(pk=question_id).order_by("-pub_date")[:3]
    return render(
        request,
        "polls/results.html",
        {"question": question, "other_questions": other_questions},
    )


def vote(request, question_id):
    """投票を受け付ける。POST 専用想定。"""
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choices.get(pk=request.POST["choice"])
    except KeyError, Choice.DoesNotExist:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "選択肢を選んでください。",
            },
        )
    selected_choice.votes += 1
    selected_choice.save()
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


def whoami(request):
    """リクエスト内容を JSON で返すデバッグ用ビュー。"""
    return JsonResponse(
        {
            "method": request.method,
            "path": request.path,
            "full_path": request.get_full_path(),
            "host": request.get_host(),
            "is_secure": request.is_secure(),
            "user_agent": request.headers.get("User-Agent", ""),
            "remote_addr": request.META.get("REMOTE_ADDR", ""),
            "query_params": dict(request.GET),
            "cookies": dict(request.COOKIES),
            "user_authenticated": request.user.is_authenticated,
            "session_key": request.session.session_key,
        }
    )


def response_demo(request):
    """?type=json / ?type=redirect / ?type=404 で挙動が変わる。"""
    response_type = request.GET.get("type", "html")

    if response_type == "json":
        return JsonResponse({"hello": "world", "items": [1, 2, 3]})

    if response_type == "redirect":
        return HttpResponseRedirect("/polls/")

    if response_type == "404":
        return HttpResponseNotFound("見つかりません")

    # デフォルト: HTML
    response = HttpResponse("<h1>Hello</h1>")
    response["X-Demo-Header"] = "yes"
    response.set_cookie("demo", "on", max_age=60)
    return response
