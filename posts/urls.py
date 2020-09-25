from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet)
router.register(r'posts/explore/user/(?P<keyword>[0-9a-zA-Z가-힣]+)', views.PostSearchViewSet)
router.register(r'posts/explore/season/(?P<keyword>[0-9a-zA-Z가-힣]+)', views.PostSeasonViewSet)
router.register(r'posts/explore/(?P<search>[0-9a-zA-Z가-힣]+)/(?P<keyword>[0-9a-zA-Z가-힣]+)', views.PostDetailSearchViewSet)
router.register(r'count/tag/(?P<keyword>[0-9a-zA-Z가-힣]+)', views.TagViewSet)
router.register(r"posts/(?P<post_pk>\d+)/comments", views.CommentViewSet)
router.register("mypage", views.MypageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

