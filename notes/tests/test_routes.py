from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()

class RoutesTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.auth_client = Client()
        user = User.objects.create(username='user')
        cls.auth_client.force_login(user)

        cls.author_client = Client()
        author = User.objects.create(username='author')
        cls.author_client.force_login(author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=author,
        )

    def test_pages_availability_for_anonymous_user(self):
        for name in ('notes:home', 'users:login', 'users:logout', 'users:signup'):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                assert response.status_code == HTTPStatus.OK

    def test_pages_availability_for_auth_user(self):
        for name in ('notes:list', 'notes:add', 'notes:success'):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.auth_client.get(url)
                assert response.status_code == HTTPStatus.OK

    def test_pages_availability_for_author(self):
        for name in ('notes:detail', 'notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.author_client.get(url)
                assert response.status_code == HTTPStatus.OK

    def test_pages_availability_for_different_users(self):
        client_status = {
            self.auth_client: HTTPStatus.NOT_FOUND,
            self.author_client: HTTPStatus.OK
        }
        for client, expected_status in client_status.items():
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(client=client, expected_status=expected_status, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    assert response.status_code == expected_status

    def test_redirects(self):
        name_args = {
            'notes:detail': (self.note.slug,),
            'notes:edit': (self.note.slug,),
            'notes:delete': (self.note.slug,),
            'notes:add': None,
            'notes:success': None,
            'notes:list': None
        }
        for name, args in name_args.items():
            login_url = reverse('users:login')
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, expected_url)
