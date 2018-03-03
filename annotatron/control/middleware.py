from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse


class MissingSuperUserMiddleware:
    """
        This middleware checks if Annotatron has been configured.
        If it hasn't, then redirect to a screen where we can setup
        the system.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):

        if "/control/" not in request.get_raw_uri():
            superusers = User.objects.filter(is_superuser=True)
            if superusers.count() == 0:
                return HttpResponseRedirect(reverse('control-setup'))

        return self.get_response(request)
