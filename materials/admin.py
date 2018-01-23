# -*- coding: utf-8 -*-


from django.contrib import admin

from materials.models import Tag, System, AtomicPositions, Publication, Author, Phase, ExcitonEmission, BandGap, BandStructure

admin.site.register(System)
admin.site.register(AtomicPositions)
admin.site.register(Publication)
admin.site.register(Author)
admin.site.register(Phase)
admin.site.register(ExcitonEmission)
admin.site.register(BandGap)
admin.site.register(BandStructure)
admin.site.register(Tag)
# Register your models here.
