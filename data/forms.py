from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="帳號",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入帳號'})
    )
    email = forms.EmailField(
        label="電子郵件",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '請輸入電子郵件'})
    )
    password1 = forms.CharField(
        label="密碼",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '請輸入密碼'})
    )
    password2 = forms.CharField(
        label="密碼確認",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '請重新輸入密碼'})
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class Forgot_password_Form(PasswordResetForm):
    email = forms.EmailField(
        label="註冊信箱",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '請輸入註冊信箱'})
    )

class ResetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="新密碼",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '請輸入新密碼'})
    )
    new_password2 = forms.CharField(
        label="確認新密碼",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '再次輸入新密碼'})
    )