# -*- coding: utf-8 -*-


from django.contrib import admin

from materials.models import Tag, System, AtomicPositions, Publication, Author, Phase, ExcitonEmission, BandGap, BandStructure, Method, SpecificMethod

admin.site.register(System)
admin.site.register(AtomicPositions)
admin.site.register(Publication)
admin.site.register(Author)
admin.site.register(Phase)
admin.site.register(ExcitonEmission)
admin.site.register(BandGap)
admin.site.register(BandStructure)
admin.site.register(Tag)
admin.site.register(Method)
admin.site.register(SpecificMethod)
# Register your models here.
