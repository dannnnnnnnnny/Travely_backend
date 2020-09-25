from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Post, Comment, DetailPostImage, PostDate, Tag
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from .serializers import (
    PostSerializer,
    PostSearchSerializer,
    DetailPostImageSerializer,
    PostDateSerializer, 
    TagSearchSerializer,
    CommentSerializer
)
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from django.db.models import Count
from .sendPush import sendPush
import re

class PostCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'

class PostViewSet(ModelViewSet):
    """
    ## 게시물 API
    Headers 필요
    
    * 글쓰기
    /api/posts/
    @POST 메소드
    -간편 리뷰 필드
    is_quick : true (간편)
    day0_caption : 글 (하나)
    day0_image : 사진 (여러장)
    day0_location : 장소 (여러개)
    rating : 평점 (하나 / 0.0~5.0 / 0.5단위로)
    tag : 태그 (여러개)

    - 상세 리뷰 필드
    is_quick = false (상세)
    start_date : 여행 출발 날짜 (ex) 2020-08-01)
    end_date : 여행 복귀 날짜 (ex) 2020-08-02)
    day0,1,2,3..._caption : 글 (날짜당 하나)
    day0,1,2,3..._image : 사진 (날짜당 여러장)
    day0,1,2,3..._location : 장소 (날짜당 여러개)
    rating : 평점 (하나 / 0.0~5.0 / 0.5단위로)
    tag : 태그 (여러개)

    * 글 상세보기
    /api/posts/{int:id}/
    @GET 메소드

    * 글 수정하기
    /api/posts/{int:id}/ (id는 글번호)
    @POST 메소드
    위와 동일함
    (/api/posts/pk/ @GET 메소드를 통해서 원래 글정보를 그대로 가져온 후 수정하는 방식으로)

    * 글 삭제하기
    /api/posts/{int:id}/
    @DELETE 메소드
    
    * 글 검색하기
    /api/posts/explore/location/키워드/ : 지역,장소 검색
    /api/posts/explore/caption/키워드/ : 글 내용 검색
    /api/posts/explore/tag/키워드/ : 태그 검색
    /api/posts/explore/user/키워드/ : 유저 이름, 닉네임 검색
    /api/posts/explore/season/키워드/ : 계절 검색

    * 글 좋아요 - 성공시 201
    /api/posts/{int:id}/like/
    @POST 메소드

    * 글 좋아요 취소 - 성공시 204
    /api/posts/{int:id}/like/
    @DELETE 메소드
    """
    # queryset = Post.objects.all()
    queryset = (Post.objects.all()
                .select_related("author")
                .prefetch_related("date", "like_user_set")
    )
    pagination_class = PostCursorPagination
    serializer_class = PostSerializer
    

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

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

    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return super().perform_create(serializer)

    def post(self, request, *args, **kwargs):
        # 자신의 글만 수정 가능
        if Post.objects.get(pk=kwargs['pk']).author == request.user:
            return self.update(request, *args, **kwargs)
        else:
            return Response(status.HTTP_403_FORBIDDEN)
    

    @action(detail=True, methods=["POST"]) # 특정 포스팅
    def like(self, request, pk):
        dic = {}
        post = self.get_object() # 현재 포스팅을 얻어옴
        post.like_user_set.add(self.request.user) # 현재 유저를 추가해줌
        
        try:
            msg = self.request.user.nick_name + "님이 회원님의 게시물을 좋아합니다."
            sendPush("좋아요 알림", msg, str(post.author.fcm_token), "post_like")
            FCMAlarm.objects.create(user=post.author, div='post_like', text=msg)
        except:
            #print("-fcm 토큰 부재-")
            pass
        dic['like_count'] = post.like_user_set.count()
        return Response(dic, status.HTTP_201_CREATED)

    @like.mapping.delete
    def unlike(self, request, pk):
        dic = {}
        post = self.get_object()
        post.like_user_set.remove(self.request.user)
        dic['like_count'] = post.like_user_set.count()
        return Response(dic, status.HTTP_201_CREATED)


class PostSearchViewSet(ModelViewSet):
    """
    # 글쓴이 활동명, 이름으로 검색 
    /api/posts/explore/{keyword}
    Headers
    @GET
    """
    queryset = (Post.objects.all()
                .select_related("author")
                .prefetch_related("like_user_set", "date")
    )
    serializer_class = PostSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            Q(author__nick_name__icontains=self.kwargs["keyword"])
            | Q(author__name__icontains=self.kwargs["keyword"])
            | Q(season=self.kwargs["keyword"])          
        )

        return qs.distinct()

class PostSeasonViewSet(ModelViewSet):
    """
    # 계절로 글 검색 API
    /api/posts/explore/season/{keyword}
    Headers
    @GET
    
    """
    queryset = (Post.objects.all()
                .select_related("author")
                .prefetch_related("like_user_set", "date")
    )
    serializer_class = PostSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(Q(season=self.kwargs["keyword"]))

        return qs.distinct()

