from django.shortcuts import render

# Create your views here.
from rest_framework import serializers, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from .models import Corpus


class CorpusSerializer(serializers.ModelSerializer):
    """
        Used for converting, creating and updating corpora.
    """
    class Meta:
        model = Corpus
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
