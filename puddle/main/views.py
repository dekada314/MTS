from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'MTS Cloud Orchestrator - Главная'
        return context


class AboutView(TemplateView):
    template_name = 'main/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'MTS Cloud Orchestrator - О проекте'
        context['content'] = 'О проекте'
        context['text_on_page'] = (
            'Платформа помогает быстро подобрать и протестировать инфраструктуру, '
            'поддержку и готовые решения под ваши бизнес-задачи.'
        )
        return context


class SupportView(TemplateView):
    template_name = 'main/support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'MTS Cloud Orchestrator - 4-уровневая поддержка'
        return context


class FreeTestingView(TemplateView):
    template_name = 'main/free_testing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'MTS Cloud Orchestrator - Бесплатное тестирование'
        return context


class ReadySolutionsView(TemplateView):
    template_name = 'main/solutions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'MTS Cloud Orchestrator - Готовые решения'
        context['solution_type'] = self.request.GET.get('type', 'website')
        return context


@method_decorator(login_required, name='dispatch')
class StudentSubscriptionView(TemplateView):
    template_name = 'users/student_verification.html'

    def dispatch(self, request, *args, **kwargs):
        return redirect(reverse('user:student_verification'))
