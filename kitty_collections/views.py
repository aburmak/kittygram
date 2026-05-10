from django.db import IntegrityError, transaction
from django.db.models import Count, Q

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from kittygram.pagination import StandardResultsSetPagination

from .filters import CollectionFilter
from .models import Collection, CollectionFavorite, CollectionItem, Tag
from .permissions import IsOwnerOrStaff
from .serializers import (
    CollectionDetailSerializer,
    CollectionItemAddSerializer,
    CollectionListSerializer,
    CollectionWriteSerializer,
    FavoriteSerializer,
    TagSerializer,
)
from .validators import assert_can_set_public, assert_not_own_favorite, assert_under_cat_limit


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class CollectionViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = CollectionFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ('title', 'description')
    ordering_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def get_queryset(self):
        qs = (
            Collection.objects.select_related('owner')
            .prefetch_related('tags', 'items__cat')
            .annotate(
                items_count=Count('items', distinct=True),
                favorites_count=Count('favorites', distinct=True),
            )
        )
        user = self.request.user
        action = self.action

        if action == 'my':
            return qs.filter(owner=user).order_by('-created_at')

        if action == 'favorites':
            return qs.filter(favorites__user=user).distinct().order_by('-created_at')

        if action == 'list':
            if user.is_authenticated and user.is_staff:
                return qs.order_by('-created_at').distinct()
            return (
                qs.filter(visibility=Collection.Visibility.PUBLIC)
                .order_by('-created_at')
                .distinct()
            )

        if action in (
            'retrieve',
            'update',
            'partial_update',
            'destroy',
            'add_cat',
            'remove_cat',
            'favorite',
        ):
            if user.is_staff:
                return qs
            if user.is_authenticated:
                return qs.filter(
                    Q(visibility=Collection.Visibility.PUBLIC) | Q(owner=user)
                )
            return qs.filter(visibility=Collection.Visibility.PUBLIC)

        return qs.none()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CollectionWriteSerializer
        if self.action == 'retrieve':
            return CollectionDetailSerializer
        return CollectionListSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action in ('my', 'favorites', 'favorite'):
            return [IsAuthenticated()]
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ('update', 'partial_update', 'destroy', 'add_cat', 'remove_cat'):
            return [IsAuthenticated(), IsOwnerOrStaff()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = CollectionListSerializer(page, many=True, context={'request': request})
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = CollectionListSerializer(page, many=True, context={'request': request})
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    @action(detail=True, methods=['post'], url_path='add_cat')
    def add_cat(self, request, pk=None):
        collection = self.get_object()
        ser = CollectionItemAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cat_id = ser.validated_data['cat_id']
        position = ser.validated_data.get('position')
        assert_under_cat_limit(collection)
        if CollectionItem.objects.filter(collection=collection, cat_id=cat_id).exists():
            raise ValidationError({'detail': 'Этот кот уже в подборке.'})
        try:
            with transaction.atomic():
                CollectionItem.objects.create(
                    collection=collection,
                    cat_id=cat_id,
                    position=position,
                )
        except IntegrityError:
            raise ValidationError({'detail': 'Этот кот уже в подборке.'})
        collection.refresh_from_db()
        out = CollectionDetailSerializer(collection, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='remove_cat')
    def remove_cat(self, request, pk=None):
        collection = self.get_object()
        cat_id = request.data.get('cat_id') or request.query_params.get('cat_id')
        if cat_id is None:
            raise ValidationError({'cat_id': 'Укажите cat_id в теле или query.'})
        try:
            cat_id = int(cat_id)
        except (TypeError, ValueError):
            raise ValidationError({'cat_id': 'Некорректный cat_id.'})
        item = CollectionItem.objects.filter(collection=collection, cat_id=cat_id).first()
        if not item:
            return Response(status=status.HTTP_404_NOT_FOUND)
        remaining = collection.items.count()
        if (
            collection.visibility == Collection.Visibility.PUBLIC
            and remaining <= 1
        ):
            raise ValidationError(
                {
                    'detail': 'Нельзя удалить последнего кота из публичной подборки. Сначала сделайте её приватной или добавьте другого кота.'
                }
            )
        with transaction.atomic():
            item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        collection = self.get_object()
        if request.method == 'POST':
            assert_not_own_favorite(request.user, collection)
            _, created = CollectionFavorite.objects.get_or_create(
                user=request.user,
                collection=collection,
            )
            if not created:
                return Response({'detail': 'Уже в избранном.'}, status=status.HTTP_200_OK)
            return Response({'detail': 'Добавлено в избранное.'}, status=status.HTTP_201_CREATED)
        CollectionFavorite.objects.filter(user=request.user, collection=collection).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
