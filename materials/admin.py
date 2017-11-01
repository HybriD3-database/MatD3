# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from materials.models import System, AtomicPositions, Author, Contributor

admin.site.register(System)
admin.site.register(AtomicPositions)
admin.site.register(Author)
admin.site.register(Contributor)
# Register your models here.
