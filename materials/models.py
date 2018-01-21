# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.db import models
from os.path import basename
import os

UserProfile = "accounts.UserProfile"
# Create your models here.
class Post(models.Model):
    post = models.CharField(max_length=500)

class Author(models.Model):
    """Contain data of authors"""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    institution = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.first_name + " " + self.last_name + " " + self.institution

class Publication(models.Model):
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    title = models.CharField(max_length=100) #what's a good title?
    journal = models.CharField(max_length=100, blank=True)
    vol = models.CharField(max_length=100) #should I use Integer or char?
    pages_start = models.CharField(max_length=10)
    pages_end = models.CharField(max_length=10)
    year = models.CharField(max_length=4) #OR models.DateField() #what's a good title?
    doi_isbn = models.CharField(max_length=30, blank=True)

    def __unicode__(self):
        return self.title

def file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s_%s_%s_apos.%s" % (instance.phase, instance.system.organic, instance.system.inorganic, ext)
    return os.path.join('uploads', filename)

def pl_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s_%s_%s_pl.%s" % (instance.phase, instance.system.organic, instance.system.inorganic, ext)
    return os.path.join('uploads', filename)

class Tag(models.Model):
    tag = models.CharField(max_length=50)

    def __unicode__(self):
        return self.tag

    # Add Contributor class
class System(models.Model):
    """Contains meta data for investigated system. """
    # use fhi file format.
    compound_name = models.CharField(max_length=100)
    group = models.CharField(max_length=30)
    formula = models.CharField(max_length=100)
    organic = models.CharField(max_length=30)
    inorganic = models.CharField(max_length=30)
    last_update = models.DateField(default=datetime.now)
    description = models.TextField(max_length=100, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __unicode__(self):
        return self.compound_name

class Phase(models.Model):
    phase = models.CharField(max_length=50)

    def __unicode__(self):
        return self.phase

class IDInfo(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    contributor = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    temperature = models.CharField(max_length=20, blank=True)
    phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
    method = models.CharField(max_length=100)
    specific_method = models.CharField(max_length=100)
    comments = models.CharField(max_length=1000, blank=True)

class ExcitonEmission(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    pl_file = models.FileField(upload_to=pl_file_name, blank=True)
    exciton_emission = models.DecimalField(max_digits=7, decimal_places=4)

    def __unicode__(self):
        return str(self.exciton_emission)

class BandGap(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    band_gap = models.CharField(max_length=10)

    def __unicode__(self):
        return self.band_gap

class BandStructure(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    band_structure = models.CharField(max_length=100)

    def __unicode__(self):
        return self.band_structure

class BondAngle(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_angle = models.CharField(max_length=100, blank=True)
    mhm_angle = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.hmh_angle + " " + self.mhm_angle

class BondLength(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_length = models.CharField(max_length=100, blank=True)
    mhm_length = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.hmh_length + " " + self.mhm_length

class AtomicPositions(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    fhi_file = models.FileField(upload_to=file_name, blank=True)
    a = models.CharField(max_length=10)
    b = models.CharField(max_length=10)
    c = models.CharField(max_length=10)
    alpha = models.CharField(max_length=10)
    beta = models.CharField(max_length=10)
    gamma = models.CharField(max_length=10)
    volume = models.CharField(max_length=10, blank=True)
    Z = models.CharField(max_length=10, blank=True)

    def __unicode__(self):
        return self.phase.phase + " " + self.system.formula
