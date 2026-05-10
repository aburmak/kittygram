from django.conf import settings
from django.db import models

from cats.models import Cat


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Collection(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'public'
        PRIVATE = 'private', 'private'

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
    )
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='collections',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='items',
    )
    cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name='collection_items',
    )
    position = models.PositiveIntegerField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'added_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['collection', 'cat'],
                name='collections_item_unique_collection_cat',
            ),
        ]

    def __str__(self):
        return f'{self.collection_id}:{self.cat_id}'


class CollectionFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_collections',
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'collection'],
                name='collections_fav_unique_user_collection',
            ),
        ]

    def __str__(self):
        return f'{self.user_id}♥{self.collection_id}'
