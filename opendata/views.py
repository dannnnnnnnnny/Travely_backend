from django.shortcuts import render
from rest_framework.permissions import AllowAny
from .models import AreaData, AreaCode
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
)
from .serializers import (
    OpenDataSerializer
)

class OpendataListAPIView(ListCreateAPIView):
    """
    지역 검색 (서울/경기/강원/전라/경상 ....)
    """
    queryset = AreaData.objects.all()
    serializer_class = OpenDataSerializer
    permission_classes = [
        AllowAny,
    ]
class OpendataAPIView(ListCreateAPIView):
    """
    지역 검색 (서울/경기/강원/전라/경상 ....)
    """
    queryset = AreaData.objects.all()
    serializer_class = OpenDataSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        keyword = self.kwargs['keyword']
        qs = AreaData.objects.filter(areaname__name__icontains=keyword)

        return qs

class DataSearchAPIView(ListCreateAPIView):
    """
    관광지 이름 검색
    """
    queryset = AreaData.objects.all()
    serializer_class = OpenDataSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        keyword = self.kwargs['keyword']
        qs = AreaData.objects.filter(title__icontains=keyword)

        return qs