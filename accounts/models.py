from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import resolve_url
from opendata.models import *
from django.conf import settings

class User(AbstractUser):
    """
    회원가입
    로컬 : username(email), name, birthday, password
    소셜 : username(uuid), name, image_url, password
    """

    name = models.CharField(max_length=20, null=True)
    nick_name = models.CharField(max_length=20, null=True)
    birthday = models.DateField(auto_now=False, null=True)
    avatar = models.ImageField(
        blank=True,
        upload_to="accounts/avatar/%Y/%m/%d",
        default="defaultProfileImage.png"
    )
    image_url = models.URLField(max_length=500, blank=True)
    auth_code = models.CharField(max_length=10, blank=True)
    
    follow_set = models.ManyToManyField("self", blank=True, symmetrical=False, related_name='follow_by') # 팔로우 목록
    
    level = models.IntegerField(default = 0) # 레벨
    exp = models.IntegerField(default = 0) # 경험치, 250씩 2배로
    #follower_set = models.ManyToManyField("self", blank=True)
    #following_set = models.ManyToManyField("self", blank=True)
    
    is_first = models.BooleanField(default=True) # 첫 사용자인지
    
    area_set = models.ManyToManyField("Area", blank=True)
    concept_set = models.ManyToManyField("Concept", blank=True)

    fcm_token = models.CharField(max_length=300, null=True, blank=True)


    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        # else:
            # return resolve_url("pydenticon_image", self.username)

# 관심 지역
class Area(models.Model):
   area = models.CharField(max_length=30, unique=True)
   def __str__(self):
       return self.area

class Concept(models.Model):
    concept = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.concept

class MapData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="map_data_set",on_delete=models.CASCADE)
    code = models.IntegerField(unique=True)
    map_name = models.CharField(max_length=10, unique=True)
    count = models.IntegerField(default=0)



# 타임스탬프
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class FCMAlarm(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="fcm_set",on_delete=models.CASCADE)
    div = models.CharField(max_length=30)
    text = models.TextField()