class PostDetailSearchViewSet(ModelViewSet):
    """
    # 글 내용, 장소, 태그로 검색 API 
    /api/posts/explore/location/{keyword}/
    /api/posts/explore/caption/{keyword}/
    /api/posts/explore/location/{keyword}/
    Headers
    @GET
    """
    queryset = (Post.objects.all()
                .select_related("author")
                .prefetch_related("like_user_set", "date")
    )
    serializer_class = PostSearchSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context['kwargs'] = self.kwargs
        return context
    
    def get_queryset(self):
        if self.kwargs["search"] == "location":
            qs = Post.objects.prefetch_related('date').filter(date__detail_locations__location__icontains=self.kwargs["keyword"]).distinct()
        elif self.kwargs["search"] == "caption":
            qs = Post.objects.prefetch_related('date').filter(date__caption__icontains=self.kwargs["keyword"]).distinct()
        elif self.kwargs["search"] == "tag":
            qs = Post.objects.prefetch_related('date').filter(date__tag_set__name__icontains=self.kwargs["keyword"]).distinct()
        else:
            return []
        return qs

# 태그 검색 API 뷰셋
class TagViewSet(ModelViewSet):
    """
    ## Tag 갯수 검색 API ##
    /api/count/tag/키워드/
    Headers
    @GET
    """
    queryset = PostDate.objects.all()
    serializer_class = TagSearchSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(tag_set__name__icontains=self.kwargs["keyword"]).values('tag_set__name')\
            .annotate(Count('tag_set__name'))
        return qs


# 마이페이지 뷰셋
class MypageViewSet(ModelViewSet):
    """
    ## 마이페이지 API ##
    /api/mypage/
    headers JWT 필요
    @GET
    자신의 간편, 상세 리뷰 가져옴 
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def list(self, request):
        queryset = self.get_queryset()
        queryset = queryset.filter(author=request.user)
        if queryset.count() == 0:
            return Response(0,status.HTTP_204_NO_CONTENT)
        else:
            serializer = PostSerializer(queryset, context={'request': request}, many=True)
            return Response(serializer.data)

# 댓글 뷰셋 
class CommentViewSet(ModelViewSet):
    """
    ## 댓글 API ##
    /api/posts/{n}/comments/
    headers JWT 필요

    @GET
    해당 게시물의 댓글을 가져옴
    
    author 글쓴이
    message 메시지
    created_at 입력시간

    @POST
    message (메시지)
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(post_id=self.kwargs['post_pk'])
        return qs

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)
        user_tag = re.findall('(?:@([^\s]+))+', self.request.data['message'])

        for user_name in list(set(user_tag)):
            f_token = get_user_model().objects.get(nick_name=user_name).fcm_token
            try:
                msg = self.request.user.nick_name + "님이 댓글에 회원님을 언급했습니다."
                sendPush("댓글 태그 알림", msg, str(f_token), "comment_userTag")
                FCMAlarm.objects.create(user=f_token, div='comment_tag', text=msg)
            except:
                pass
                #print("-fcm 토큰 부재-")
        
        try:
            msg = self.request.user.nick_name + "님이 회원님의 게시물에 댓글을 남겼습니다."
            sendPush("댓글 알림", msg, str(post.author.fcm_token), "post_comment")
            FCMAlarm.objects.create(user=f_token, div='comment', text=msg)
        except:
            pass
            #print("-fcm 토큰 부재-")

        return super().perform_create(serializer)

    def post(self, request, *args, **kwargs):
        # 자신의 댓글만 수정 가능
        if Comment.objects.get(pk=kwargs['pk']).author == request.user:
            user_tag = re.findall('(?:@([^\s]+))+', request.data['message'])
            for user_name in list(set(user_tag)):
                f_token = get_user_model().objects.get(nick_name=user_name).fcm_token
                try:
                    msg = request.user.nick_name + "님이 댓글에 회원님을 언급했습니다."
                    sendPush("댓글 태그 알림", msg, str(f_token), "comment_userTag")
                    FCMAlarm.objects.create(user=f_token, div='comment_tag', text=msg)
                except:
                    pass
                    #print("-fcm 토큰 부재-")
            return self.update(request, *args, **kwargs)
        else:
            return Response(status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["POST"]) # 특정 댓글
    def like(self, request, post_pk, pk):
        dic = {}
        comment = self.get_object() # 현재 댓글을 불러옴
        comment.like_user_set.add(self.request.user) # 현재 유저를 추가해줌

        try:
            msg = self.request.user.nick_name + "님이 회원님의 댓글을 좋아합니다."
            sendPush("좋아요 알림", msg, str(post.author.fcm_token), "comment_like")
            FCMAlarm.objects.create(user=post.author, div='comment_like', text=msg)
        except:
            #print("-fcm 토큰 부재-")
            pass

        dic['like_count'] = comment.like_user_set.count()
        return Response(dic, status.HTTP_201_CREATED)

    @like.mapping.delete
    def unlike(self, request, post_pk, pk):
        dic = {}
        comment = self.get_object()
        comment.like_user_set.remove(self.request.user)
        dic['like_count'] = comment.like_user_set.count()
        return Response(dic, status.HTTP_201_CREATED)


