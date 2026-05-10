from django.db.models import Count

from rest_framework.exceptions import ValidationError

from .constants import MAX_CATS_PER_COLLECTION


def assert_can_set_public(collection):
    """Нельзя оставить публичной подборку без котов."""
    n = collection.items.aggregate(c=Count('id'))['c']
    if n == 0:
        raise ValidationError(
            {'visibility': 'Публичная подборка не может быть пустой. Добавьте котов или оставьте приватной.'}
        )


def assert_under_cat_limit(collection):
    n = collection.items.aggregate(c=Count('id'))['c']
    if n >= MAX_CATS_PER_COLLECTION:
        raise ValidationError(
            {'detail': f'В подборке не больше {MAX_CATS_PER_COLLECTION} котов.'}
        )


def assert_not_own_favorite(user, collection):
    if collection.owner_id == user.id:
        raise ValidationError({'detail': 'Нельзя добавить в избранное собственную подборку.'})
