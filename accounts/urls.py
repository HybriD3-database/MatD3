from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.urls import path
from django.urls import re_path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'),
         name='login'),
    path('logout/', LogoutView.as_view(template_name='accounts/logout.html'),
         name='logout'),
    path('register/', views.register, name='register'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/'
            r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            views.activate, name='activate'),
    path('profile/', views.view_profile, name='view_profile'),
    re_path(r'^profile/(?P<pk>\d+)/$', views.view_profile,
            name='view_profile_with_pk'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('reset-password/', PasswordResetView.as_view(
        template_name='accounts/reset_password.html',
        success_url='accounts:password_reset_done',
        email_template_name='accounts/reset_password_email.html'),
         name='reset_password'),
    path('reset-password/done', PasswordResetDoneView.as_view(
        template_name='accounts/reset_password_done.html'),
         name='password_reset_done'),
    re_path(r'^reset-password/confirm(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
            PasswordResetConfirmView.as_view(
                template_name='accounts/reset_password_confirm.html',
                success_url='accounts:password_reset_complete'),
            name='password_reset_confirm'),
    path('reset-password/complete/', PasswordResetCompleteView.as_view(
        template_name='accounts/reset_password_complete.html'),
         name='password_reset_complete')
]
