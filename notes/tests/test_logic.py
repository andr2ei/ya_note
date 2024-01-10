from http import HTTPStatus

from django.urls import reverse
from pytils.translit import slugify
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()

class LogicTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.auth_client = Client()
        cls.user = User.objects.create(username='user')
        cls.auth_client.force_login(cls.user)

        cls.author_client = Client()
        cls.author = User.objects.create(username='author')
        cls.author_client.force_login(cls.author)

        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 2
        new_note = Note.objects.filter(slug=self.form_data['slug']).get()
        assert new_note.title == self.form_data['title']
        assert new_note.text == self.form_data['text']
        assert new_note.slug == self.form_data['slug']
        assert new_note.author == self.author

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        assert Note.objects.count() == 1

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(response, 'form', 'slug', errors=(self.note.slug + WARNING))
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 2
        expected_slug = slugify(self.form_data['title'])
        new_note = Note.objects.filter(slug=expected_slug).get()
        assert new_note.slug == expected_slug

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get()
        assert note.title == self.form_data['title']
        assert note.text == self.form_data['text']
        assert note.slug == self.form_data['slug']


    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.post(url, self.form_data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        note_from_db = Note.objects.get(id=self.note.id)
        assert self.note.title == note_from_db.title
        assert self.note.text == note_from_db.text
        assert self.note.slug == note_from_db.slug

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 0

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Note.objects.count() == 1
