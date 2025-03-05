from django import forms
from .models import Task, Kanban
from django.forms import DateTimeInput, Select


class TaskAddForm(forms.ModelForm):
    # TODO: Нужна валидация текстовых полей формы
    class Meta:
        model = Task
        fields = ['title', 'description', 'image']
        labels = {
            'title': 'название',
            'description': 'описание',
            'image': 'изображение (не больше 2 МБ)',
        }


class KanbanAddForm(forms.ModelForm):
    # TODO: Нужна валидация текстовых полей формы
    class Meta:
        model = Kanban
        fields = ['title']
        labels = {
            'title': 'название',
        }


class TaskAssignForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['executor', 'datetime_deadline']
        labels = {
            'executor': 'исполнитель',
            'datetime_deadline': 'дедлайн',
        }
        widgets = {
            'executor': Select(
                attrs={'required': True}
            ),
            'datetime_deadline': DateTimeInput(
                attrs={'type': 'datetime-local', 'required': True}
            ),
        }
