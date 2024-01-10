from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()

class ContentTestCase(TestCase):

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

    def test_notes_list_for_different_users(self):
        client_and_note_in_list = {
            self.author_client: True,
            self.auth_client: False
        }
        url = reverse('notes:list')
        for client, note_in_list in client_and_note_in_list.items():
            with self.subTest(client=client, note_in_list=note_in_list):
                response = client.get(url)
                object_list = response.context['object_list']
                assert (self.note in object_list) is note_in_list

    def test_pages_contains_form(self):
        name_args = {
            'notes:add': None,
            'notes:edit': (self.note.slug,)
        }
        for name, args in name_args.items():
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                assert 'form' in response.context