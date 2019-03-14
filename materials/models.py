import logging
import os
import shutil

from django.db import models
from django.contrib.auth import get_user_model

from mainproject import settings


logger = logging.getLogger(__name__)


class Base(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    this = '%(app_label)s_%(class)s'
    created_by = models.ForeignKey(get_user_model(),
                                   related_name=f'{this}_created_by',
                                   on_delete=models.PROTECT)
    updated_by = models.ForeignKey(get_user_model(),
                                   related_name=f'{this}_updated_by',
                                   on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def save(self, user=None, *args, **kwargs):
        if user:
            self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)


class Property(Base):
    name = models.CharField(max_length=60, unique=True)
    require_input_files = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Unit(Base):
    label = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.label


def file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = '%s_%s_%s_apos.%s' % (instance.phase, instance.system.organic,
                                     instance.system.inorganic, ext)
    return os.path.join('uploads', filename)


def pl_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = '%s_%s_%s_pl.%s' % (instance.phase, instance.system.organic,
                                   instance.system.inorganic, ext)
    return os.path.join('uploads', filename)


def syn_file_name(instance, filename):
    filename = '%s_%s_%s_syn.txt' % (instance.phase, instance.system.organic,
                                     instance.system.inorganic)
    return os.path.join('uploads', filename)


class Publication(models.Model):
    author_count = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=1000)
    journal = models.CharField(max_length=500, blank=True)
    vol = models.CharField(max_length=100)
    pages_start = models.CharField(max_length=10)
    pages_end = models.CharField(max_length=10)
    year = models.CharField(max_length=4)
    doi_isbn = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title

    def getAuthorsAsString(self):
        names = ', '.join([f'{x.first_name[0]}. {x.last_name}' for
                           x in self.author_set.all()])
        if names:
            names += ','
        return names

    def getAuthors(self):
        return self.author_set.all()


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100, blank=True)
    publication = models.ManyToManyField(Publication)

    def __str__(self):
        value = (self.first_name + ' ' + self.last_name + ', ' +
                 self.institution)
        if len(value) > 45:
            value = value[:42] + '...'
        return value

    def splitFirstName(self):
        return self.first_name.split()


class Tag(models.Model):
    tag = models.CharField(max_length=100)

    def __str__(self):
        return self.tag


