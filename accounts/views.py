from django.contrib.auth import get_user_model
from rest_framework import generics, status
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.viewsets import ModelViewSet
from django.core.mail import send_mail
from django.db.models import Q
from django.views.generic import TemplateView
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    UpdateAPIView,
    DestroyAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    get_object_or_404,
)
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .EmailThread import send_mail
from datetime import datetime
from .models import Concept
from .sendPush import sendPush
import ujson as json, folium
import pandas as pd
from .serializers import (
    AlarmSerializer,
    SignUpSerializer,
    UpdateSerializer,
    ChangePasswordSerializer,
    CheckAuthCodeSerializer,
    ConceptListSerializer,
    FCMSerializer,
    FollowListSerializer,
    FollowerListSerializer,
    NonLoginChangePasswordSerializer,
    OthersFollowListSerializer,
    ReadUserSerializer,
    SuggestionUserSerializer,
    TokenVerifySerializer,
    TokenObtainPairSerializer,

    MyTokenObtainPairSerializer,

    InitialConceptUserSerializer,
    InitialAreaUserSerializer,
)
import string
import random , time
import os, re
from posts.models import PostDate
from django.db.models import Count, Sum
from accounts.models import MapData, FCMAlarm
from collections import Counter
from posts.models import *

User = get_user_model()
string_pool = string.ascii_letters + string.digits

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

class TokenViewBase(generics.GenericAPIView):
    permission_classes = ()
    authentication_classes = ()

    serializer_class = None

    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class TokenObtainPairView(TokenViewBase):
    """
    /accounts/token/
    username, password 을 입력하여 로그인하면 access 토큰과 refresh 토큰을 반환
    """
    # serializer_class = TokenObtainPairSerializer
    serializer_class = MyTokenObtainPairSerializer

token_obtain_pair = TokenObtainPairView.as_view()



class SignupView(ListCreateAPIView):
    """
    ## 회원가입 API ##
    /accounts/signup/
    GET :  /accounts/signup/?username=  으로 아이디 있는지 중복확인
           /accounts/signup/?nick_name=  으로 활동명  있는지 중복확인
    POST : 항목 입력 후 서버 측 전달

    * : 필수항목 표시
    * username : ID ( email or uid 형식 )
    * password : 비밀번호
      name : 이름
      image_url : 소셜로그인시에만 사용 -> img url을 avatar로 변경해줌
    """
    queryset = get_user_model().objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [
        AllowAny,
    ]
    pagination_class = None

    def get_queryset(self):
        username = self.request.GET.get('username')
        nick_name = self.request.GET.get('nick_name')
        qs = super().get_queryset()
        
        if nick_name is None:
            qs = get_user_model().objects.filter(username__iexact=username)
        elif username is None:
            qs = get_user_model().objects.filter(nick_name__iexact=nick_name)

        return qs

class InitialAreaRetrieveUpdateAPIView(ListCreateAPIView):
    """
    /accounts/initial/Area/
    Headers와 함께
    POST : 항목 입력 후 서버 측 전달
    area = '서울'
    area = '강원'
    ... 이런식으로 작성해서 
    """
    queryset = get_user_model().objects.all()
    serializer_class = InitialAreaUserSerializer
    pagination_class = None

    def get_queryset(self):
        qs = get_user_model().objects.filter(username__iexact=self.request.user)

        return qs


class InitialConceptRetrieveUpdateAPIView(ListCreateAPIView):
    """
    /accounts/initial/Concept/
    Headers와 함께
    POST : 항목 입력 후 서버 측 전달
    concept = '바캉스'
    concept = '호캉스'
    ... 이런식으로 작성해서 
    """
    queryset = get_user_model().objects.all()
    serializer_class = InitialConceptUserSerializer
    pagination_class = None

    def get_queryset(self):


        qs = get_user_model().objects.filter(username__iexact=self.request.user)
        #print("#유저 : ",self.request.user)

        return qs

