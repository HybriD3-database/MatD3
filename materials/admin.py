# This file is covered by the BSD license. See LICENSE in the root directory.
import nested_admin

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from . import models
from mainproject.settings import MATD3_NAME

from .models import System, System_Stoichiometry, Stoichiometry_Elements
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import re
from .utils import parse_formula

admin.site.site_header = mark_safe(f"{MATD3_NAME} database")


class BaseMixin:
    readonly_fields = ("id", "created_by", "created", "updated_by", "updated")

    def check_perm(self, user, obj=None):
        return (
            user.is_superuser
            or obj
            and (not hasattr(obj, "created_by") or obj.created_by == user)
        )

    def has_change_permission(self, request, obj=None):
        return self.check_perm(request.user, obj)

    def has_delete_permission(self, request, obj=None):
        return self.check_perm(request.user, obj)


class BaseAdmin(BaseMixin, nested_admin.NestedModelAdmin):
    def save_model(self, request, obj, form, change):
        if not hasattr(obj, "created_by"):
            obj.created_by = request.user
        obj.updated_by = request.user
        obj.updated = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if not hasattr(instance, "created_by"):
                instance.created_by = request.user
            instance.updated_by = request.user
            instance.updated = timezone.now()
            instance.save()
        formset.save_m2m()


# Inline for Stoichiometry Elements
class StoichiometryElementsInline(nested_admin.NestedTabularInline):
    model = Stoichiometry_Elements
    extra = 0
    verbose_name_plural = "Stoichiometry Elements"


# Inline for System Stoichiometry, now including Stoichiometry Elements
class SystemStoichiometryInline(nested_admin.NestedTabularInline):
    model = System_Stoichiometry
    extra = 0
    verbose_name_plural = "Stoichiometry"
    inlines = [StoichiometryElementsInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        Stoichiometry_Elements.objects.filter(system_stoichiometry=obj).delete()
        # Remove chiral prefixes
        formula = re.sub(r"(\(R/S\)-|\b[SR]-)", "", obj.stoichiometry)
        # Parse the formula using the same logic
        try:
            element_counts = parse_formula(formula)
        except Exception as e:
            # Handle parsing errors if necessary
            return
        for element, count in element_counts.items():
            if count == count.to_integral():
                count_formatted = str(count.to_integral())
            else:
                count_formatted = str(
                    count.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
                )
            Stoichiometry_Elements.objects.create(
                system_stoichiometry=obj,
                element=element,
                string_value=count_formatted,
                float_value=float(count),
            )


# SystemAdmin to include the Stoichiometry inline
class SystemAdmin(nested_admin.NestedModelAdmin):
    list_display = ("id", "compound_name")
    search_fields = ["id", "compound_name"]
    filter_horizontal = ["derived_to_from"]
    inlines = [SystemStoichiometryInline]


admin.site.register(System, SystemAdmin)


class AuthorAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "institution",
    )
    search_fields = [
        "id",
        "first_name",
        "last_name",
    ]


admin.site.register(models.Author, AuthorAdmin)


class ReferenceAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "id",
        "title",
        "journal",
        "year",
    )
    search_fields = [
        "id",
        "title",
        "journal",
    ]


admin.site.register(models.Reference, ReferenceAdmin)


class PropertyAdmin(BaseAdmin):
    list_display = ("id", "name", "created_by", "updated_by", "updated")
    search_fields = [
        "id",
        "name",
    ]
    ordering = [
        "name",
    ]


admin.site.register(models.Property, PropertyAdmin)


class UnitAdmin(BaseAdmin):
    list_display = ("id", "label", "created_by", "updated_by", "updated")
    search_fields = [
        "id",
        "label",
    ]
    fieldsets = (
        (
            "",
            {
                "fields": ("label",),
            },
        ),
        ("Meta", {"fields": BaseAdmin.readonly_fields}),
    )


admin.site.register(models.Unit, UnitAdmin)


class CommentInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Comment
    verbose_name_plural = ""
    fields = ["text"]


