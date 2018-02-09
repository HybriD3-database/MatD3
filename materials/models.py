# -*- coding: utf-8 -*-
from datetime import datetime
from django.db import models
from os.path import basename
import os

UserProfile = "accounts.UserProfile"

def file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s_%s_%s_apos.%s" % (instance.phase, instance.system.organic, instance.system.inorganic, ext)
    return os.path.join('uploads', filename)

def pl_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s_%s_%s_pl.%s" % (instance.phase, instance.system.organic, instance.system.inorganic, ext)
    return os.path.join('uploads', filename)

# Create your models here.
class Post(models.Model):
    post = models.CharField(max_length=500)

class Author(models.Model):
    """Contain data of authors"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.first_name + " " + self.last_name + ", " + self.institution

class Publication(models.Model):
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    title = models.CharField(max_length=1000) #what's a good title?
    journal = models.CharField(max_length=500, blank=True)
    vol = models.CharField(max_length=100) #should I use Integer or char?
    pages_start = models.CharField(max_length=10)
    pages_end = models.CharField(max_length=10)
    year = models.CharField(max_length=4) #OR models.DateField() #what's a good title?
    doi_isbn = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title

class Tag(models.Model):
    tag = models.CharField(max_length=100)

    def __str__(self):
        return self.tag

    # Add Contributor class
class System(models.Model):
    """Contains meta data for investigated system. """
    # use fhi file format.
    compound_name = models.CharField(max_length=1000)
    group = models.CharField(max_length=100)
    formula = models.CharField(max_length=200)
    organic = models.CharField(max_length=100)
    inorganic = models.CharField(max_length=100)
    last_update = models.DateField(default=datetime.now)
    description = models.TextField(max_length=1000, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.formula

class Phase(models.Model):
    phase = models.CharField(max_length=50)

    def __str__(self):
        return self.phase

class Method(models.Model):
    method = models.CharField(max_length=100)

    def __str__(self):
        return self.method

class SpecificMethod(models.Model):
    specific_method = models.CharField(max_length=500)

    def __str__(self):
        return self.specific_method

class IDInfo(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    contributor = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    temperature = models.CharField(max_length=20, blank=True)
    phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
    method = models.ForeignKey(Method, on_delete=models.PROTECT, null=True)
    specific_method = models.ForeignKey(SpecificMethod, on_delete=models.PROTECT, null=True)
    comments = models.CharField(max_length=1000, blank=True)

class ExcitonEmission(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    exciton_emission = models.DecimalField(max_digits=7, decimal_places=4)
    pl_file = models.FileField(upload_to=pl_file_name, blank=True)

    def __str__(self):
        return str(self.exciton_emission)

class BandGap(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    band_gap = models.CharField(max_length=10)

    def __str__(self):
        return self.band_gap

class BandStructure(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    folder_location = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.folder_location

class BondAngle(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_angle = models.CharField(max_length=100, blank=True)
    mhm_angle = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.hmh_angle + " " + self.mhm_angle

class BondLength(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_length = models.CharField(max_length=100, blank=True)
    mhm_length = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.hmh_length + " " + self.mhm_length

class AtomicPositions(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    a = models.CharField(max_length=50)
    b = models.CharField(max_length=50)
    c = models.CharField(max_length=50)
    alpha = models.CharField(max_length=50)
    beta = models.CharField(max_length=50)
    gamma = models.CharField(max_length=50)
    volume = models.CharField(max_length=50, blank=True)
    Z = models.CharField(max_length=50, blank=True)
    fhi_file = models.FileField(upload_to=file_name, blank=True)

    def __str__(self):
        return self.phase.phase + " " + self.system.formula
