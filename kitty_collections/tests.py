from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from cats.models import Cat
from kitty_collections.models import Collection, CollectionItem, Tag

User = get_user_model()


class CollectionsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username='owner', password='pass12345')
        cls.other = User.objects.create_user(username='other', password='pass12345')
        cls.cat = Cat.objects.create(name='Barsik', color='ginger', birth_year=2020)
        cls.tag = Tag.objects.create(name='Милые', slug='cute')

    def setUp(self):
        self.collection = Collection.objects.create(
            title='Моя подборка',
            description='',
            owner=self.owner,
            visibility=Collection.Visibility.PRIVATE,
        )
        self.collection.tags.add(self.tag)
        CollectionItem.objects.create(collection=self.collection, cat=self.cat)

    def _token(self, user):
        return Token.objects.get_or_create(user=user)[0].key

    def test_guest_sees_only_public_on_list(self):
        Collection.objects.create(
            title='Публичная',
            owner=self.owner,
            visibility=Collection.Visibility.PUBLIC,
        )
        url = reverse('collection-list')
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        titles = [x['title'] for x in r.data['results']]
        self.assertIn('Публичная', titles)
        self.assertNotIn('Моя подборка', titles)

    def test_private_detail_forbidden_for_stranger(self):
        url = reverse('collection-detail', args=[self.collection.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.other)}')
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_favorite_own_collection(self):
        url = reverse('collection-favorite', args=[self.collection.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.owner)}')
        r = self.client.post(url, {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_cat_in_collection(self):
        cat2 = Cat.objects.create(name='Murz', color='black', birth_year=2021)
        CollectionItem.objects.create(collection=self.collection, cat=cat2)
        url = reverse('collection-add-cat', args=[self.collection.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.owner)}')
        r = self.client.post(url, {'cat_id': self.cat.pk}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_requires_non_empty(self):
        col = Collection.objects.create(
            title='Пустая публичная',
            owner=self.owner,
            visibility=Collection.Visibility.PRIVATE,
        )
        url = reverse('collection-detail', args=[col.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.owner)}')
        r = self.client.patch(url, {'visibility': 'public'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stranger_cannot_patch_private_collection(self):
        """Чужую приватную подборку патчить нельзя — вернётся 404, как на GET."""
        url = reverse('collection-detail', args=[self.collection.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.other)}')
        r = self.client.patch(url, {'title': 'hack'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_stranger_cannot_patch_public_collection(self):
        col = Collection.objects.create(
            title='Публичная',
            owner=self.owner,
            visibility=Collection.Visibility.PUBLIC,
        )
        CollectionItem.objects.create(collection=col, cat=self.cat)
        url = reverse('collection-detail', args=[col.pk])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._token(self.other)}')
        r = self.client.patch(url, {'title': 'hack'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