class SynthesisAdmin(BaseAdmin):
    list_display = ("id", "created_by", "updated_by", "updated")
    search_fields = [
        "id",
    ]
    fields = [f.name for f in models.SynthesisMethod._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.SynthesisMethod, SynthesisAdmin)


class ExperimentalAdmin(BaseAdmin):
    list_display = ("id", "created_by", "updated_by", "updated")
    search_fields = [
        "id",
    ]
    fields = [f.name for f in models.ExperimentalDetails._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.ExperimentalDetails, ExperimentalAdmin)


class ComputationalAdmin(BaseAdmin):
    list_display = ("id", "created_by", "updated_by", "updated")
    search_fields = [
        "id",
    ]
    fields = [f.name for f in models.ComputationalDetails._meta.local_fields]
    inlines = [CommentInline]


admin.site.register(models.ComputationalDetails, ComputationalAdmin)


class SpaceGroupAdmin(BaseAdmin):
    list_display = ("id", "value")
    search_fields = [
        "id",
    ]
    fields = [f.name for f in models.SpaceGroup._meta.local_fields]


admin.site.register(models.SpaceGroup, SpaceGroupAdmin)


class SpaceGroupInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.SpaceGroup
    extra = 0
    verbose_name_plural = ""
    fields = ["value"]


class SymbolInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Symbol
    extra = 0
    verbose_name_plural = ""
    fields = ["value"]


class ErrorInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Error
    extra = 0
    verbose_name_plural = ""
    fields = ["value"]


class UpperBoundInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.UpperBound
    extra = 0
    verbose_name_plural = ""
    fields = ["value"]


class NumericalValueInline(BaseMixin, nested_admin.NestedTabularInline):
    model = models.NumericalValue
    extra = 0
    verbose_name_plural = ""
    fields = ["qualifier", "value_type", "value"]
    inlines = [ErrorInline, UpperBoundInline]


class DatapointInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Datapoint
    extra = 0
    verbose_name_plural = ""
    fields = ["id"]
    inlines = [SymbolInline, NumericalValueInline]


class NumericalValueFixedForm(forms.ModelForm):
    """Needed to make the error field non-mandatory."""

    error = forms.FloatField(required=False)
    upper_bound = forms.FloatField(required=False)


class NumericalValueFixedInline(nested_admin.NestedTabularInline):
    model = models.NumericalValueFixed
    form = NumericalValueFixedForm
    extra = 0
    verbose_name_plural = "Fixed parameters"
    fields = (
        "physical_property",
        "value_type",
        "value",
        "error",
        "upper_bound",
        "unit",
    )


class SynthesisInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.SynthesisMethod
    fields = SynthesisAdmin.fields
    inlines = [CommentInline]
    extra = 0


class ExperimentalInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.ExperimentalDetails
    fields = ExperimentalAdmin.fields
    inlines = [CommentInline]
    extra = 0


class ComputationalInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.ComputationalDetails
    fields = ComputationalAdmin.fields
    inlines = [CommentInline]
    extra = 0


class SubsetInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Subset
    extra = 0
    fields = [f.name for f in models.Subset._meta.local_fields]
    inlines = [NumericalValueFixedInline]


class FilesInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.AdditionalFile
    fields = [f.name for f in models.AdditionalFile._meta.local_fields]
    extra = 0


class NotesInline(BaseMixin, nested_admin.NestedStackedInline):
    model = models.Note
    extra = 0


class DatasetAdmin(BaseAdmin):
    list_display = (
        "id",
        "primary_property",
        "caption",
        "created_by",
        "updated_by",
        "updated",
    )
    search_fields = [
        "id",
    ]
    list_filter = ("updated",)
    ordering = ("-updated",)
    fields = [f.name for f in models.Dataset._meta.local_fields] + ["linked_to"]
    inlines = (
        SynthesisInline,
        ExperimentalInline,
        ComputationalInline,
        SubsetInline,
        FilesInline,
        NotesInline,
    )
    filter_horizontal = ["linked_to"]

    def view_on_site(self, obj):
        return reverse("materials:dataset", kwargs={"pk": obj.pk})


admin.site.register(models.Dataset, DatasetAdmin)
