from django.urls import path, include
from . import views

urlpatterns = [
    path('list/', views.OpendataListAPIView.as_view()),
    path('list/<str:keyword>/', views.OpendataAPIView.as_view()),
    path('search/<str:keyword>/', views.DataSearchAPIView.as_view()),
]