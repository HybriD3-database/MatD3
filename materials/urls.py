# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.views.generic import ListView, DetailView
from materials.models import System, AtomicPositions, Author, Contributor

# Create your tests here.

urlpatterns = [
        url(r'^$', ListView.as_view(queryset=System.objects.all().order_by("id"),
                                    template_name="materials/home.html")),
        url(r'^(?P<pk>\d+)$', DetailView.as_view(model=System, template_name="materials/system.html"))
                ]
