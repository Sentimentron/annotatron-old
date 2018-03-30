from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings


class DisableCSRFForDRFMiddleWare(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if "/v1/" in request.get_raw_uri():
            setattr(request, '_dont_enforce_csrf_checks', True)

        return self.get_response(request)