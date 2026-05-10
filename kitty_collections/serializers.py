from django.db import transaction

from rest_framework import serializers

from cats.models import Cat
from cats.serializers import CatSerializer

from .models import Collection, CollectionFavorite, CollectionItem, Tag
from .validators import assert_can_set_public


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class CollectionItemSerializer(serializers.ModelSerializer):
    cat = CatSerializer(read_only=True)
    cat_id = serializers.PrimaryKeyRelatedField(
        queryset=Cat.objects.all(), source='cat', write_only=True
    )

    class Meta:
        model = CollectionItem
        fields = ('id', 'cat', 'cat_id', 'position', 'added_at')
        read_only_fields = ('id', 'cat', 'added_at')


class CollectionListSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = (
            'id',
            'title',
            'description',
            'visibility',
            'owner',
            'tags',
            'items_count',
            'favorites_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class CollectionDetailSerializer(CollectionListSerializer):
    items = CollectionItemSerializer(many=True, read_only=True)

    class Meta(CollectionListSerializer.Meta):
        fields = CollectionListSerializer.Meta.fields + ('items',)


class CollectionWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, allow_empty=True
    )

    class Meta:
        model = Collection
        fields = ('title', 'description', 'visibility', 'tags')

    def validate_visibility(self, value):
        return value

    def validate(self, attrs):
        visibility = attrs.get('visibility', getattr(self.instance, 'visibility', None))
        if self.instance is None:
            if visibility == Collection.Visibility.PUBLIC:
                raise serializers.ValidationError(
                    {'visibility': 'Создайте подборку как приватную, добавьте котов, затем сделайте публичной.'}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        instance = Collection.objects.create(**validated_data)
        if tags:
            instance.tags.set(tags)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        instance.refresh_from_db()
        if instance.visibility == Collection.Visibility.PUBLIC:
            assert_can_set_public(instance)
        return instance


class CollectionItemAddSerializer(serializers.Serializer):
    cat_id = serializers.IntegerField()
    position = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    def validate_cat_id(self, value):
        if not Cat.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Кот с таким id не найден.')
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    collection = CollectionListSerializer(read_only=True)

    class Meta:
        model = CollectionFavorite
        fields = ('id', 'collection', 'created_at')
        read_only_fields = fields
