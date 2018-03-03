from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpRequest
from django.contrib.auth.models import User


# Create your views here.
class InitialSetupView(TemplateView):
    template_name = "initial.html"

    def get(self, request):
        return render(request, 'initial.html', {})

    def post(self, request):
        # Basic validation
        if len(request.POST['username']) == 0:
            return render(request, 'initial.html', {'error_rejection': 'username must be specified'})
        if len(request.POST['password']) == 0:
            return render(request, 'initial.html', {'error_rejection': 'password must be specified'})
        if len(request.POST['email']) == 0:
            return render(request, 'initial.html', {'error_rejection': 'email must be specified'})

        # Check that we're not already configured
        super_users = User.objects.filter(is_superuser=True)
        if super_users.count() > 0:
            return render(request, 'initial.html', {'error_rejection': 'application already configured'})

        # Read the form variables
        username = request.POST['username']
        email = request.POST['password']
        password = request.POST['password']

        # Do some additional password validation
        if len(password) < 8:
            return render(request, 'initial.html', {'error_rejection': 'password is too short'})

        # Create the super-user
        User.objects.create_superuser(username=username, email=email, password=password)

        if super_users.count() > 0:
            return render(request, 'initial.html', {'success': True})


class IndexView(TemplateView):
    template_name = 'index.html'
