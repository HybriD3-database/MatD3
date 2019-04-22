from django.contrib import admin

from . import models


class BandStructureAdmin(admin.ModelAdmin):
    list_display = ('system', 'folder_location')


admin.site.register(models.System)
admin.site.register(models.Reference)
admin.site.register(models.Author)
admin.site.register(models.Phase)
admin.site.register(models.ExcitonEmission)
admin.site.register(models.SynthesisMethodOld)
admin.site.register(models.BandStructure, BandStructureAdmin)
admin.site.register(models.Tag)
admin.site.register(models.Method)
admin.site.register(models.SpecificMethod)
