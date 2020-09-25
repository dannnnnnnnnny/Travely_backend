from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.core.files import File
from .models import Concept, Area, FCMAlarm
import os
import re
from urllib import request
import json
from travely.settings import SECRET_KEY
import jwt
from rest_framework_jwt.compat import get_username_field, PasswordField, Serializer
from rest_framework_jwt.settings import api_settings
# from .compat import Serializer
from rest_framework_simplejwt.tokens import RefreshToken, SlidingToken, UntypedToken
from rest_framework_simplejwt import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import MapData

User = get_user_model()

class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['required'] = False
        kwargs['write_only'] = True
        

        super().__init__(*args, **kwargs)

class TokenObtainSerializer(serializers.Serializer):
    username_field = User.USERNAME_FIELD
    default_error_messages = {
        'no_active_account': ('No active account found with the given credentials')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()

    def validate(self, attrs):
        if attrs.get('password'):
            pwd = attrs.get('password')
        else:
            pwd = ''

        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': pwd,
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if self.user is None or not self.user.is_active:
            raise exceptions.AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        return {}

    @classmethod
    def get_token(cls, user):
        raise NotImplementedError('Must implement `get_token` method for `TokenObtainSerializer` subclasses')


# class TokenObtainPairSerializer(TokenObtainSerializer):
#     @classmethod
#     def get_token(cls, user):
#         return RefreshToken.for_user(user)

#     def validate(self, attrs):
        
#         data = super().validate(attrs)
#         # print("## attrs : ", data)
#         refresh = self.get_token(self.user)

#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#         data['nick_name'] = str(refresh.nick_name)
#         payload = jwt.decode(data['access'], SECRET_KEY, 'HS256')
#         user = User.objects.get(pk=payload['user_id'])
#         data['username'] = user.username
#         data['name'] = user.name
#         data['nick_name'] = user.nick_name
#         return data

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['nick_name'] = user.nick_name
        # ...

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        payload = jwt.decode(data['access'], SECRET_KEY, 'HS256')
        user = User.objects.get(pk=payload['user_id'])
        data['username'] = user.username
        data['name'] = user.name
        data['nick_name'] = user.nick_name
        return data

class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        data = super().validate(attrs)
        UntypedToken(attrs['token'])

        payload = jwt.decode(attrs['token'], SECRET_KEY, 'HS256')
        #print("######### : ", payload['user_id'])
        user = User.objects.get(pk = payload['user_id'])
        #print("######### : ", user)
        data['username'] = user.username
        data['name'] = user.name
        data['nick_name'] = user.nick_name

        return data

class SignUpSerializer(serializers.ModelSerializer):
    """
    회원가입 serializer
    로컬 : username(email), name, birthday , password
    소셜 : username (uid) , name, image_url, password
    """
    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'birthday', 'password', 'image_url', 'avatar']

    password = serializers.CharField(write_only=True, required=False)  # 쓰기 전용
    def create(self, validated_data):
        email = self.context['request'].data['username'] # username 이 이메일형식이거나 아니거나
        exp = re.findall("^[a-z0-9]{2,}@[a-z]{2,}\.[a-z]{2,}$",email)

        user = User.objects.create(**validated_data)
        
        if user.image_url:
            result = request.urlretrieve(user.image_url)
            user.avatar.save(
                os.path.basename(user.image_url),
                File(open(result[0], 'rb'))
            )

        if len(exp) != 0:
            user.set_password(validated_data['password'])
        else:
            user.set_password('')

        user.save()


        return user

class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMAlarm
        fileds = ['div', 'text']

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['area']

class InitialAreaUserSerializer(serializers.ModelSerializer):
    area_set = AreaSerializer(many=True, read_only=True)
    username = serializers.CharField(read_only=True)

    def create(self, validated_data):
        user = User.objects.get(username=self.context['request'].user)
        area_list = self.context['request'].data.getlist('area')
        # print("## 이니셜유저 : ", user)
        # print("## 이니셜지역 : ", area_list)

        for c_data in area_list:
            if c_data != '':
                _c, _ = Area.objects.get_or_create(area=c_data)
                user.area_set.add(_c)

        user.is_first = False
        return user

    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'is_first', 'area_set']

class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ['concept']


class InitialConceptUserSerializer(serializers.ModelSerializer):
    concept_set = ConceptSerializer(many=True, read_only=True)
    username = serializers.CharField(read_only=True)

    def create(self, validated_data):
        user = User.objects.get(username=self.context['request'].user)
        concept_list = self.context['request'].data.getlist('concept')
        # print("## 컨셉 data: ", concept_list)
        
        for c_data in concept_list:
            if c_data != '':
                _c, _ = Concept.objects.get_or_create(concept=c_data)
                user.concept_set.add(_c)
        
        user.is_first = False

        return user

    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'is_first', 'concept_set']

