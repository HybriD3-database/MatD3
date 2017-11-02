# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from os.path import basename

# Create your models here.

class Author(models.Model):
    """Contain data of authors """
    article_title = models.CharField(max_length=300) #what's a good title?
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    pub_title = models.CharField(max_length=100) #what's a good title?
    pub_vol = models.CharField(max_length=100) #should I use Integer or char?
    pub_pages_start = models.CharField(max_length=10)
    pub_pages_end = models.CharField(max_length=10)
    pub_year = models.CharField(max_length=4) #OR models.DateField() #what's a good title?
    doi_isbn = models.CharField(max_length=30)

    def __unicode__(self):
        return self.first_name+" "+self.last_name

class Contributor(models.Model):
    """Contain data of contributor """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    date = models.DateField()

    def __unicode__(self):
        return self.first_name+" "+self.last_name

    # Add Contributor class
class System(models.Model):
    """Contains meta data for investigated system. """
    # use fhi file format.
    compound_name = models.CharField(max_length=100) # Name of the system: Alanine/ Alanine+Ca2+/ GLycine+Ba2+ etc.
    #urlname = models.CharField(max_length=100) # Name which appearl in url
    group = models.CharField(max_length=10) # Short name used in database, ala/gly/argH/ etc.
    tags = models.CharField(max_length=100) # General tags for the sytem
    organic = models.CharField(max_length=30)
    inorganic = models.CharField(max_length=10)
    # authors = models.ManyToManyField(Author)  # There is no need thos anymore
    formula = models.CharField(max_length=100) # Simple chemical formula of the system
    # charge = models.FloatField() # Do we have charge?
    # citation = models.CharField(max_length=200) # Possible citation/ citations where system was published
    last_update = models.DateField() # when system was last time updated
    desc = models.TextField(max_length=100) # Description of the system if provided

    """Parameters I need for this.
    What are the parameters we need for AtomicPositions, do we need crystal phase? Are there
    Atomic Positions - included
    Band Gaps
    Band Structure
    Excition emission
    """

    def __unicode__(self):
        return self.compound_name

class Phase(models.Model):
    phase = models.CharField(max_length=20)

    def __unicode__(self):
        return self.phase

class Temperature(models.Model):
    temperature = models.CharField(max_length=10)

    def __unicode__(self):
        return self.temperature

class ExcitonEmission(models.Model):
    # might link to atomic measurements
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    temperature = models.ForeignKey(Temperature, max_length=4)
    exciton_emission = models.CharField(max_length=10)
    contributor = models.ForeignKey(Contributor, on_delete=models.PROTECT, null=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, null=True)
    method = models.CharField(max_length=20)

    def __unicode__(self):
        return self.exciton_emission

class BandGap(models.Model):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    temperature = models.ForeignKey(Temperature, max_length=4)
    band_gap = models.CharField(max_length=10)
    contributor = models.ForeignKey(Contributor, on_delete=models.PROTECT, null=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, null=True)
    method = models.CharField(max_length=20)

    def __unicode__(self):
        return self.band_gap

class BandStructure(models.Model):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    temperature = models.ForeignKey(Temperature, max_length=4)
    band_structure = models.CharField(max_length=100)
    contributor = models.ForeignKey(Contributor, on_delete=models.PROTECT, null=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, null=True)
    method = models.CharField(max_length=20)

    def __unicode__(self):
        return self.band_structure
"""
To be added
"""
# class AngleVariance(models.model):
#     temperature = models.CharField(max_length=10)
#
#     def __unicode__(self):
#         return self.
#
# class QuadraticElongation(models.model):
#     temperature = models.CharField(max_length=10)
#
#     def __unicode__(self):
#         return self.temperature

class AtomicPositions(models.Model):
    # Link two different kinds of lists, one for calculated, another for x-ray diffracted
    contributor = models.ForeignKey(Contributor, on_delete=models.PROTECT)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    system = models.ForeignKey(System, on_delete=models.PROTECT) #protect from deletion
    method = models.CharField(max_length=20) # PBE+vdW for example. [Be specific]
    temperature = models.ForeignKey(Temperature, on_delete=models.PROTECT)
    phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
    a = models.CharField(max_length=10)
    b = models.CharField(max_length=10)
    c = models.CharField(max_length=10)
    alpha = models.CharField(max_length=10)
    beta = models.CharField(max_length=10)
    gamma = models.CharField(max_length=10)
    """
    Atomic Pos Measurement
    """
    # angle_variance = models.ManyToManyField(AngleVariance)
    code = models.CharField(max_length=30)
    codeversion = models.CharField(max_length=10) # Do we need this?

    # hierarcy_file = models.CharField(max_length=100) # Energy hierarchy file generated

    def __unicode__(self):
        return self.method #to be updated when there's a better method

    # class Meta:
    #       unique_together = ("aminoacid", "capping","ion")

# class Conformer(models.Model):
#     """Contain one conformer for given system"""
#     filename = models.CharField(max_length=100,unique=True) # Filename/ location of file
#     energy = models.FloatField() # Total energy obtained for this conformation
#     system = models.ForeignKey(System) # To which sytem this conformer belongs to
#     last_update = models.DateField() # When this was last time updated
#
#     def __unicode__(self):
#         return self.system.name +" : "+ basename(self.filename)
#
#
# class Extrafile(models.Model):
#     """Contain extra output file and description for given system """
#     system = models.ForeignKey(System) # Which system this file belongs to
#     desc = models.CharField(max_length=200) # Short description of file
#     filename = models.CharField(max_length=100) # location of file
#
#     def __unicode__(self):
#         return self.system.name + " " + basename(self.filename)
