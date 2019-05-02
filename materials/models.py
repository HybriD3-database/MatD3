import logging
import os
import shutil

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from mainproject import settings

logger = logging.getLogger(__name__)


class Base(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(default=timezone.now)
    this = '%(app_label)s_%(class)s'
    created_by = models.ForeignKey(get_user_model(),
                                   related_name=f'{this}_created_by',
                                   on_delete=models.PROTECT)
    updated_by = models.ForeignKey(get_user_model(),
                                   related_name=f'{this}_updated_by',
                                   on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'created_by' in kwargs and 'updated_by' not in kwargs:
            self.updated_by = self.created_by

    def __str__(self):
        return f'ID: {self.pk}'


class Property(Base):
    name = models.CharField(max_length=100, unique=True)
    require_input_files = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'properties'


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


class Reference(models.Model):
    author_count = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=1000)
    journal = models.CharField(max_length=500, blank=True)
    vol = models.CharField(max_length=100)
    pages_start = models.CharField(max_length=10)
    pages_end = models.CharField(max_length=10)
    year = models.CharField(max_length=4)
    doi_isbn = models.CharField(max_length=100, blank=True)

    def __str__(self):
        text = (f'{self.year} {"- " if self.year else ""} '
                f'{self.getAuthorsAsString()} {self.journal} {self.vol} '
                f'{"," if self.vol and self.pages_start else ""} '
                f'{self.pages_start} "{self.title}"')
        return text

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
    institution = models.CharField(max_length=600, blank=True)
    reference = models.ManyToManyField(Reference)

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
    group = models.CharField(max_length=100, blank=True)  # aka Alternate names
    organic = models.CharField(max_length=100)
    inorganic = models.CharField(max_length=100)
    last_update = models.DateField(auto_now=True)
    description = models.TextField(max_length=1000, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.compound_name

    def listAlternateNames(self):
        return self.group.replace(',', ' ').split()

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
                for author in data.reference.author_set.all():
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


class IDInfo(models.Model):
    reference = models.ForeignKey(Reference, on_delete=models.PROTECT)
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
        return self.reference.getAuthors()


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


class Dataset(Base):
    SINGLE_CRYSTAL = 0
    POWDER = 1
    FILM = 2
    UNKNOWN = 3
    SAMPLE_TYPES = (
        (SINGLE_CRYSTAL, 'single crystal'),
        (POWDER, 'powder'),
        (FILM, 'film'),
        (UNKNOWN, 'unknown'),
    )
    TRICLINIC = 0
    MONOCLINIC = 1
    ORTHORHOMBIC = 2
    TETRAGONAL = 3
    TRIGONAL = 4
    HEXAGONAL = 5
    CUBIC = 6
    UNKNOWN_SYSTEM = 7
    CRYSTAL_SYSTEMS = (
        (TRICLINIC, 'triclinic'),
        (MONOCLINIC, 'monoclinic'),
        (ORTHORHOMBIC, 'orthorhombic'),
        (TETRAGONAL, 'tetragonal'),
        (TRIGONAL, 'trigonal'),
        (HEXAGONAL, 'hexagonal'),
        (CUBIC, 'cubic'),
        (UNKNOWN_SYSTEM, 'unknown'),
    )
    DIMENSIONALITIES = (
        (3, 3),
        (2, 2),
    )
    label = models.TextField(blank=True, max_length=1000)
    system = models.ForeignKey(System, on_delete=models.PROTECT)
    primary_property = models.ForeignKey(
        Property, on_delete=models.PROTECT, related_name='primary_property')
    primary_unit = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT,
        related_name='primary_unit')
    secondary_property = models.ForeignKey(
        Property, null=True, blank=True, on_delete=models.PROTECT,
        related_name='secondary_property')
    secondary_unit = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT,
        related_name='secondary_unit')
    reference = models.ForeignKey(
        Reference, null=True, on_delete=models.PROTECT)
    visible = models.BooleanField()
    is_figure = models.BooleanField()
    is_experimental = models.BooleanField()  # theoretical if false
    dimensionality = models.PositiveSmallIntegerField(choices=DIMENSIONALITIES)
    sample_type = models.PositiveSmallIntegerField(choices=SAMPLE_TYPES)
    crystal_system = models.PositiveSmallIntegerField(choices=CRYSTAL_SYSTEMS)
    extraction_method = models.CharField(max_length=300, blank=True)
    representative = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.representative:
            # Unset the representative flag of the dataset that was
            # previously representative
            Dataset.objects.filter(system=self.system).filter(
                primary_property=self.primary_property).update(
                    representative=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Additionally remove any files uploaded by the user."""
        if self.files.exists():
            shutil.rmtree(
                os.path.dirname(self.files.first().dataset_file.path))
        super().delete(*args, **kwargs)

    def num_all_entries(self):
        return Dataset.objects.filter(system=self.system).filter(
            primary_property=self.primary_property).count()

    def __str__(self):
        return f'ID: {self.pk} ({self.primary_property})'

    def get_all_fixed_properties(self):
        """Return a formatted list of all fixed properties."""
        values = NumericalValueFixed.objects.filter(dataseries__dataset=self)
        text = ''
        if not values:
            return ''
        for i_value, value in enumerate(values):
            text += (f'{value.physical_property} = {value.formatted()} '
                     f'{value.unit}{", " if i_value < len(values)-1 else ""}')
        return '(' + text + ')'


class Dataseries(Base):
    label = models.CharField(max_length=100, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'dataseries'

    def get_fixed_values(self):
        """Return all fixed properties for the given series."""
        values = self.fixed_values.all()
        output = []
        for value in values:
            value_str = value.formatted()
            output.append([
                value.physical_property.name, value_str, value.unit.label])
        return output

    def get_lattice_constants(self):
        """Return three lattice constants and angles."""
        symbols = Symbol.objects.filter(datapoint__dataseries=self).annotate(
            num=models.Count('datapoint__symbols')).filter(num=1).order_by(
                'datapoint_id').values_list('value', flat=True)
        values_float = NumericalValue.objects.filter(
            datapoint__dataseries=self).annotate(
                num=models.Count('datapoint__values')).filter(
                    num=1).select_related('error').order_by('datapoint_id')
        if self.dataset.primary_unit:
            units = 3*[f' {self.dataset.primary_unit.label}'] + 3*['°']
        else:
            units = 3*[' '] + 3*['°']
        values = []
        for value in values_float:
            values.append(value.formatted('.10g'))
        return zip(symbols, values, units)

    def __str__(self):
        return f'ID: {self.pk} ({self.datapoints.count()} data points)'


class Datapoint(Base):
    dataseries = models.ForeignKey(Dataseries, on_delete=models.CASCADE,
                                   related_name='datapoints')


class NumericalValueBase(Base):
    ACCURATE = 0
    APPROXIMATE = 1
    LOWER_BOUND = 2
    UPPER_BOUND = 3
    VALUE_TYPES = (
        (ACCURATE, ''),
        (APPROXIMATE, '≈'),
        (LOWER_BOUND, '>'),
        (UPPER_BOUND, '<'),
    )
    value = models.FloatField()
    value_type = models.PositiveSmallIntegerField(
        default=ACCURATE, choices=VALUE_TYPES)
    counter = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True


class NumericalValue(NumericalValueBase):
    PRIMARY = 0
    SECONDARY = 1
    QUALIFIER_TYPES = (
        (PRIMARY, 'primary'),
        (SECONDARY, 'secondary'),
    )
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE,
                                  related_name='values')
    qualifier = models.PositiveSmallIntegerField(
        default=PRIMARY, choices=QUALIFIER_TYPES)

    def formatted(self, F=''):
        """Return the value as a polished string.

        In particular, the value type and an error, if present, are
        attached to the value, e.g., ">12.3 (±0.4)".

        """
        value_str = f'{self.VALUE_TYPES[self.value_type][1]}{self.value:{F}}'
        if hasattr(self, 'error'):
            value_str += f' (±{self.error.value:{F}})'
        return value_str


class Symbol(Base):
    """Data point information not storable as floats.

    This includes, for example, k-point coordinates such as "X" or the
    component of a tensor such as "c111".

    """
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE,
                                  related_name='symbols')
    value = models.CharField(max_length=10)
    counter = models.PositiveSmallIntegerField(default=0)


class NumericalValueFixed(NumericalValueBase):
    physical_property = models.ForeignKey(Property, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    dataset = models.ForeignKey(Dataset, null=True, on_delete=models.CASCADE,
                                related_name='fixed_values')
    dataseries = models.ForeignKey(Dataseries,
                                   null=True,
                                   on_delete=models.CASCADE,
                                   related_name='fixed_values')
    error = models.FloatField(null=True)

    def formatted(self):
        """Same as for NumericalValue but error is now a class member."""
        value_str = f'{self.VALUE_TYPES[self.value_type][1]}{self.value}'
        if self.error:
            value_str += f' (±{self.error})'
        return value_str


class ComputationalDetails(Base):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name='computational')
    code = models.TextField(blank=True)
    level_of_theory = models.TextField(blank=True)
    xc_functional = models.TextField(blank=True)
    kgrid = models.TextField(blank=True)
    relativity_level = models.TextField(blank=True)
    basis = models.TextField(blank=True)
    numerical_accuracy = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'computational details'


class ExperimentalDetails(Base):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name='experimental')
    method = models.TextField()
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'experimental details'


class SynthesisMethod(Base):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name='synthesis')
    starting_materials = models.TextField(blank=True)
    product = models.TextField(blank=True)
    description = models.TextField(blank=True)


class Comment(Base):
    synthesis_method = models.OneToOneField(
        SynthesisMethod, null=True, on_delete=models.CASCADE)
    computational_details = models.OneToOneField(
        ComputationalDetails, null=True, on_delete=models.CASCADE)
    experimental_details = models.OneToOneField(
        ExperimentalDetails, null=True, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text


class Error(Base):
    """Store the error (or uncertainty) of each value separately."""
    numerical_value = models.OneToOneField(
        NumericalValue, on_delete=models.CASCADE, primary_key=True)
    value = models.FloatField()


def dataset_file_path(instance, filename):
    return os.path.join('uploads', f'dataset_{instance.dataset.pk}', filename)


class DatasetFile(Base):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                related_name='files')
    dataset_file = models.FileField(upload_to=dataset_file_path)
