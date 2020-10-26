# This file is covered by the BSD license. See LICENSE in the root directory.
"""MatD3 URL Configuration.

"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import generic

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('contact/', generic.TemplateView.as_view(
        template_name='mainproject/contact.html'), name='contact'),
    path('contributors/', views.contributors, name='contributors'),
    path('materials/', include('materials.urls')),
    path('accounts/', include('accounts.urls')),
    path('nested_admin/', include('nested_admin.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
