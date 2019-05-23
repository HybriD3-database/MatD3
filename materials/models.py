import logging
import os
import shutil

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Base(models.Model):
    """Basic meta information that all models must have."""
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

    class Meta:
        verbose_name_plural = 'properties'

    def __str__(self):
        return self.name


class Unit(Base):
    label = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.label


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
    """Primary information about the physical system."""
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


class Dataset(Base):
    """Class for mainly tables and figures.

    It doesn't have to be limited to tables and figures though. A data
    set is a self-contained collection of any data.

    """
    SINGLE_CRYSTAL = 0
    POWDER = 1
    FILM = 2
    BULK_POLYCRYSTALLINE = 3
    PELLET = 4
    NANOFORM = 5
    UNKNOWN = 6
    SAMPLE_TYPES = (
        (SINGLE_CRYSTAL, 'single crystal'),
        (POWDER, 'powder'),
        (FILM, 'film'),
        (BULK_POLYCRYSTALLINE, 'bulk polycrystalline'),
        (PELLET, 'pellet'),
        (NANOFORM, 'nanoform'),
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
    primary_property_label = models.TextField(blank=True, max_length=50)
    secondary_property = models.ForeignKey(
        Property, null=True, blank=True, on_delete=models.PROTECT,
        related_name='secondary_property')
    secondary_unit = models.ForeignKey(
        Unit, null=True, blank=True, on_delete=models.PROTECT,
        related_name='secondary_unit')
    secondary_property_label = models.TextField(blank=True, max_length=50)
    reference = models.ForeignKey(
        Reference, null=True, blank=True, on_delete=models.PROTECT)
    visible = models.BooleanField()
    is_figure = models.BooleanField()
    is_experimental = models.BooleanField()  # theoretical if false
    dimensionality = models.PositiveSmallIntegerField(choices=DIMENSIONALITIES)
    sample_type = models.PositiveSmallIntegerField(choices=SAMPLE_TYPES)
    crystal_system = models.PositiveSmallIntegerField(choices=CRYSTAL_SYSTEMS)
    extraction_method = models.CharField(max_length=300, blank=True)
    representative = models.BooleanField(default=False)
    linked_to = models.ManyToManyField('self', blank=True)

    class Meta:
        verbose_name_plural = 'data sets'

    def __str__(self):
        return f'ID: {self.pk} ({self.primary_property})'

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
        if self.representative:
            Dataset.objects.filter(system=self.system).filter(
                primary_property=self.primary_property).exclude(
                    pk=self.pk).update(representative=True)
        super().delete(*args, **kwargs)

    def num_all_entries(self):
        return Dataset.objects.filter(system=self.system).filter(
            primary_property=self.primary_property).count()

    def get_all_fixed_temperatures(self):
        """Return a formatted list of all fixed temperatures."""
        values = []
        for value in NumericalValueFixed.objects.filter(
                subset__dataset=self).filter(
                    physical_property__name='temperature'):
            values.append(f'{value.formatted()} {value.unit}')
        return ('(T = ' + ', '.join(values) + ')' if values else '')


class Subset(Base):
    """Subset of data.

    A data set always has at least one subset. It may have more if it
    makes sense to split up data into several subsets (e.g., several
    curves in a figure).

    """
    label = models.CharField(max_length=100, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                related_name='subsets')

    class Meta:
        verbose_name_plural = 'data subsets'

    def __str__(self):
        return f'ID: {self.pk} ({self.datapoints.count()} data points)'

    def get_fixed_values(self):
        """Return all fixed properties for the given subset."""
        values = self.fixed_values.all()
        output = []
        for value in values:
            value_str = value.formatted()
            output.append([
                value.physical_property.name, value_str, value.unit.label])
        return output

    def get_lattice_constants(self):
        """Return three lattice constants and angles."""
        symbols = Symbol.objects.filter(datapoint__subset=self).annotate(
            num=models.Count('datapoint__symbols')).filter(num=1).order_by(
                'datapoint_id').values_list('value', flat=True)
        values_float = NumericalValue.objects.filter(
            datapoint__subset=self).annotate(
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


class Datapoint(Base):
    """Container for the data point.

    The actual data are contained in other tables such as
    NumericalValue.

    """
    subset = models.ForeignKey(
        Subset, on_delete=models.CASCADE, related_name='datapoints')


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
    """Numerical value(s) associated with a data point."""
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
        """Return the value as a formatted string.

        In particular, the value type and an error, if present, are
        attached to the value, e.g., ">12.3 (±0.4)".

        """
        value_str = f'{self.VALUE_TYPES[self.value_type][1]}{self.value:{F}}'
        if hasattr(self, 'error'):
            value_str += f' (±{self.error.value:{F}})'
        return value_str


class NumericalValueFixed(NumericalValueBase):
    """Values that are constant within a data subset."""
    physical_property = models.ForeignKey(Property, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    subset = models.ForeignKey(Subset,
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


class Symbol(Base):
    """Data point information not storable as floats.

    This includes, for example, k-point coordinates such as "X" or the
    component of a tensor such as "c111".

    """
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE,
                                  related_name='symbols')
    value = models.CharField(max_length=10)
    counter = models.PositiveSmallIntegerField(default=0)


class ComputationalDetails(Base):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name='computational')
    code = models.TextField(blank=True)
    level_of_theory = models.TextField(blank=True)
    xc_functional = models.TextField(blank=True)
    k_point_grid = models.TextField(blank=True)
    level_of_relativity = models.TextField(blank=True)
    basis_set_definition = models.TextField(blank=True)
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
