from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Cat
from .serializers import CatSerializer


class CatViewSet(viewsets.ModelViewSet):
    """Список котиков, добавление нового и просмотр."""

    queryset = Cat.objects.all().order_by('id')
    serializer_class = CatSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'post', 'head', 'options']
