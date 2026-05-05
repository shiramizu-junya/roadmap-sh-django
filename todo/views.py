from django.shortcuts import render, redirect
from .models import Task


def task_list(request):
    """タスク一覧を表示する。"""
    tasks = Task.objects.all().order_by("-created_at")
    return render(request, "todo/list.html", {"tasks": tasks})


def task_create(request):
    """新規タスクを作成する。"""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            Task.objects.create(title=title)
    return redirect("task_list")


def task_toggle(request, task_id):
    """タスクの完了状態をトグル。"""
    task = Task.objects.get(pk=task_id)
    task.is_done = not task.is_done
    task.save()
    return redirect("task_list")
