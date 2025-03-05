from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
    TemplateView,
)
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.shortcuts import render
from django.utils import timezone
from .forms import TaskAddForm, KanbanAddForm, TaskAssignForm
from .models import Task, Kanban


class KanbanCreateView(LoginRequiredMixin, CreateView):
    model = Kanban
    form_class = KanbanAddForm
    template_name = 'tasks/kanban_add.html'
    success_url = reverse_lazy('tasks:kanban_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Авторизуйтесь прежде чем создавать канбан'}
            )
        )


class KanbanListView(LoginRequiredMixin, ListView):
    model = Kanban
    template_name = 'tasks/kanban_list.html'
    context_object_name = 'kanbans'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Kanban.objects.filter(owner=self.request.user)
        return Task.objects.none()

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Авторизуйтесь чтобы увидеть свои задачи'}
            )
        )


class KanbanDetailView(UserPassesTestMixin, DetailView):
    model = Kanban
    template_name = 'tasks/kanban_detail.html'
    context_object_name = 'kanban'

    def test_func(self) -> bool:
        kanban = self.get_object()
        return kanban.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя просматривать этот канбан'}
            )
        )


class KanbanDeleteView(UserPassesTestMixin, DeleteView):
    model = Kanban
    template_name = 'tasks/kanban_delete.html'
    success_url = reverse_lazy('tasks:kanban_list')

    def test_func(self) -> bool:
        kanban = self.get_object()
        return kanban.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя удалять этот канбан'}
            )
        )


class IndexView(TemplateView):
    template_name = 'tasks/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_authenticated'] = self.request.user.is_authenticated
        return context


class TaskDetailView(UserPassesTestMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def test_func(self) -> bool:
        task = self.get_object()
        return task.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя просматривать эту задачу'}
            )
        )


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskAddForm
    template_name = 'tasks/task_add.html'

    def get_success_url(self):
        return reverse_lazy('tasks:kanban_detail', kwargs={'pk': self.object.kanban.pk})

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.kanban = Kanban.objects.get(pk=self.kwargs['kanban_pk'])
        return super().form_valid(form)

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Авторизуйтесь прежде чем создавать задачи'}
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kanban_pk'] = self.kwargs['kanban_pk']
        return context


class TaskDeleteView(UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_delete.html'

    def get_success_url(self):
        return reverse_lazy('tasks:kanban_detail', kwargs={'pk': self.object.kanban.pk})

    def test_func(self) -> bool:
        task = self.get_object()
        return task.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя удалять эту задачу'}
            )
        )


class TaskUpdateView(UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskAddForm
    template_name = 'tasks/task_update.html'

    def get_success_url(self):
        return reverse_lazy('tasks:kanban_detail', kwargs={'pk': self.object.kanban.pk})

    def test_func(self) -> bool:
        task = self.get_object()
        return task.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя редактировать эту задачу'}
            )
        )


class TaskAssignView(UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskAssignForm
    template_name = 'tasks/task_assign.html'

    def get_success_url(self):
        return reverse_lazy('tasks:kanban_detail', kwargs={'pk': self.object.kanban.pk})

    def test_func(self) -> bool:
        task = self.get_object()
        return task.owner == self.request.user

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(
                self.request,
                'tasks/forbidden.html',
                {'message': 'Вам нельзя назначать эту задачу'}
            )
        )

    def form_valid(self, form):
        executor = form.cleaned_data['executor']
        deadline = form.cleaned_data['datetime_deadline']
        now = timezone.now()

        if not executor:
            form.add_error(
                'executor',
                'Назначьте исполнителя!'
            )
            return self.form_invalid(form)

        if not deadline:
            form.add_error(
                'datetime_deadline',
                'Задайте дедлайн!'
            )
            return self.form_invalid(form)

        if deadline < now:
            form.add_error(
                'datetime_deadline',
                'Дедлайн не может быть раньше даты назначения!'
            )
            return self.form_invalid(form)

        form.instance.to_assigned()
        return super().form_valid(form)


class AppLoginView(LoginView):
    template_name = 'tasks/login.html'

    def get_success_url(self):
        return reverse_lazy('tasks:kanban_list')


class AppLogoutView(LogoutView):
    next_page = reverse_lazy('tasks:index')


class AppSignupView(UserPassesTestMixin, CreateView):
    form_class = UserCreationForm
    template_name = 'tasks/signup.html'
    success_url = reverse_lazy('tasks:kanban_list')

    def test_func(self) -> bool:
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return HttpResponseForbidden(
            render(self.request, 'tasks/forbidden.html', {'message': 'Вы уже авторизованы'})
        )


# TODO: Показать 404 в шаблоне not_found.html
