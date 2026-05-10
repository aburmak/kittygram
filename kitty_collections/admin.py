from django.contrib import admin

from .models import Collection, CollectionFavorite, CollectionItem, Tag


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'visibility', 'created_at')
    list_filter = ('visibility',)
    search_fields = ('title', 'description')
    inlines = (CollectionItemInline,)
    filter_horizontal = ('tags',)


@admin.register(CollectionFavorite)
class CollectionFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'collection', 'created_at')
