from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from cats.views import CatViewSet
from kitty_collections.views import CollectionViewSet, TagViewSet

router = DefaultRouter()
router.register(r'cats', CatViewSet, basename='cat')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/token/', obtain_auth_token, name='api-token'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path(
        'cats/',
        RedirectView.as_view(url='/api/v1/cats/', permanent=False),
        name='legacy-cats',
    ),
]
