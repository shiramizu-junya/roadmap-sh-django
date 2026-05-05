from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def detail(request, question_id):
    return HttpResponse(f"You're looking at question {question_id}.")


def results(request, question_id):
    return HttpResponse(f"You're looking at the results of question {question_id}.")


def vote(request, question_id):
    return HttpResponseRedirect(reverse("polls:results", args=(question_id,)))
