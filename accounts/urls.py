# This file is covered by the BSD license. See LICENSE in the root directory.
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'),
         name='login'),
    path('logout', LogoutView.as_view(template_name='accounts/logout.html'),
         name='logout'),
    path('register', views.register, name='register'),
    path('activate/<str:uid>/<slug:token>', views.activate, name='activate'),
    path('profile', views.profile, name='profile'),
    path('change-password', views.change_password, name='change_password'),
    path('reset-password', PasswordResetView.as_view(
        template_name='accounts/reset_password.html',
        success_url='/accounts/reset-password/done',
        email_template_name='accounts/reset_password_email.html'),
         name='reset_password'),
    path('reset-password/done', PasswordResetDoneView.as_view(
        template_name='accounts/reset_password_done.html')),
    path('reset-password/confirm<str:uidb64>/<slug:token>/',
         PasswordResetConfirmView.as_view(
             template_name='accounts/reset_password_confirm.html',
             success_url='/accounts/reset-password/complete'),
         name='password_reset_confirm'),
    path('reset-password/complete', PasswordResetCompleteView.as_view(
        template_name='accounts/reset_password_complete.html')),
]
