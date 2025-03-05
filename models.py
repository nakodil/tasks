from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from uuid import uuid4
from os import rename


class Kanban(models.Model):
    class Meta:
        verbose_name = 'Канбан'
        verbose_name_plural = 'Канбаны'

    title = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='kanbans'
    )

    def __str__(self) -> str:
        return self.title


class Task(models.Model):
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    title = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tasks'
    )
    image = models.ImageField(
        upload_to='tasks/',
        blank=True,
        null=True
    )
    kanban = models.ForeignKey(Kanban, on_delete=models.CASCADE, related_name='tasks')

    statuses = [
        ('planned', 'планируемая'),
        ('assigned', 'выполняется'),
        ('review', 'проверяется'),
        ('done', 'готова'),
        ('overdue', 'просрочена'),
    ]
    status = models.CharField(max_length=100, default='planned', choices=statuses)

    datetime_created = models.DateTimeField(default=timezone.now, editable=False)
    datetime_assigned = models.DateTimeField(blank=True, null=True)
    datetime_deadline = models.DateTimeField(blank=True, null=True)
    datetime_review = models.DateTimeField(blank=True, null=True)
    datetime_done = models.DateTimeField(blank=True, null=True)

    executor = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tasks', blank=True, null=True)

    def __str__(self) -> str:
        return self.title

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.image:
            self.validate_image()

    def validate_image(self):
        '''Проверяет разрешение изображения'''
        if self.image.size / 1024 / 1024 > settings.IMAGE_MAX_SIZE_MB:
            raise ValidationError(
                f'Размер изображения не должен превышать '
                f'{settings.IMAGE_MAX_SIZE_MB} МБ'
            )

    def save(self):
        if self.pk:  # если апдейт
            old_image = Task.objects.get(pk=self.pk).image
            if old_image and old_image != self.image:
                old_image.delete(save=False)
        super().save()

        if self.image:
            self.resize_image()
            self.convert_image_to_jpg()
            self.rename_image()
            super().save()  # TODO: избавиться от второго сохранения в БД

    def resize_image(self):
        '''Изменяет разрешение изображения, если оно слишком большое'''
        img = Image.open(self.image.path)
        if max(img.width, img.height) > settings.IMAGE_MAX_SIDE_PX:
            img.thumbnail(
                (settings.IMAGE_MAX_SIDE_PX, settings.IMAGE_MAX_SIDE_PX),
                Image.LANCZOS
            )
            img.save(self.image.path)

    def convert_image_to_jpg(self):
        '''Конвертирует изображение в JPG'''
        img = Image.open(self.image.path)
        if img.format.upper() == 'JPEG':
            return

        rgb_image = img.convert('RGB')
        jpg_path = self.image.path.split('.')[:-1]
        jpg_path = '.'.join(jpg_path) + '.jpg'
        rgb_image.save(jpg_path, format='JPEG', quality=90)

        self.image.delete(save=False)
        self.image.name = jpg_path.split('/')[-1]

    def rename_image(self):
        '''Переименовывает файлы изображений в UUID'''
        image_file_extention = self.image.path.split('.')[-1]  # jpg
        new_image_name = f'{uuid4()}.{image_file_extention}'
        new_image_path = f'{settings.MEDIA_ROOT}/tasks/{new_image_name}'
        rename(self.image.path, new_image_path)
        self.image.name = new_image_path

    def to_assigned(self):
        '''Назначение задачи исполнителю'''
        if not self.executor:
            raise ValueError('Нет исполнителя.')
        if not self.datetime_deadline:
            raise ValueError('Нет дедлайна.')
        if self.datetime_deadline <= timezone.now():
            raise ValueError('Дедлайн раньше, чем сейчас.')
        self.status = 'assigned'
        self.datetime_assigned = timezone.now()
        self.save()
