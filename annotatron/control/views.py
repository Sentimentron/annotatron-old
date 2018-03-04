from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpRequest
from django.contrib.auth.models import User
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

import base64

from .models import Asset, Corpus


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


class Base64Field(serializers.Field):
    """
        Decodes binary data held in a Base64 encoded string.
    """
    def to_representation(self, value):
        return base64.standard_b64encode(value).decode("utf8")

    def to_internal_value(self, data):
        return base64.standard_b64decode(data)


class AssetSerializer(serializers.ModelSerializer):
    """
        Converts an asset into something that can be safely handled.
    """

    content = Base64Field(source='binary_content')

    class Meta:
        model = Asset
        fields = ('unique_id', 'kind', 'mime_type', 'content')


class CorpusSerializer(serializers.ModelSerializer):
    """
        Used for converting, creating and updating corpora.
    """
    class Meta:
        model = Corpus


class AssetView(generics.ListCreateAPIView):
    """
        This is an API view which processes and handles assets.
    """
    serializer_class = AssetSerializer

    def get_queryset(self):
        corpus_raw = self.request.query_params.get('corpus', None)
        corpus = Corpus.objects.get(name=corpus_raw)
        queryset = Corpus.objects.filter(corpus=corpus)
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        serializer = AssetSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, corpus, request):
        serializer = AssetSerializer(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            data = {
                "errors": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CorpusView(generics.ListCreateAPIView):
    """
        This view allows the programmatic creation of things.
    """
    queryset = Corpus.objects.all()
    serializer_class = CorpusSerializer


class DebugAssetView(APIView):
    """
        This is a debug view (intended for use with unit testing) which
        DELETES ALL OF THE ASSETS IN THE DATABASE.
    """

    def post(self, request):
        assets = Asset.objects.all()
        assets.delete()
        return Response({})


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
