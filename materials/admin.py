# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from materials.models import System, AtomicPositions, Author, Contributor, Phase, Temperature, ExcitonEmission, BandGap, BandStructure

admin.site.register(System)
admin.site.register(AtomicPositions)
admin.site.register(Author)
admin.site.register(Contributor)
admin.site.register(Phase)
admin.site.register(Temperature)
admin.site.register(ExcitonEmission)
admin.site.register(BandGap)
admin.site.register(BandStructure)
# Register your models here.