class ConceptListSerializer(serializers.ModelSerializer):
    """
    컨셉 리스트
    """
    class Meta:
        model = Concept
        fields = ['concept']

class ReadUserSerializer(serializers.ModelSerializer):
    # follow_set 상속받아 수정
    following_count = serializers.SerializerMethodField("check_follower_name")

    follower_count = serializers.SerializerMethodField("check_follower")
    followBy = serializers.SerializerMethodField("check_follow_by")
    isFollow = serializers.SerializerMethodField("is_follow")

    def check_follower_name(self, obj):
        return get_user_model().objects.get(username=obj).follow_set.count()

    def check_follower(self,obj):
        read_user = get_user_model().objects.get(username=obj)
        return get_user_model().objects.prefetch_related('follow_by').filter(follow_set=read_user).count()

    def check_follow_by(self, obj):
        user = self.context['request'].user
        data = []
        read_user = get_user_model().objects.get(username=obj)
        try:
            read_user.follow_set.get(username=user)
        except:
            return False
        return True

    def is_follow(self, obj): # 내가 이 유저를 팔로우하고 있는지
        user = self.context['request'].user
        read_user = get_user_model().objects.get(username=user)
        try:
            read_user.follow_set.get(username=obj)
        except:
            return False
        return True

    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'level', 'birthday' , 'avatar','following_count','follower_count', 'isFollow', 'followBy']


class UpdateSerializer(serializers.ModelSerializer):
    """
    회원정보 수정 serializer 
    """
    following_count = serializers.SerializerMethodField("check_follow_count")
    follower_count = serializers.SerializerMethodField("check_follower_count")

    def check_follow_count(self, obj):
        user = self.context['request'].user
        return get_user_model().objects.get(username=user).follow_set.count()

    def check_follower_count(self,obj):
        user = self.context['request'].user
        return get_user_model().objects.prefetch_related('follow_by').filter(follow_set=user).count()

    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'level', 'exp', 'birthday' , 'avatar', 'following_count', 'follower_count']
    
    username = serializers.CharField(read_only=True)
    level = serializers.IntegerField(read_only=True)
    exp = serializers.IntegerField(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """
    비밀번호 수정 serializer
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class NonLoginChangePasswordSerializer(serializers.ModelSerializer):
    """
    비밀번호 리셋 serializer
    """
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']


class CheckAuthCodeSerializer(serializers.ModelSerializer):
    """
    인증번호 확인 serializer
    """
    class Meta:
        model = User
        fields = ['pk', 'username', 'auth_code']

    username = serializers.CharField(read_only=True)

class SuggestionUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'name', 'nick_name', 'avatar']

class FollowListSerializer(serializers.ModelSerializer):
    followBy = serializers.SerializerMethodField("follow_by_me")

    def follow_by_me(self, obj):
        user = obj.follow_set.all().filter(username=self.context['request'].user).exists()
        return user
        

    class Meta:
        model = User
        fields = ['pk', 'username', 'nick_name', 'name', 'avatar', 'followBy']

class FollowerListSerializer(serializers.ModelSerializer):
    isFollow = serializers.SerializerMethodField("is_follow")

    def is_follow(self, obj):
        user = self.context['request'].user
        read_user = get_user_model().objects.get(username=user)
        try:
            read_user.follow_set.get(username=obj)
        except:
            return False
        return True

    class Meta:
        model = User
        fields = ['pk', 'username', 'nick_name', 'name', 'avatar', 'isFollow']

class OthersFollowListSerializer(serializers.ModelSerializer):
    isFollow = serializers.SerializerMethodField("is_follow")
    followBy = serializers.SerializerMethodField("follow_by_me")

    def follow_by_me(self, obj):
        user = obj.follow_set.all().filter(username=self.context['request'].user).exists()
        return user

    def is_follow(self, obj):
        user = self.context['request'].user
        read_user = get_user_model().objects.get(username=user)
        try:
            read_user.follow_set.get(username=obj)
        except:
            return False
        return True

    class Meta:
        model = User
        fields = ['pk', 'username', 'nick_name', 'name', 'avatar', 'isFollow', 'followBy']

class FCMSerializer(serializers.ModelSerializer):
    """
    FCM 디바이스 토큰 등록
    """
    class Meta:
        model = User
        fields = ['username', 'nick_name', 'fcm_token']

    username = serializers.CharField(read_only=True)
    nick_name = serializers.CharField(read_only=True)
