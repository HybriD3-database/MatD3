# This file is covered by the BSD license. See LICENSE in the root directory.
from rest_framework import serializers

from . import models


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Author
        fields = ('first_name', 'last_name', 'institution')


class ReferenceSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = models.Reference
        fields = ('pk',
                  'authors',
                  'title',
                  'journal',
                  'vol',
                  'pages_start',
                  'pages_end',
                  'year',
                  'doi_isbn')


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.System
        fields = ('pk',
                  'compound_name',
                  'formula',
                  'group',
                  'inorganic',
                  'last_update',
                  'description')


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ('pk', 'name')


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Unit
        fields = ('pk', 'label')


class DatasetSerializerInfo(serializers.ModelSerializer):
    system = serializers.StringRelatedField()
    primary_property = serializers.StringRelatedField()
    primary_unit = serializers.StringRelatedField()
    secondary_property = serializers.StringRelatedField()
    secondary_unit = serializers.StringRelatedField()
    sample_type = serializers.CharField(source='get_sample_type_display')

    class Meta:
        model = models.Dataset
        fields = ('pk',
                  'caption',
                  'system',
                  'primary_property',
                  'primary_unit',
                  'secondary_property',
                  'secondary_unit',
                  'reference',
                  'is_experimental',
                  'dimensionality',
                  'sample_type',
                  'extraction_method')


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dataset
        fields = ([f.name for f in models.Dataset._meta.local_fields])
