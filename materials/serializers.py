# This file is covered by the BSD license. See LICENSE in the root directory.
from rest_framework import serializers

from . import models


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ('pk', 'name')


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Unit
        fields = ('pk', 'label')
class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dataset
        fields = ([f.name for f in models.Dataset._meta.local_fields])
