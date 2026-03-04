from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm

from users.models import User


class UserLoginForm(AuthenticationForm):

    class Meta:
        model = User
        fields = ['username', 'password']

    username = forms.CharField()
    password = forms.CharField()

    # username = forms.CharField(
    #     label = 'Имя',
    #     widget=forms.TextInput(attrs={"autofocus": True,
    #                                   'class': 'form-control',
    #                                   'placeholder': 'Введите ваше имя пользователя'})
    # )
    # password = forms.CharField(
    #     label = 'Пароль',
    #     widget=forms.PasswordInput(attrs={"autocomplete": "current-password",
    #                                       'class': 'form-control',
    #                                       'placeholder': 'Введите ваш пароль'})
    # )

class UserRegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )
    
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.CharField()
    password1 = forms.CharField()
    password2 = forms.CharField()


    # first_name = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваше имя",
    #         }
    #     )
    # )
    # last_name = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите вашу фамилию",
    #         }
    #     )
    # )
    # username = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваше имя пользователя",
    #         }
    #     )
    # )
    # email = forms.CharField(
    #     widget=forms.EmailInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваш email *youremail@example.com",
    #         }
    #     )
    # )
    # password1 = forms.CharField(
    #     widget=forms.PasswordInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваш пароль",
    #         }
    #     )
    # )
    # password2 = forms.CharField(
    #     widget=forms.PasswordInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Поддтвердите ваш пароль",
    #         }
    #     )
    # )

class ProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "image",
            "first_name",
            "last_name",
            "username",
            "email",)

    image = forms.ImageField(required=False)
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.CharField()


class StudentVerificationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "student_country",
            "student_university",
            "student_email",
            "student_id_card",
        )

    student_country = forms.CharField(max_length=80)
    student_university = forms.CharField(max_length=160)
    student_email = forms.EmailField()
    student_id_card = forms.ImageField(required=True)



    # image = forms.ImageField(
    #     widget=forms.FileInput(attrs={"class": "form-control mt-3"}), required=False
    # )
    # first_name = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваше имя",
    #         }
    #     )
    # )
    # last_name = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите вашу фамилию",
    #         }
    #     )
    # )
    # username = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваше имя пользователя",
    #         }
    #     )
    # )
    # email = forms.CharField(
    #     widget=forms.EmailInput(
    #         attrs={
    #             "class": "form-control",
    #             "placeholder": "Введите ваш email *youremail@example.com",
    #             # 'readonly': True,
    #         }
    #     ),
    # )
