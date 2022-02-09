from rest_framework import generics
from ..models import Space
from .serializers import SpaceSerializer


class SpaceListView(generics.ListAPIView):
    queryset = Space.objects.all()[:10]
    serializer_class = SpaceSerializer


class SpaceDetailView(generics.ListAPIView):
    queryset = Space.objects.all()
    serializer_class = SpaceSerializer
