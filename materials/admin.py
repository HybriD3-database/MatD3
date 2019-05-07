import nested_admin

from django.contrib import admin
from django.utils import timezone

from . import models


class BaseAdmin(nested_admin.NestedModelAdmin):
    readonly_fields = ('id', 'created_by', 'created', 'updated_by', 'updated')

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        obj.updated = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if not hasattr(instance, 'created_by'):
                instance.created_by = request.user
            instance.updated_by = request.user
            instance.updated = timezone.now()
            instance.save()
        formset.save_m2m()


class BaseInline(nested_admin.NestedStackedInline):
    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(models.System)
admin.site.register(models.Reference)
admin.site.register(models.Author)


class PropertyAdmin(BaseAdmin):
    list_display = ('name', 'id', 'created_by', 'updated_by', 'updated')
    fieldsets = (
        ('', {
            'fields': ('name', 'require_input_files'),
        }),
        ('Meta', {'fields': BaseAdmin.readonly_fields}),
    )


admin.site.register(models.Property, PropertyAdmin)


class UnitAdmin(BaseAdmin):
    list_display = ('label', 'id', 'created_by', 'updated_by', 'updated')
    fieldsets = (
        ('', {
            'fields': ('label',),
        }),
        ('Meta', {'fields': BaseAdmin.readonly_fields}),
    )


admin.site.register(models.Unit, UnitAdmin)


class CommentInline(BaseInline):
    model = models.Comment
    verbose_name_plural = ''
    fields = ['text']


class SynthesisAdmin(BaseAdmin):
    list_display = ('id', 'created_by', 'updated_by', 'updated')
    fields = [f.name for f in models.SynthesisMethod._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.SynthesisMethod, SynthesisAdmin)


class ExperimentalAdmin(BaseAdmin):
    list_display = ('id', 'created_by', 'updated_by', 'updated')
    fields = [f.name for f in models.ExperimentalDetails._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.ExperimentalDetails, ExperimentalAdmin)


class ComputationalAdmin(BaseAdmin):
    list_display = ('id', 'created_by', 'updated_by', 'updated')
    fields = [f.name for f in models.ComputationalDetails._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.ComputationalDetails, ComputationalAdmin)


class NumericalValueInline(BaseInline):
    model = models.NumericalValue
    extra = 0
    verbose_name_plural = ''
    fields = ['qualifier', 'value']


class DatapointInline(BaseInline):
    model = models.Datapoint
    extra = 0
    verbose_name_plural = ''
    fields = ['id']
    inlines = [NumericalValueInline]


class DataseriesAdmin(BaseAdmin):
    list_display = ('id', 'created_by', 'updated_by', 'updated')
    fields = [f.name for f in models.Dataseries._meta.local_fields]
    inlines = [DatapointInline]


admin.site.register(models.Dataseries, DataseriesAdmin)


class SynthesisInline(BaseInline):
    model = models.SynthesisMethod
    fields = SynthesisAdmin.fields
    inlines = [CommentInline]
    extra = 0


class ExperimentalInline(BaseInline):
    model = models.ExperimentalDetails
    fields = ExperimentalAdmin.fields
    inlines = [CommentInline]
    extra = 0


class ComputationalInline(BaseInline):
    model = models.ComputationalDetails
    fields = ComputationalAdmin.fields
    inlines = [CommentInline]
    extra = 0


class DataseriesInline(BaseInline):
    model = models.Dataseries
    extra = 0
    fields = [f.name for f in models.Dataseries._meta.local_fields]


class FilesInline(BaseInline):
    model = models.DatasetFile
    fields = [f.name for f in models.DatasetFile._meta.local_fields]
    extra = 0


class DatasetAdmin(BaseAdmin):
    list_display = ('id', 'primary_property', 'label', 'created_by',
                    'updated_by', 'updated')
    list_filter = ('updated',)
    ordering = ('-updated',)
    fields = [f.name for f in models.Dataset._meta.local_fields]
    inlines = (SynthesisInline, ExperimentalInline, ComputationalInline,
               DataseriesInline, FilesInline)


admin.site.register(models.Dataset, DatasetAdmin)