class System(models.Model):
    """Contains meta data for investigated system."""
    compound_name = models.CharField(max_length=1000)
    formula = models.CharField(max_length=200)
    group = models.CharField(max_length=100)  # aka Alternate names
    organic = models.CharField(max_length=100)
    inorganic = models.CharField(max_length=100)
    last_update = models.DateField(auto_now=True)
    description = models.TextField(max_length=1000, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.compound_name

    def listAlternateNames(self):
        return self.group.replace(',', ' ').split()

    def listProperties(self):
        L = []
        for mat_prop in self.materialproperty_set.all():
            property = mat_prop.property
            if property not in L:
                L.append(property)
        return L

    def getAuthors(self):
        """Returns a list of authors related to a system.

        An author appears no more than once.

        """
        def authorSort(author):  # function that decides author sort criteria
            return author.last_name

        L = []
        for dataType in [self.atomicpositions_set, self.synthesismethodold_set,
                         self.excitonemission_set, self.bandstructure_set]:
            for data in dataType.all():
                for author in data.publication.author_set.all():
                    if author not in L:  # don't add duplicate authors
                        L.append(author)

        return sorted(L, key=authorSort)


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


class PropertyOld(models.Model):
    property = models.CharField(max_length=500)

    class Meta:
        verbose_name_plural = 'properties'

    def __str__(self):
        return self.property


class IDInfo(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    source = models.CharField(max_length=500)
    data_extraction_method = models.CharField(max_length=500)
    contributor = models.ForeignKey('accounts.UserProfile',
                                    on_delete=models.PROTECT)
    temperature = models.CharField(max_length=20, blank=True)
    phase = models.ForeignKey(Phase, on_delete=models.PROTECT)
    method = models.ForeignKey(Method, on_delete=models.PROTECT, null=True)
    specific_method = models.ForeignKey(SpecificMethod,
                                        on_delete=models.PROTECT, null=True)
    comments = models.CharField(max_length=1000, blank=True)
    last_update = models.DateField(auto_now=True)

    def getAuthors(self):
        return self.publication.getAuthors()


class SynthesisMethodOld(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    synthesis_method = models.TextField(max_length=1000, blank=True)
    starting_materials = models.TextField(max_length=1000, blank=True)
    remarks = models.TextField(max_length=1000, blank=True)
    product = models.TextField(max_length=1000, blank=True)
    syn_file = models.FileField(upload_to=syn_file_name, blank=True)

    def __str__(self):
        return (self.system.compound_name + ' synthesis #' +
                str(self.methodNumber()))

    def methodNumber(self):
        for i, obj in enumerate(self.system.synthesismethodold_set.all()):
            if obj.pk == self.pk:
                return i + 1


class ExcitonEmission(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    exciton_emission = models.DecimalField(max_digits=7, decimal_places=4)
    pl_file = models.FileField(upload_to=pl_file_name, blank=True)
    plotted = models.BooleanField(default=False)
    synthesis_method = models.ForeignKey(SynthesisMethodOld,
                                         on_delete=models.PROTECT, null=True,
                                         blank=True)

    def __str__(self):
        return str(self.exciton_emission)

    def delete(self, *args, **kwargs):
        if(self.pl_file):
            file_loc = os.path.join(settings.MEDIA_ROOT, 'uploads',
                                    str(self.pl_file).split('/')[1])
            if os.path.isfile(file_loc):
                os.remove(file_loc)
        super().delete(*args, **kwargs)


class BandStructure(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    band_gap = models.CharField(max_length=10, blank=True)
    folder_location = models.CharField(max_length=500, blank=True)
    plotted = models.BooleanField(default=False)
    visible = models.BooleanField(default=False)
    synthesis_method = models.ForeignKey(SynthesisMethodOld,
                                         on_delete=models.PROTECT, null=True,
                                         blank=True)

    def __str__(self):
        return self.folder_location

    def getFullBSPath(self):
        path = (
            '../../media/uploads/%s_%s_%s_%s_bs/%s_%s_%s_%s_bs_full.png' %
            (self.phase, self.system.organic, self.system.inorganic, self.pk,
             self.phase, self.system.organic, self.system.inorganic, self.pk))
        return path

    def getMiniBSPath(self):
        path = (
            '../../media/uploads/%s_%s_%s_%s_bs/%s_%s_%s_%s_bs_min.png' %
            (self.phase, self.system.organic, self.system.inorganic, self.pk,
             self.phase, self.system.organic, self.system.inorganic, self.pk))
        return path

    def delete(self, *args, **kwargs):
        folder_loc = os.path.join(settings.MEDIA_ROOT, self.folder_location)
        if os.path.isdir(folder_loc):
            shutil.rmtree(folder_loc)
        super().delete(*args, **kwargs)


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
    synthesis_method = models.ForeignKey(SynthesisMethodOld,
                                         on_delete=models.PROTECT, null=True,
                                         blank=True)

    class Meta:
        verbose_name_plural = 'atomic positions'

    def __str__(self):
        return self.phase.phase + ' ' + self.system.formula

    def delete(self, *args, **kwargs):
        if(self.fhi_file):
            file_loc = os.path.join(settings.MEDIA_ROOT, 'uploads',
                                    str(self.fhi_file).split('/')[1])
            if os.path.isfile(file_loc):
                os.remove(file_loc)
        super().delete(*args, **kwargs)


class MaterialProperty(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    property = models.ForeignKey(PropertyOld, on_delete=models.PROTECT)
    value = models.CharField(max_length=500)

    class Meta:
        verbose_name_plural = 'material properties'

    def __str__(self):
        return str(self.system) + ' ' + str(self.property) + ': ' + self.value


class BondAngle(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_angle = models.CharField(max_length=100, blank=True)
    mhm_angle = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.hmh_angle + ' ' + self.mhm_angle


class BondLength(IDInfo):
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    hmh_length = models.CharField(max_length=100, blank=True)
    mhm_length = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.hmh_length + ' ' + self.mhm_length


class Dataset(Base):
    # Files associated with each dataset are uploaded in
    # media/uploads/dataset_{{ pk }}
    SINGLE_CRYSTAL = 0
    POWDER = 1
    FILM = 2
    SAMPLE_TYPES = (
        (SINGLE_CRYSTAL, 'single crystal'),
        (POWDER, 'powder'),
        (FILM, 'film'),
    )
    TRICLINIC = 0
    MONOCLINIC = 1
    ORTHORHOMBIC = 2
    TETRAGONAL = 3
    TRIGONAL = 4
    HEXAGONAL = 5
    CUBIC = 6
    CRYSTAL_SYSTEMS = (
        (TRICLINIC, 'triclinic'),
        (MONOCLINIC, 'monoclinic'),
        (ORTHORHOMBIC, 'orthorhombic'),
        (TETRAGONAL, 'tetragonal'),
        (TRIGONAL, 'trigonal'),
        (HEXAGONAL, 'hexagonal'),
        (CUBIC, 'cubic'),
    )
    label = models.TextField(max_length=1000)
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    primary_property = models.ForeignKey(
        Property, null=True, on_delete=models.PROTECT,
        related_name='primary_property')
    primary_unit = models.ForeignKey(
        Unit, null=True, on_delete=models.PROTECT, related_name='primary_unit')
    secondary_property = models.ForeignKey(
        Property, null=True, on_delete=models.PROTECT,
        related_name='secondary_property')
    secondary_unit = models.ForeignKey(
        Unit, null=True, on_delete=models.PROTECT,
        related_name='secondary_unit')
    reference = models.ForeignKey(Publication, on_delete=models.PROTECT)
    visible = models.BooleanField()
    plotted = models.BooleanField()
    has_files = models.BooleanField()
    experimental = models.BooleanField()  # theoretical if false
    dimensionality = models.PositiveSmallIntegerField(choices=((2, 2), (3, 3)))
    sample_type = models.PositiveSmallIntegerField(choices=SAMPLE_TYPES)
    crystal_system = models.PositiveSmallIntegerField(choices=CRYSTAL_SYSTEMS)

    def delete(self, *args, **kwargs):
        """Additionally remove any files uploaded by the user."""
        if self.has_files:
            loc = os.path.join(settings.MEDIA_ROOT,
                               f'uploads/dataset_{self.pk}')
            for file_ in os.listdir(loc):
                logger.info(f'deleting input_files/dataset_{self.pk}/{file_}')
            shutil.rmtree(loc)
        if self.primary_property and self.primary_property.require_input_files:
            loc = os.path.join(settings.MEDIA_ROOT,
                               f'input_files/dataset_{self.pk}')
            for file_ in os.listdir(loc):
                logger.info(f'deleting input_files/dataset_{self.pk}/{file_}')
            shutil.rmtree(loc)
        super().delete(*args, **kwargs)


class Dataseries(Base):
    label = models.CharField(max_length=100, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)


class Datapoint(Base):
    dataseries = models.ForeignKey(Dataseries, on_delete=models.CASCADE)


class NumericalValueBase(Base):
    ACCURATE = 0
    APPROXIMATE = 1
    LOWER_BOUND = 2
    UPPER_BOUND = 3
    ERROR = 4
    VALUE_TYPES = (
        (ACCURATE, 'accurate'),
        (APPROXIMATE, 'approximate'),
        (LOWER_BOUND, 'lower_bound'),
        (UPPER_BOUND, 'upper_bound'),
        (ERROR, 'error'),
    )
    value = models.FloatField()
    value_type = models.PositiveSmallIntegerField(choices=VALUE_TYPES)

    class Meta:
        abstract = True


class NumericalValue(NumericalValueBase):
    PRIMARY = 0
    SECONDARY = 1
    QUALIFIER_TYPES = (
        (PRIMARY, 'primary'),
        (SECONDARY, 'secondary'),
    )
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE)
    qualifier = models.PositiveSmallIntegerField(choices=QUALIFIER_TYPES)


class DatapointSymbol(Base):
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)


class NumericalValueFixed(NumericalValueBase):
    physical_property = models.ForeignKey(Property, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    dataset = models.ForeignKey(Dataset, null=True, on_delete=models.CASCADE)
    dataseries = models.ForeignKey(Dataseries, null=True,
                                   on_delete=models.CASCADE)


class ComputationalDetails(Base):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    code = models.CharField(max_length=40)
    level_of_theory = models.CharField(max_length=50)
    xc_functional = models.CharField(max_length=50)
    kgrid = models.CharField(max_length=40)
    relativity_level = models.CharField(max_length=40)
    basis = models.CharField(max_length=100)
    numerical_accuracy = models.CharField(max_length=500)


class ExperimentalDetails(Base):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)


class SynthesisMethod(Base):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    starting_materials = models.TextField(max_length=1000, blank=True)
    product = models.TextField(max_length=1000, blank=True)
    description = models.TextField(max_length=1000, blank=True)


class Comment(Base):
    computational_details = models.ForeignKey(ComputationalDetails, null=True,
                                              on_delete=models.CASCADE)
    experimental_details = models.ForeignKey(ExperimentalDetails, null=True,
                                             on_delete=models.CASCADE)
    synthesis_method = models.ForeignKey(SynthesisMethod, null=True,
                                         on_delete=models.CASCADE)
    text = models.TextField(max_length=500)

    def __str__(self):
        return self.text
