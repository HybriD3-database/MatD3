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
