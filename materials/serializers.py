# This file is covered by the BSD license. See LICENSE in the root directory.
from rest_framework import serializers

from . import models


class BaseSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    updated_by = serializers.StringRelatedField()

    class Meta:
        fields = (
            "created",
            "created_by",
            "updated",
            "updated_by",
        )


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Author
        fields = ("first_name", "last_name", "institution")


class ReferenceSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = models.Reference
        fields = (
            "pk",
            "authors",
            "title",
            "journal",
            "vol",
            "pages_start",
            "pages_end",
            "year",
            "doi_isbn",
        )


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ("pk", "name", "method")


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Unit
        fields = ("pk", "label")


class ComputationalSerializer(BaseSerializer):
    comment = serializers.StringRelatedField()

    class Meta:
        model = models.ComputationalDetails
        fields = BaseSerializer.Meta.fields + (
            "pk",
            "code",
            "level_of_theory",
            "xc_functional",
            "k_point_grid",
            "level_of_relativity",
            "basis_set_definition",
            "numerical_accuracy",
            "comment",
        )


class SynthesisSerializer(BaseSerializer):
    comment = serializers.StringRelatedField()

    class Meta:
        model = models.SynthesisMethod
        fields = BaseSerializer.Meta.fields + (
            "pk",
            "starting_materials",
            "product",
            "description",
            "comment",
        )


class ExperimentalSerializer(BaseSerializer):
    comment = serializers.StringRelatedField()

    class Meta:
        model = models.ExperimentalDetails
        fields = BaseSerializer.Meta.fields + (
            "pk",
            "method",
            "description",
            "comment",
        )


class NumericalValueSerializer(BaseSerializer):
    qualifier = serializers.CharField(source="get_qualifier_display")

    class Meta:
        model = models.NumericalValue
        fields = (
            "qualifier",
            "formatted",
        )


class DatapointSerializer(BaseSerializer):
    values = NumericalValueSerializer(many=True)

    class Meta:
        model = models.Datapoint
        fields = ("values",)


class FixedValueSerializer(BaseSerializer):
    class Meta:
        model = models.NumericalValueFixed
        depth = 1
        fields = (
            "physical_property",
            "unit",
            "subset",
            "error",
            "upper_bound",
            "formatted",
        )


class SubsetSerializer(BaseSerializer):
    crystal_system = serializers.CharField(source="get_crystal_system_display")
    datapoints = DatapointSerializer(many=True)
    fixed_values = FixedValueSerializer(many=True)

    class Meta:
        model = models.Subset
        depth = 1
        fields = (
            "pk",
            "label",
            "crystal_system",
            "fixed_values",
            "datapoints",
        )


class DatasetSerializer(BaseSerializer):
    sample_type = serializers.CharField(source="get_sample_type_display")
    subsets = SubsetSerializer(many=True)

    class Meta:
        model = models.Dataset
        depth = 1
        fields = BaseSerializer.Meta.fields + (
            "pk",
            "caption",
            "system",
            "primary_property",
            "primary_unit",
            "secondary_property",
            "secondary_unit",
            "reference",
            "visible",
            "is_experimental",
            # "dimensionality",
            "sample_type",
            "extraction_method",
            "representative",
            "linked_to",
            "verified_by",
            "computational",
            "synthesis",
            "experimental",
            "subsets",
            "space_group",
        )


class DatasetSerializerInfo(serializers.ModelSerializer):
    sample_type = serializers.CharField(source="get_sample_type_display")

    class Meta:
        model = models.Dataset
        depth = 1
        fields = (
            "pk",
            "caption",
            "system",
            "primary_property",
            "primary_unit",
            "secondary_property",
            "secondary_unit",
            "reference",
            "is_experimental",
            # "dimensionality",
            "sample_type",
            "extraction_method",
        )


class DatasetSerializerSummary(serializers.ModelSerializer):
    sample_type = serializers.CharField(source="get_sample_type_display")

    class Meta:
        model = models.Dataset
        fields = (
            "pk",
            "caption",
            "system",
            "primary_property",
            "primary_unit",
            "secondary_property",
            "secondary_unit",
            "reference",
            "is_experimental",
            # "dimensionality",
            "sample_type",
        )


# Define the DIMENSIONALITIES mapping
DIMENSIONALITIES = {
    4: 3,
    3: 2.5,
    2: 2,
    1: 1,
    0: 0,
}

# Serializer for System_Stoichiometry (single field for stoichiometry)
class SystemStoichiometrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.System_Stoichiometry
        fields = ("stoichiometry",)


# SystemSerializer with a custom field for stoichiometry
class SystemSerializer(serializers.ModelSerializer):
    stoichiometry = serializers.SerializerMethodField()
    # dimensionality = serializers.SerializerMethodField()

    class Meta:
        model = models.System
        fields = (
            "pk",
            "compound_name",
            "formula",
            "group",
            "organic",
            "inorganic",
            "iupac",
            "last_update",
            "derived_to_from",
            "description",
            "dimensionality",
            "n",
            "stoichiometry",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["dimensionality"] = DIMENSIONALITIES.get(
            instance.dimensionality, None
        )
        return representation

    def get_stoichiometry(self, obj):
        # Retrieve the first related System_Stoichiometry instance
        stoichiometry_set = obj.system_stoichiometry_set.first()
        if stoichiometry_set:
            # Return only the stoichiometry value as a plain string
            return stoichiometry_set.stoichiometry
        else:
            return None  # or a default message if no stoichiometry is found

    def get_dimensionality(self, obj):
        # Map the dimensionality value based on the defined DIMENSIONALITIES mapping
        return DIMENSIONALITIES.get(
            obj.dimensionality, None
        )  # Returns None if not in mapping
