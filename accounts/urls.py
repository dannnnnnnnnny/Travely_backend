from django.urls import path, include
from . import views
#from rest_framework_jwt.views import (
#    obtain_jwt_token,
#    refresh_jwt_token,
#    verify_jwt_token,
#)
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("user/", views.UserView.as_view(), name="find_user"),
    path("profile/", views.UserRetrieveUpdateAPIView.as_view(), name="edit"),
    path('initial/area/', views.InitialAreaRetrieveUpdateAPIView.as_view(), name="initial_area"),
    path('initial/concept/', views.InitialConceptRetrieveUpdateAPIView.as_view(), name="initial_concept"),
    path(
        "edit/password/",
        views.ChangePasswordUpdateAPIView.as_view(),
        name="change_password",
    ),
    path(
        "find/password/",
        views.CheckAuthCodeListCreateAPIView.as_view(),
        name="find_password",
    ),
    path(
        "reset/password/",
        views.ResetPasswordRetrieveUpdateAPIView.as_view(),
        name="reset_password",
    ),
    path("delete/", views.UserDestoryAPIView.as_view(), name="delete_user"),
    # path("token/", views.JWTLogin.as_view()),
    # path("token/refresh/", refresh_jwt_token),
    # path("token/verify/", verify_jwt_token),
    path('token/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', views.TokenVerifyView.as_view(), name='token_verify'),
    path(
        "suggestions/",
        views.SuggestionListAPIView.as_view(),
        name="suggestion_user_list",
    ),
    path("device/", views.FCMDeviceAPIView.as_view()),
    path("follow/", views.user_follow, name="user_follow"),
    path("unfollow/", views.user_unfollow, name="user_unfollow"),
    path("followlist/", views.FollowListAPIView.as_view()),
    path("followerlist/", views.FollowerListAPIView.as_view()),
    path("notice/", views.AlarmListAPIView.as_view()),
    #path("map/", views.map_view),
    path("folium/", views.FoliumView.as_view()),
    path("<str:nickname>/", views.ReadUserRetrieveAPIView.as_view()),
    path("<str:nickname>/followlist/", views.UserFollowListAPIView.as_view()),
    path("<str:nickname>/followerlist/", views.UserFollowerListAPIView.as_view()),
    
    
]