class InitialConceptRetrieveUpdateAPIView(ListCreateAPIView):
    """
    /accounts/initial/
    Headers와 함께
    POST : 항목 입력 후 서버 측 전달
    concept = '국내'
    concept = '해외'
    ... 이런식으로 작성해서 
    """
    queryset = get_user_model().objects.all()
    serializer_class = InitialConceptUserSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated|ReadOnly]

    def get(self, request):
        queryset = Concept.objects.all()
        dic = {'concept': []}
        serializer = ConceptListSerializer(queryset, many=True)
        for data in serializer.data:
            dic['concept'].append(str(data['concept']))
            #print(data['concept'])
        #print(dic)
        # return Response(serializer.data)
        return Response(dic)

    def get_queryset(self):


        qs = get_user_model().objects.filter(username__iexact=self.request.user)
        return qs




class UserView(ListCreateAPIView):
    """
    ## 회원중복체크 API ##
    /accounts/user/
    GET :  /accounts/user/?username=  으로 아이디 있는지 중복확인
           /accounts/user/?nick_name=  으로 별명  있는지 중복확인
    """
    queryset = get_user_model().objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [
        AllowAny,
    ]
    pagination_class = None

    def get_queryset(self):
        username = self.request.GET.get('username')
        nick_name = self.request.GET.get('nick_name')
        qs = super().get_queryset()

        if nick_name is None:
            qs = get_user_model().objects.filter(username__iexact=username)
        elif username is None:
            qs = get_user_model().objects.filter(nick_name__iexact=nick_name)

        return qs

class TokenVerifyView(TokenViewBase):
    """
    Takes a token and indicates if it is valid.  This view provides no
    information about a token's fitness for a particular use.
    """
    serializer_class = TokenVerifySerializer


token_verify = TokenVerifyView.as_view()
       
class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """
    ## 프로필 수정 API ##
    /accounts/profile/
    GET : 로그인된 유저의 프로필 정보 조회
    PUT : 모든 필드에 대해서 수정
    PATCH : 일부 필드에 대해서 수정

    Headers : JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    avatar : 로컬로그인시 사용하는 프로필 이미지
    name : 이름
    """
    queryset = get_user_model().objects.all()
    serializer_class = UpdateSerializer

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
        
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, username=self.request.user)
        #print("## 프로필 : ", type(obj))
        return obj


