import django_filters

from .models import Collection


class CollectionFilter(django_filters.FilterSet):
    """Фильтры для списка подборок."""

    owner = django_filters.NumberFilter(field_name='owner_id')
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')

    class Meta:
        model = Collection
        fields = ['visibility', 'owner', 'tag']
