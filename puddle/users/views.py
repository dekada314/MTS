from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from carts.models import Cart
from common.mixins import CacheMixin
from orders.models import Order, OrderItem

from users.forms import ProfileForm, UserLoginForm, UserRegistrationForm
import secrets
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views import View
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import Http404

User = get_user_model()

class EmailVerificationView(View):
    """Handle email verification via token link."""
    
    def get(self, request, token):
        try:
            user = get_object_or_404(User, verification_token=token)
            
            if user.email_verified:
                messages.info(request, 'Ваш email уже подтверждён!')
                return redirect('main:index')
            
            if not user.is_token_valid():
                messages.error(
                    request, 
                    'Ссылка устарела. Пожалуйста, свяжитесь с поддержкой.'
                )
                return redirect('main:index')
            
            # Verify email
            user.email_verified = True
            user.verification_token = None
            user.token_created_at = None
            user.save(update_fields=['email_verified', 'verification_token', 'token_created_at'])
            
            messages.success(request, 'Ваш email успешно подтверждён! Теперь вы можете оформлять заказы.')
            return redirect('users:profile')
            
        except Http404:
            messages.error(request, 'Неверная ссылка для подтверждения.')
            return redirect('main:index')

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    # success_url = reverse_lazy('main:index')
    
    def get_success_url(self):
        redirect_page = self.request.POST.get('next', None)
        if redirect_page and redirect_page != reverse('user:logout'):
            return redirect_page
        return reverse_lazy('main:index')
    
    def form_valid(self, form):
        session_key = self.request.session.session_key

        user = form.get_user()

        if user:
            auth.login(self.request, user)
            if session_key:
                # delete old authorized user carts
                forgot_carts = Cart.objects.filter(user=user)
                if forgot_carts.exists():
                    forgot_carts.delete()
                # add new authorized user carts from anonimous session
                Cart.objects.filter(session_key=session_key).update(user=user)

                messages.success(self.request, f"{user.username}, Вы вошли в аккаунт")

                return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - Авторизация'
        return context


class UserRegistrationView(CreateView):
    template_name = 'users/registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        session_key = self.request.session.session_key
        user = form.instance

        if user:
            form.save()
            
            # Send verification email
            self._send_verification_email(user)
            
            # Log user in (but they need to verify email to place orders)
            auth.login(self.request, user)

        if session_key:
            Cart.objects.filter(session_key=session_key).update(user=user)

        if getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', True):
            messages.success(
                self.request, 
                f"{user.username}, Вы успешно зарегистрированы! Проверьте email для подтверждения."
            )
        else:
            messages.success(self.request, f"{user.username}, Вы успешно зарегистрированы и вошли в аккаунт")
        
        return HttpResponseRedirect(self.success_url)
    
    def _send_verification_email(self, user):
        """Отправить письмо со ссылкой для подтверждения email."""
        try:
            verification_url = self.request.build_absolute_uri(
                reverse('users:verify_email', kwargs={'token': user.verification_token})
            )
            
            context = {
                'user': user,
                'verification_url': verification_url,
                'expiry_days': getattr(settings, 'EMAIL_CONFIRMATION_EXPIRE_DAYS', 7)
            }
            
            html_message = render_to_string('email/email_verification.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Подтвердите ваш email - Puddle',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail registration
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - Регистрация'
        return context


class UserProfileView(LoginRequiredMixin, CacheMixin , UpdateView):
    template_name = 'users/profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, "Профайл успешно обновлен")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Произошла ошибка")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - Кабинет'

        # Можно вынести сам запрос в отдельный метод этого класса контроллера
        orders = Order.objects.filter(user=self.request.user).prefetch_related(
                Prefetch(
                    "orderitem_set",
                    queryset=OrderItem.objects.select_related("product"),
                )
            ).order_by("-id")

        context['orders'] = self.set_get_cache(orders, f"user_{self.request.user.id}_orders", 60)
        return context


class UserCartView(TemplateView):
    template_name = 'users/users_cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - Корзина'
        return context

# def users_cart(request):
#     return render(request, 'users/users_cart.html')

# @login_required
# def profile(request):
#     if request.method == 'POST':
#         form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Профайл успешно обновлен")
#             return HttpResponseRedirect(reverse('user:profile'))
#     else:
#         form = ProfileForm(instance=request.user)

#     orders = Order.objects.filter(user=request.user).prefetch_related(
#                 Prefetch(
#                     "orderitem_set",
#                     queryset=OrderItem.objects.select_related("product"),
#                 )
#             ).order_by("-id")
        

#     context = {
#         'title': 'Home - Кабинет',
#         'form': form,
#         'orders': orders,
#     }
#     return render(request, 'users/profile.html', context)



# def login(request):
#     if request.method == 'POST':
#         form = UserLoginForm(data=request.POST)
#         if form.is_valid():
#             username = request.POST['username']
#             password = request.POST['password']
#             user = auth.authenticate(username=username, password=password)

#             session_key = request.session.session_key

#             if user:
#                 auth.login(request, user)
#                 messages.success(request, f"{username}, Вы вошли в аккаунт")

#                 if session_key:
#                     # delete old authorized user carts
#                     forgot_carts = Cart.objects.filter(user=user)
#                     if forgot_carts.exists():
#                         forgot_carts.delete()
#                     # add new authorized user carts from anonimous session
#                     Cart.objects.filter(session_key=session_key).update(user=user)

#                 redirect_page = request.POST.get('next', None)
#                 if redirect_page and redirect_page != reverse('user:logout'):
#                     return HttpResponseRedirect(request.POST.get('next'))
                    
#                 return HttpResponseRedirect(reverse('main:index'))
#     else:
#         form = UserLoginForm()

#     context = {
#         'title': 'Home - Авторизация',
#         'form': form
#     }
#     return render(request, 'users/login.html', context)


# def registration(request):
#     if request.method == 'POST':
#         form = UserRegistrationForm(data=request.POST)
#         if form.is_valid():
#             form.save()

#             session_key = request.session.session_key

#             user = form.instance
#             auth.login(request, user)

#             if session_key:
#                 Cart.objects.filter(session_key=session_key).update(user=user)
#             messages.success(request, f"{user.username}, Вы успешно зарегистрированы и вошли в аккаунт")
#             return HttpResponseRedirect(reverse('main:index'))
#     else:
#         form = UserRegistrationForm()
    
#     context = {
#         'title': 'Home - Регистрация',
#         'form': form
#     }
#     return render(request, 'users/registration.html', context)


@login_required
def logout(request):
    messages.success(request, f"{request.user.username}, Вы вышли из аккаунта")
    auth.logout(request)
    return redirect(reverse('main:index'))