class ChangePasswordUpdateAPIView(UpdateAPIView):
    """
    ## 비밀번호 변경 API ##
    /accounts/edit/password/
    PUT

    Headers : JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    old_password : 기존 비밀번호와 비교 검증
    new_password : 새로운 비밀번호
    """
    serializer_class = ChangePasswordSerializer
    model = get_user_model()

    def get_object(self, queryset=None):
           obj = self.request.user
           return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            old_password = serializer.data.get("old_password")
            if not self.object.check_password(old_password):
                return Response({"old_password" : ["비밀번호가 틀립니다."]},
                    status=status.HTTP_400_BAD_REQUEST)

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response("비밀번호 변경 성공", status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckAuthCodeListCreateAPIView(ListCreateAPIView):
    """
    ## 이메일 확인 및 인증번호 확인 API
    /accounts/find/password/?username=
    GET 
    ?username= 을 통해 이메일이 있는지 확인 후 인증코드 생성 및 이메일로 전송
    (성공시 200 OK, 유저와 인증코드를 반환 / 실패시 404 NOT FOUND 반환)
    
    POST
    받은 인증번호 입력, 확인 및 응답으로 돌려받은 username과 함께 reset/password/ 에 요청

    """
    queryset = get_user_model().objects.all()
    serializer_class = CheckAuthCodeSerializer
    permission_classes = [
        AllowAny,
    ]

    def list(self, request):
        check_username = request.GET.get('username')
        
        try:
            user = get_user_model().objects.get(username=check_username)

            result = ""
            for i in range(6):
                result += random.choice(string_pool)

            user.auth_code = result
            user.save()

            send_mail(
                "<Travely> 패스워드를 설정하기 위한 인증코드 메일이 도착했습니다.",
                f"인증코드 {result} 입니다. 인증 후 비밀번호를 설정해주세요.",
                "Travely support",
                [check_username])
        except get_user_model().DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        ## 사실 없어도 됨
        user_code = get_user_model().objects.get(username=check_username)
        serializer = CheckAuthCodeSerializer(user_code)
        ## 사실 없어도 됨

        return Response(serializer.data , status=status.HTTP_200_OK)
        
    def post(self, request):
        code = request.data['auth_code'] # 입력받은 코드

        try:
            user = get_user_model().objects.get(auth_code=code)
        except get_user_model().DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user = get_user_model().objects.get(username = user.username)
        serializer = CheckAuthCodeSerializer(user)

        user.auth_code = ""
        user.save()

        return Response(serializer.data ,status=status.HTTP_200_OK)


class ResetPasswordRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """
    ## 비로그인 비밀번호 리셋 API ##
    /accounts/reset/password/?username=

    PUT
    /accounts/find/password/의 POST 요청에서 반환된 username을 가져와, 
    url에 파라미터로 넘기면서 user를 명시.
    password 값을 입력받아서 보냄

    """
    serializer_class = NonLoginChangePasswordSerializer
    model = get_user_model()
    permission_classes = [
        AllowAny,
    ]

    def get_object(self):
        # username = self.request.data['username']
        username = self.request.GET.get('username')
        #print("###################username :", username)
        obj = get_user_model().objects.get(username=username)
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.data.get("password")
            self.object.set_password(new_password)
            self.object.save()
            return Response("비밀번호 변경 성공", status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDestoryAPIView(DestroyAPIView):
    """
    ## 회원탈퇴 API ##
    /accounts/delete/
    Headers : JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    DELETE
    """
    serializer_class = UpdateSerializer
    model = get_user_model()

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj 
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SuggestionListAPIView(ListAPIView):
    """
    팔로우 리스트 (유저목록 가져옴)
    /accounts/suggestions/
    Headers : JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    GET
    username, name, avatar_url
    """
    queryset = get_user_model().objects.all()
    serializer_class = SuggestionUserSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.exclude(pk=self.request.user.pk) # 자신 제외
        # qs = qs.exclude(is_superuser=True) # 관리자 계정 제외
        # qs = qs.exclude(pk__in=self.request.user.following_set.all())
        qs = qs.exclude(pk__in=self.request.user.follow_set.all())
        return qs
    

@api_view(['POST'])
def user_follow(request):
    """
    유저 팔로우 기능
    /accounts/follow/
    Headers : Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    POST
    nick_name (팔로우할 상대의 닉네임)
    """
    nick_name = request.data['nick_name']
    follow_user = get_object_or_404(get_user_model(), nick_name=nick_name, is_active=True) # active된 유저만, nick_name으로 할지??

    request.user.follow_set.add(follow_user)
    # follow_user.follow_set.add(request.user)

    try:
        msg = request.user.nick_name +  "님이 팔로우 요청을 보냈습니다."
        sendPush("팔로우 요청", msg, follow_user.fcm_token, 'follow')
        FCMAlarm.objects.create(user=follow_user, div='follow', text=msg)
    except:
        print("-fcm 토큰 부재-")
    
    
    # print("### 팔로잉, 팔로우 : ", request.user.following_set.all(), request.user.follower_set.all())
    return Response(status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def user_unfollow(request):
    """
    유저 언팔로우 기능
    /accounts/unfollow/
    Headers : Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.ef..........

    POST
    nick_name (언팔로우할 상대의 닉네임)
    """
    nick_name = request.data['nick_name']
    follow_user = get_object_or_404(get_user_model(), nick_name=nick_name, is_active=True)
    
    request.user.follow_set.remove(follow_user)
    # follow_user.follow_set.remove(request.user)
    
    return Response(status.HTTP_204_NO_CONTENT)


class ReadUserRetrieveAPIView(RetrieveAPIView):
    """
    /accounts/닉네임명/
    유저 조회
    isFollow : 내가 이 유저를 팔로우하고 있는지
    followBy : 이 유저가 나를 팔로우하고 있는지
    """ 
    queryset = get_user_model().objects.all()
    serializer_class = ReadUserSerializer
    pagination_class = None

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, nick_name__iexact=self.kwargs["nickname"])
        return obj

class FollowListAPIView(ListAPIView):
    """
    /accounts/followlist/
    자신이 팔로우하는 유저 리스트
    followBy : 유저가 나를 팔로우하고 있는지
    """
    queryset = get_user_model().objects.all()
    serializer_class = FollowListSerializer
    pagination_class = None

    def get_queryset(self):
        qs = get_user_model().objects.get(username=self.request.user).follow_set.all()
        #print(self.request.user)
        return qs


class FollowerListAPIView(ListAPIView):
    """
    /accounts/followerlist/
    자신을 팔로우하는 유저 리스트
    isFollow : 내가 이 유저를 팔로우하고 있는지
    """
    queryset = get_user_model().objects.all()
    serializer_class = FollowerListSerializer
    pagination_class = None

    def get_queryset(self):
        pk_data = []
        # read_user = get_user_model().objects.get(pk=self.request.user.pk)
        read_user = get_object_or_404(get_user_model().objects.all(), username=self.request.user)
        #f_list = get_user_model().objects.prefetch_related('follow_by').filter(follow_set__in=str(read_user.pk))
        #print(read_user)
        f_list = get_user_model().objects.prefetch_related('follow_by').filter(follow_set=str(read_user.pk))

        for f in f_list:
            pk_data.append(f.pk)
        qs = get_user_model().objects.filter(pk__in=pk_data)
        return qs 


class UserFollowListAPIView(ListAPIView):
    """
    /accounts/닉네임명/followlist/
    해당 유저가 팔로우하는 유저 리스트
    isFollow : 내가 이 유저를 팔로우하는지
    followBy : 이 유저가 나를 팔로우하는지
    """
    queryset = get_user_model().objects.all()
    serializer_class = OthersFollowListSerializer
    pagination_class = None

    def get_queryset(self):
        qs = get_user_model().objects.get(nick_name=self.kwargs["nickname"]).follow_set.all()
        qs = qs.exclude(pk=self.request.user.pk)
        return qs 

class UserFollowerListAPIView(ListAPIView):
    """
    /accounts/닉네임명/followerlist/
    해당 유저를 팔로우하는 유저 리스트
    isFollow : 내가 이 유저를 팔로우하는지
    followBy : 이 유저가 나를 팔로우하는지
    """
    queryset = get_user_model().objects.all()
    serializer_class = OthersFollowListSerializer
    pagination_class = None

    def get_queryset(self):
        pk_data = []
        read_user = get_user_model().objects.get(nick_name=self.kwargs["nickname"])
        f_list = get_user_model().objects.prefetch_related('follow_by').filter(follow_set=str(read_user.pk))

        for f in f_list:
            pk_data.append(f.pk)
        qs = get_user_model().objects.filter(pk__in=pk_data)
        qs = qs.exclude(pk=self.request.user.pk)
        return qs 

class FCMDeviceAPIView(RetrieveUpdateAPIView):
    """
    ## FCM 디바이스 등록 API ##
    - POST 요청을 통해 등록, 수정 가능
    headers (JWT)
    body (fcm_token 값)

    """
    queryset = get_user_model().objects.all()
    serializer_class = FCMSerializer

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
        
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, username=self.request.user)
        return obj

class AlarmListAPIView(ListAPIView):
    queryset = FCMAlarm.objects.all()
    serializer_class = AlarmSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(user=self.request.user)
        return qs

    # 3일 이내, 자신과 팔로우한 글만 보이게
    # def get_queryset(self):
    #     # timesince = timezone.now() - timedelta(days=3)
    #     qs = super().get_queryset()
    #     qs = qs.filter(
    #         Q(author=self.request.user)
    #         | Q(author__in=self.request.user.following_set.all())
    #     )
    #     # qs = qs.filter(created_at__gte=timesince )
    #     return qs





# def map_view(request):
#     start = time.time()
#     with open('CTPRVN_WGS84.json', 'r') as f:
#         ajson = json.load(f)
#     m = folium.Map(location=[37.566345, 126.977893], zoom_start=6, prefer_canvas=True)
#     data = pd.DataFrame(list(MapData.objects.filter(user__nick_name='asus').values('code','count')))
    
#     print("1 : ", time.time() - start)

#     c = folium.Choropleth(
#         geo_data=ajson,
#         name='트레블리 여행지도',
#         data=data,
        
#         columns =['code', 'count'],
#         key_on="feature.properties.code",
#         nan_fill_color='white',
#         bins = list(range(max(data['count']))),
#         #fill_color = 'YlGnBu',
#         line_opacity=0.2,
#         prefer_canvas=True,
#     ).add_to(m)

#     folium.LayerControl().add_to(m)
#     c.geojson.add_child(
#         folium.features.GeoJsonTooltip(['CTP_KOR_NM'], labels=False)
#     )

#     html = m.get_root().render()
#     print("3 : ", time.time() - start)
#     context = {'my_map' : html}
#     return render(request, 'accounts/test.html', context)


# class FoliumView(TemplateView):
#     template_name = "accounts/map.html"

#     def get_context_data(self, **kwargs):
#         start = time.time()

#         figure = folium.Figure()
#         with open('CTPRVN_WGS84.json', 'r', encoding='unicode_escape') as f:
#             ajson = json.load(f)
#         print("json : ", time.time() - start)
#         m = folium.Map(
#             location=[36.066345, 127.977893],
#             zoom_start=7, 
#             tiles='',
#         )
#         m.add_to(figure)
#         try: 
#             data = pd.DataFrame(list(MapData.objects.filter(user__nick_name=self.request.user).values('code','count')))
#             data['count']

#             c = folium.Choropleth(
#                 geo_data=ajson,
#                 name='트레블리 여행지도',
#                 data=data,
                
#                 columns =['code', 'count'],
#                 key_on="feature.properties.code",
#                 nan_fill_color='white',
#                 bins = [0, max(data['count'])/4, max(data['count'])/2, max(data['count'])/4*3, max(data['count'])],
#                 #fill_color = 'YlGnBu',
#                 line_opacity=0.2,
#             ).add_to(m)
        
#         except:
#             data = pd.DataFrame([[0],[0]], index=['code', 'count']).T
#             c = folium.Choropleth(
#                 geo_data=ajson,
#                 name='트레블리 여행지도',
#                 data=data,
                
#                 columns =['code', 'count'],
#                 key_on="feature.properties.code",
#                 nan_fill_color='white',
#                 #fill_color = 'YlGnBu',
#                 line_opacity=0.2,
#             ).add_to(m)
#         print("choropleth : ", time.time() - start)
        
        

#         # folium.LayerControl().add_to(m)
#         c.geojson.add_child(
#             folium.features.GeoJsonTooltip(['CTP_KOR_NM'], labels=False)
#         )
#         print("시간 : ", time.time() - start)
#         figure.render()
#         print("시간 : ", time.time() - start)
#         return {'map' : figure}


class FoliumView(TemplateView):
    template_name = "accounts/map.html"

    def get_context_data(self, **kwargs):
        start = time.time()
        figure = folium.Figure()
        post = Post.objects.filter(author__pk=self.request.user.pk).select_related('date__detail_locations')

        with open('CTPRVN_WGS84.json', 'r', encoding='utf-8') as f:
            ajson = json.load(f)
        print("json : ", time.time() - start)

        m = folium.Map(
            location=[36.066345, 127.977893],
            zoom_start=7, 
            tiles='',
        )
        m.add_to(figure)
        
        p = re.compile('[가-힣]{2}')
        f_all = p.findall

        data = [f_all(i[0])[0] for i in post.values_list('date__detail_locations__location')]
        a = dict(Counter(data))

        for i in range(17):
            prop = ajson['features'][i]['properties']
            if prop['CTP_KOR_NM'] in a.keys():
                prop['count'] += a[prop['CTP_KOR_NM']]

        print("n : ", time.time() - start)
        style = lambda x: {'fillColor':'#8CFF80' if x['properties']['count']>0 else '#17FF00' if x['properties']['count']>3 else '#FFFFFF', 'color':'#696969', 'weight':0.2}

        folium.GeoJson(
            ajson,
            style_function = style,
            tooltip=folium.GeoJsonTooltip(fields=['CTP_KOR_NM'], labels=False)
        ).add_to(m)

        figure.render()

        print("f : ", time.time() - start)
        return {'map' : figure}