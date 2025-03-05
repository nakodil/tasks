from pathlib import Path
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Task


class TaskViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            owner=self.user
        )

    def test_index_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('tasks:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/index.html')

    def test_task_list_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('tasks:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task)
        self.assertTemplateUsed(response, 'tasks/list.html')

    def test_task_detail_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('tasks:detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task)
        self.assertTemplateUsed(response, 'tasks/detail.html')

    def test_task_delete_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('tasks:delete', args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        task = Task.objects.filter(pk=self.task.pk)
        self.assertFalse(task.exists())

    def test_task_update_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        context = {
            'title': 'Updated Test Task',
            'description': 'Updated Test Description',
        }
        response = self.client.post(reverse('tasks:update', args=[self.task.pk]), context)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, context['title'])
        self.assertEqual(self.task.description, context['description'])

    def test_task_create_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        context = {
            'title': 'New Test Task',
            'description': 'New Test Description',
        }
        response = self.client.post(reverse('tasks:add'), context)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.filter(title=context['title'])
        self.assertTrue(task.exists())


class TaskFormTest(TestCase):
    def setUp(self):
        pass


class TaskAuthTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )

    def test_login(self):
        context = {
            'username': 'testuser',
            'password': 'password',
        }
        response = self.client.post(reverse('tasks:login'), context)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('tasks:logout'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.status_code, 302)


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            owner=self.user
        )

    def test_task_image_delete(self):
        self.task.image = SimpleUploadedFile('test_image.jpg', b'', 'image/jpg')
        self.task.save()
        image_path = Path(self.task.image.path)
        self.task.delete()
        self.assertFalse(image_path.exists())

    def test_task_image_upload(self):
        self.task.image = SimpleUploadedFile('test_image.jpg', b'', 'image/jpg')
        self.task.save()
        image_path = Path(self.task.image.path)
        self.assertTrue(image_path.exists())
        self.task.delete()

    def test_task_owner_delete(self):
        task = Task.objects.filter(pk=self.task.pk)
        self.user.delete()
        self.assertFalse(task.exists())
