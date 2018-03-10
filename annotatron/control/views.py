from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny


class RequiresSetupView(APIView):
    """
    This API is called by the front-end code to determine if we need
    to go through initial configuration.
    """

    permission_classes = (AllowAny,)

    def get(self, request):
        superusers = User.objects.filter(is_superuser=True)
        return Response({
            "requires_setup": superusers.count() == 0
        })

    def post(self, request):
        allowed = User.objects.filter(is_superuser=True).count() == 0
        if allowed:
            serializer = DebugUserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.create()
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "errors": serializer.errors(),
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class DebugUserSerializer(serializers.Serializer):
    """
        Debug-only serializer which programmatically creates
        new users (intended for unit testing).
    """

    username = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    is_superuser = serializers.BooleanField(required=True)
    is_staff = serializers.BooleanField(required=True)

    def create(self, validated_data):
        if validated_data['is_superuser']:
            return User.objects.create_superuser(**validated_data)

        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError()


class DebugUserCreateView(generics.ListCreateAPIView):
    """
        This is a debug view which programmatically creates new users.
    """

    queryset = User.objects.all()
    serializer_class = DebugUserSerializer


class DebugUserDeleteView(APIView):
    """
        Removes any users with "debug-" in front of their name.
    """
    def post(self, request):
        User.objects.filter(username__startswith="debug-").delete()
        return Response()

    def get(self, request):
        User.objects.filter(username__startswith="debug-").delete()
        return Response()


class DebugSayHelloAPIView(APIView):

    """
        Used to check that authentication is working.
    """
    permission_classes = (IsAdminUser,)

    def post(self, request):
        return Response({"hello": "world"})


class InitialSetupUserView(TemplateView):
    """
        This view prompts for the user to create an admin password.
    """
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
        email = request.POST['email']
        password = request.POST['password']

        # Do some additional password validation
        if len(password) < 8:
            return render(request, 'initial.html', {'error_rejection': 'password is too short'})

        # Create the super-user
        User.objects.create_superuser(username=username, email=email, password=password)

        if super_users.count() > 0:
            return render(request, 'initial.html', {'success': True})


class InitialSetupFaasView(TemplateView):
    template_name = 'faas.html'


class IndexView(TemplateView):
    template_name = 'index.html'
