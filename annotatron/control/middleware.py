from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings


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
                return HttpResponseRedirect(reverse('setup-user'))

        return self.get_response(request)


class MissingFaasMiddleWare:
    """
        This middleware checks if Annotatron has a connection to OpenFaaS set up.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if "/control/setup/faas" not in request.get_raw_uri():
            try:
                if settings.OPENFAAS_URL is None:
                    return HttpResponseRedirect(reverse('setup-faas'))
            except AttributeError:
                return HttpResponseRedirect(reverse('setup-faas'))

        return self.get_response(request)


class DisableCSRFForDRFMiddleWare(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if "/v1/" in request.get_raw_uri():
            setattr(request, '_dont_enforce_csrf_checks', True)

        return self.get_response(request)