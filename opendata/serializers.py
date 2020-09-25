from rest_framework import serializers
from .models import AreaCode, AreaData


class OpenDataSerializer(serializers.ModelSerializer):
    """
    공공데이터
    """
    class Meta:
        model = AreaData
        # fields = 
        fields = ['areaname', 'title', 'addr', 'image', 'mapx', 'mapy']

        ordering = ['-addr']