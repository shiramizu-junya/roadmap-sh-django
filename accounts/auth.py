from django.contrib import auth
from ninja.security import HttpBasicAuth


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        return auth.authenticate(request, username=username, password=password)
