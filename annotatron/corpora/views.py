import base64
import string

from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from .models import Corpus, Asset


class CorpusSerializer(serializers.ModelSerializer):
    """
        Used for converting, creating and updating corpora.
    """
    class Meta:
        model = Corpus
        fields = "__all__"

    def validate_name(self, value):
        valid_set = set(string.ascii_letters + '0123456789' + '_' + '-')
        seen_set = set(value)
        if len(seen_set.difference(valid_set)) > 0:
            raise serializers.ValidationError("name: should only consist of alpha-numeric letters, underscores, "
                                              "and dashes (got: '{}')".format(value))
        return value


class CorpusView(generics.ListCreateAPIView):
    """
        This view allows the programmatic creation of things.
    """
    permission_classes = (IsAdminUser,)
    queryset = Corpus.objects.all()
    serializer_class = CorpusSerializer


class DebugRemoveCorporaView(APIView):
    """
        This is a debug view which removes all corpora starting with 'debug-'
    """
    permission_classes = (IsAdminUser,)

    def post(self, request):
        Corpus.objects.filter(name__startswith='debug-').delete()
        return Response(200)


class Base64Field(serializers.Field):
    """
        Decodes binary data held in a Base64 encoded string.
    """
    def to_representation(self, value):
        return base64.standard_b64encode(value).decode("utf8")

    def to_internal_value(self, data):
        return base64.standard_b64decode(data)


class AssetUploadSerializer(serializers.ModelSerializer):
    """
        Converts an asset into something that can be safely handled.
    """

    content = Base64Field(source='binary_content')

    def validate_name(self, value):
        valid_set = set(string.ascii_letters + '0123456789' + '_' + '-')
        seen_set = set(value)
        if len(seen_set.difference(valid_set)) > 0:
            raise serializers.ValidationError("name: should only consist of alpha-numeric letters, underscores, "
                                              "dashes, slashes (got: '{}')".format(value))
        return value

    class Meta:
        model = Asset
        fields = ('name', 'kind', 'mime_type', 'content', 'corpus')


class AssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Asset
        fields = ('name', 'kind', 'mime_type')


class AssetView(APIView):
    """
        This is an API view which processes and handles assets.
    """

    def get(self, request, corpus=None):
        queryset = Corpus.objects.get(name=corpus).assets
        serializer = AssetSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, corpus=None):
        corpus = Corpus.objects.get(name=corpus)
        request.data["corpus"] = corpus.id
        serializer = AssetUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            data = {
                "errors": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class AssetContentView(APIView):
    """
        This returns the raw content of the request (without base64 encoding).
    """

    def get(self, request, corpus, asset):
        object = Corpus.objects.get(name=corpus).assets.get(name=asset)
        serializer = AssetUploadSerializer(object)
        #return Response(serializer.data)

        return HttpResponse(object.binary_content, content_type=object.mime_type)
        #return Response(object.binary_content, content_type=object.mime_type)

class DebugRemoveAssetsView(APIView):
    """
        This is a debug view (intended for use with unit testing) which
        DELETES ALL OF THE ASSETS IN THE DATABASE with 'debug-' at the start.
    """

    def post(self, request):
        assets = Asset.objects.filter(name__startswith='debug-')
        assets.delete()
        return Response({})