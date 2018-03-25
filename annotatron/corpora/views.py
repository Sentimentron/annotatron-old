import base64
import string

from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from .models import Corpus, Asset, Annotation, Annotator, ANNOTATION_SOURCES


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


class AnnotationSerializer(serializers.ModelSerializer):
    """
        Used for creating new Annotations.
    """

    class Meta:
        model = Annotation
        fields = "__all__"


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
        fields = ('name', 'kind', 'mime_type', 'content', 'corpus', 'metadata', 'sha_512_sum')


class AssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Asset
        fields = ('name', 'kind', 'mime_type')


class AssetView(APIView):
    """
        This is an API view which processes and handles assets.
    """

    def get(self, request, corpus=None, asset=None):
        queryset = Corpus.objects.get(name=corpus).assets
        if asset:
            queryset = queryset.get(name=asset)
        serializer = AssetSerializer(queryset, many=asset is None)
        return Response(serializer.data)

    def post(self, request, corpus=None, asset=None):
        corpus = Corpus.objects.get(name=corpus)
        request.data["corpus"] = corpus.id
        if asset:
            request.data["name"] = asset
        serializer = AssetUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            data = {
                "errors": serializer.errors
            }
            return Response(data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AssetCheckView(APIView):
    """
        This is used to check whether the Asset has already been uploaded.
    """
    def post(self, request, corpus):
        corpus = Corpus.objects.get(name=corpus)
        request.data["corpus"] = corpus.id
        serializer = AssetUploadSerializer(data=request.data)
        if serializer.is_valid():
            binary_assets = Asset.objects.filter(corpus=corpus).filter(sha_512_sum=serializer.validated_data["sha_512_sum"])
            data = {
                "matching_checksums": binary_assets.count(),
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                "errors": serializer.errors
            }
            return Response(data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AssetContentView(APIView):
    """
        This returns the raw content of the request (without base64 encoding).
    """

    def get(self, request, corpus, asset):
        try:
            asset_obj = Corpus.objects.get(name=corpus).assets.get(name=asset)
        except Corpus.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        except Asset.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


        return HttpResponse(asset_obj.binary_content, content_type=asset_obj.mime_type)


class AnnotationCreateListView(APIView):
    """
        This view returns a list of active annotations, or creates a new one.
    """

    def get(self, request, corpus, asset):

        try:
            asset_obj = Corpus.objects.get(name=corpus).assets.get(name=asset)
        except Corpus.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        except Asset.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        # TODO: I kind of hoped to be able to a GROUP BY to do this, but I can't figure out how to do it with
        # Django's ORM.
        annotations = asset_obj.annotations
        ret = {}
        for _id, human in ANNOTATION_SOURCES:
            category = annotations.filter(source=_id)
            if category.count() > 0:
                ret[human] = {}
                for obj in category:
                    if obj.summary_code not in ret:
                        ret[human][obj.summary_code] = []
                    ret[human][obj.summary_code].append(obj)

        for human in ret:
            for summary_code in ret[human]:
                serializer = AnnotationSerializer(ret[human][summary_code], many=True)
                ret[human][summary_code] = serializer.data

        return Response(ret, status=status.HTTP_200_OK)

    def post(self, request, corpus, asset):

        # Check whether we have an Annotator record for this user
        annotator, _ = Annotator.objects.get_or_create(external=request.user)

        # Locate the asset
        corpus_obj = Corpus.objects.get(name=corpus)
        asset_obj = Asset.objects.filter(corpus=corpus_obj).get(name=asset)

        # Augment the request with additional data
        request.data["asset"] = asset_obj.id
        request.data["annotator"] = annotator.id

        # Change the source from a human-readable description into the database field
        for _id, human in ANNOTATION_SOURCES:
            if request.data["source"] == human:
                request.data["source"] = _id

        serializer = AnnotationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            data = {
                "errors": serializer.errors
            }
            return Response(data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DebugRemoveAssetsView(APIView):
    """
        This is a debug view (intended for use with unit testing) which
        DELETES ALL OF THE ASSETS IN THE DATABASE with 'debug-' at the start.
    """

    def post(self, request):
        assets = Asset.objects.filter(name__startswith='debug-')
        assets.delete()
        return Response({})