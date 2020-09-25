from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from django_pydenticon.views import image as pydenticon_image

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_url_v1_patterns = [
    path('accounts/', include('accounts.urls')),
    path('api/', include('posts.urls')),
    path('data/', include('opendata.urls'))
]

schema_view_v1 = get_schema_view(
    openapi.Info(
        title="Travely",
        default_version='v1',
        description="Travely Project API 명세서",
        contact=openapi.Contact(email="ehdgnl5249@gmail.com"),
        license=openapi.License(name="Copyright Travely@2020 "),
    ),
    validators=['flex'],
    public=True,
    permission_classes=(AllowAny,),
    patterns=schema_url_v1_patterns,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('posts.urls')),
    path('accounts/', include("accounts.urls")),
    path('data/', include('opendata.urls')),
    # path("identicon/image/<path:data>.png",
    #      pydenticon_image, name="pydenticon_image"),  # accounts/models.py의 avatar_url

    path('<str:format>', schema_view_v1.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view_v1.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view_v1.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # MEDIA_URL로 시작되는 요청이 오면 document_root 경로에서 파일을 찾아 서빙함.
    # DEBUG 옵션이 False이면 static()은 빈 List를 반환함.
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]