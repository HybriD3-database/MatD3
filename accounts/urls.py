from django.conf.urls import re_path
from . import views
from django.contrib.auth.views import (
    login, logout, password_reset, password_reset_done, password_reset_confirm,
    password_reset_complete
)

app_name = "accounts"

urlpatterns = [
    re_path(r'^$', views.home, name='home'),
    re_path(r'^login/$', login, {'template_name': 'accounts/login.html'},
            name='login'),
    re_path(r'^logout/$', logout, {'template_name': 'accounts/logout.html'},
            name='logout'),
    re_path(r'^register/$', views.register, name='register'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/'
            r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            views.activate, name='activate'),
    re_path(r'^profile/$', views.view_profile, name='view_profile'),
    re_path(r'^profile/(?P<pk>\d+)/$', views.view_profile,
            name='view_profile_with_pk'),
    re_path(r'^profile/edit/$', views.edit_profile, name='edit_profile'),
    re_path(r'^change-password/$', views.change_password,
            name='change_password'),
    re_path(r'^reset-password/$', password_reset,
            {'template_name': 'accounts/reset_password.html',
             'post_reset_redirect': 'accounts:password_reset_done',
             'email_template_name': 'accounts/reset_password_email.html'},
            name='reset_password'),
    re_path(r'^reset-password/done$', password_reset_done,
            {'template_name': 'accounts/reset_password_done.html'},
            name='password_reset_done'),
    re_path(r'^reset-password/confirm(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
            password_reset_confirm,
            {'template_name': 'accounts/reset_password_confirm.html',
             'post_reset_redirect': 'accounts:password_reset_complete'},
            name='password_reset_confirm'),
    re_path(r'^reset-password/complete/$', password_reset_complete,
            {'template_name': 'accounts/reset_password_complete.html'},
            name='password_reset_complete')
]
