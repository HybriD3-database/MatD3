# This file is covered by the BSD license. See LICENSE in the root directory.
from functools import reduce
import io
import json
import logging
import operator
import os
import re
import requests
import zipfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import BooleanField
from django.db.models import Case
from django.db.models import Q
from django.db.models import Value
from django.db.models import When
from django.db.models.fields import TextField
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views import generic
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import forms
from . import models
from . import permissions
from . import qresp
from . import serializers
from . import utils

logger = logging.getLogger(__name__)


def dataset_author_check(view):
    """Test whether the logged on user is the creator of the data set."""
    @login_required
    def wrap(request, *args, **kwargs):
        dataset = get_object_or_404(models.Dataset, pk=kwargs['pk'])
        if dataset.created_by == request.user:
            return view(request, *args, **kwargs)
        else:
            logger.warning(f'Data set was created by {dataset.created_by} but '
                           'an attempt was made to delete it by '
                           f'{request.user}',
                           extra={'request': request})
            return HttpResponseForbidden()
    wrap.__doc__ = view.__doc__
    wrap.__name__ = view.__name__
    return wrap


def staff_status_required(view):
    @login_required
    def wrap(request, *args, **kwargs):
        if request.user.is_staff:
            return view(request, *args, **kwargs)
        else:
            logger.warning(f'{request.user.username} is trying to submit data '
                           'but does not have staff status.',
                           extra={'request': request})
            return HttpResponseForbidden()
    wrap.__doc__ = view.__doc__
    wrap.__name__ = view.__name__
    return wrap


class StaffStatusMixin(LoginRequiredMixin):
    """Verify that the current user is at least staff."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class SystemView(generic.ListView):
    template_name = 'materials/system.html'
    context_object_name = 'dataset_list'

    def get_queryset(self, **kwargs):
        return models.Dataset.objects.filter(
            system__pk=self.kwargs['pk']).annotate(is_atomic_structure=Case(
                When(primary_property__name='atomic structure',
                     then=Value(True)),
                default=Value(False), output_field=BooleanField())).order_by(
                    '-is_atomic_structure')


class PropertyAllEntriesView(generic.ListView):
    """Display all data sets for a given property and system."""
    template_name = 'materials/property_all_entries.html'

    def get_queryset(self, **kwargs):
        return models.Dataset.objects.filter(
            system__pk=self.kwargs['system_pk']).filter(
                primary_property__pk=self.kwargs['prop_pk'])


class ReferenceDetailView(generic.DetailView):
    model = models.Reference


class DatasetView(generic.ListView):
    """Display information about a single data set.

    This is defined as a ListView so that we can reuse the same
    template as for PropertyAllEntriesView. Otherwise, this is really
    a DetailView.

    """
    template_name = 'materials/property_all_entries.html'

    def get_queryset(self, **kwargs):
        return models.Dataset.objects.filter(pk=self.kwargs['pk'])


class LinkedDataView(generic.ListView):
    """Returns data sets that are linked to each other."""
    template_name = 'materials/linked_data.html'

    def get_queryset(self, **kwargs):
        dataset = models.Dataset.objects.get(pk=self.kwargs['pk'])
        datasets = dataset.linked_to.all()
        return list(datasets) + [dataset]


class SearchFormView(generic.TemplateView):
    """Search for system page"""
    template_name = 'materials/search.html'
    search_terms = [
        ['formula', 'Formula'],
        ['physical_property', 'Physical property'],
        ['organic', 'Organic Component'],
        ['inorganic', 'Inorganic Component'],
        ['author', 'Author'],
    ]

    def get(self, request):
        material_ids = models.System.objects.all().values_list(
            'pk', 'compound_name')
        dataset_ids = models.Dataset.objects.all().values_list(
            'pk', 'system__compound_name', 'primary_property__name')
        return render(request, self.template_name, {
            'search_terms': self.search_terms,
            'material_ids': material_ids,
            'dataset_ids': dataset_ids,
        })

    def post(self, request):
        template_name = 'materials/search_results.html'
        form = forms.SearchForm(request.POST)
        search_text = ''
        # default search_term
        search_term = 'formula'
        physical_properties = []
        if form.is_valid():
            search_text = form.cleaned_data['search_text']
            search_term = request.POST.get('search_term')
            systems_info = []
            if search_term == 'formula':
                systems = models.System.objects.filter(
                    Q(formula__icontains=search_text) |
                    Q(group__icontains=search_text) |
                    Q(compound_name__icontains=search_text)).order_by(
                        'formula')
            elif search_term == 'physical_property':
                physical_properties = models.Property.objects.filter(
                    name__icontains=search_text).values_list('name', flat=True)
                systems = models.System.objects.filter(
                    dataset__primary_property__name__icontains=search_text)
            elif search_term == 'organic':
                systems = models.System.objects.filter(
                    organic__contains=search_text).order_by('organic')
            elif search_term == 'inorganic':
                systems = models.System.objects.filter(
                    inorganic__contains=search_text).order_by('inorganic')
            elif search_term == 'author':
                keywords = search_text.split()
                query = reduce(operator.or_, (
                    Q(dataset__reference__authors__last_name__icontains=x) for
                    x in keywords))
                systems = models.System.objects.filter(query).distinct()
            else:
                raise KeyError('Invalid search term.')
        args = {
            'systems': systems,
            'search_term': search_term,
            'systems_info': systems_info,
            'physical_properties': physical_properties,
        }
        return render(request, template_name, args)


class AddDataView(StaffStatusMixin, generic.TemplateView):
    """View for submitting user data.

    The arguments are only meant to be used when this view is called
    from external sites. Fields such as the reference can be prefilled
    then.

    """
    template_name = 'materials/add_data.html'

    def get(self, request, *args, **kwargs):
        main_form = forms.AddDataForm()
        if request.GET.get('return-url'):
            return_url = request.META['HTTP_REFERER'].replace('/qrespcurator',
                                                              '')
            return_url = return_url + request.GET.get('return-url')
            base_template = 'mainproject/base.html'
            main_form.fields['return_url'].initial = return_url
        else:
            base_template = 'materials/base.html'
        if request.GET.get('reference'):
            main_form.fields['fixed_reference'].initial = (
                models.Reference.objects.get(pk=request.GET.get('reference')))
        if request.GET.get('qresp-server-url'):
            qresp_paper_id = request.GET.get('qresp-paper-id')
            qresp_fetch_url = request.GET.get("qresp-server-url")
            qresp_fetch_url += f'/api/paper/{qresp_paper_id}'
            qresp_chart_nr = int(request.GET.get('qresp-chart-nr'))
            paper_detail = requests.get(qresp_fetch_url, verify=False).json()
            main_form.fields['qresp_fetch_url'].initial = qresp_fetch_url
            main_form.fields['qresp_chart_nr'].initial = qresp_chart_nr
            main_form.fields['caption'].initial = (
                paper_detail['charts'][qresp_chart_nr]['caption'])
        if request.GET.get('qresp-search-url'):
            qresp_search_url = request.GET.get('qresp-search-url')
            main_form.fields['qresp_search_url'].initial = qresp_search_url
        return render(request, self.template_name, {
            'main_form': main_form,
            'reference_form': forms.AddReferenceForm(),
            'system_form': forms.AddSystemForm(),
            'property_form': forms.AddPropertyForm(),
            'unit_form': forms.AddUnitForm(),
            'base_template': base_template,
        })


class ImportDataView(StaffStatusMixin, generic.TemplateView):
    template_name = 'materials/import_data.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'base_template': 'materials/base.html',
        })


class ReferenceViewSet(viewsets.ModelViewSet):
    queryset = models.Reference.objects.all()
    serializer_class = serializers.ReferenceSerializer
    permission_classes = (permissions.IsStaffOrReadOnly,)

    @transaction.atomic
    def perform_create(self, serializer):
        """Save reference and optionally create authors.

        The combination first name/last name/institution must be
        unique. If not, the given author is not in the database
        yet. Note that this constraint can't be enforced at the
        database level because of the limitations of the length of the
        key.

        """
        reference = serializer.save()
        for name in self.request.POST:
            if name.startswith('first-name-'):
                counter = name.split('first-name-')[1]
                first_name = self.request.POST[name]
                last_name = self.request.POST[f'last-name-{counter}']
                institution = self.request.POST[f'institution-{counter}']
                authors = models.Author.objects.filter(
                    first_name=first_name).filter(last_name=last_name).filter(
                        institution=institution)
                if authors:
                    author = authors[0]
                else:
                    author = models.Author.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        institution=institution)
                author.references.add(reference)


class SystemViewSet(viewsets.ModelViewSet):
    queryset = models.System.objects.all()
    serializer_class = serializers.SystemSerializer
    permission_classes = (permissions.IsStaffOrReadOnly,)


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = models.Property.objects.all()
    serializer_class = serializers.PropertySerializer
    permission_classes = (permissions.IsStaffOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class UnitViewSet(viewsets.ModelViewSet):
    queryset = models.Unit.objects.all()
    serializer_class = serializers.UnitSerializer
    permission_classes = (permissions.IsStaffOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


def dataset_to_zip(request, dataset):
    """Generate a zip file from data set contents."""
    in_memory_object = io.BytesIO()
    zf = zipfile.ZipFile(in_memory_object, 'w')
    # Header file to the data
    zf.writestr('files/info.txt',
                utils.dataset_info(dataset, request.get_host()))
    # Main data
    for file_ in (f.dataset_file.path for f in dataset.input_files.all()):
        zf.write(file_,
                 os.path.join('files', os.path.basename(file_)))
    # Additional files
    for file_ in (f.dataset_file.path for f in dataset.files.all()):
        zf.write(file_,
                 os.path.join('files/additional', os.path.basename(file_)))
    zf.close()
    return in_memory_object


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer

    @action(detail=True)
    def info(self, request, pk):
        dataset = self.get_object()
        serializer = serializers.DatasetSerializerInfo(dataset)
        return Response(serializer.data)

    @action(detail=False)
    def summary(self, request):
        serializer = serializers.DatasetSerializerSummary(self.queryset,
                                                          many=True)
        return Response(serializer.data)

    @action(detail=True)
    def files(self, request, pk):
        """Retrieve data set contents and uploaded files as zip."""
        dataset = self.get_object()
        in_memory_object = dataset_to_zip(request, dataset)
        response = HttpResponse(in_memory_object.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename=files.zip'
        return response


@staff_status_required
@transaction.atomic
def submit_data(request):
    """Primary function for submitting data from the user."""
    def clean_value(value):
        """Return value as float and determine its type.

        The value is first stripped of markers such as '<', which are
        used to determine its type. If the value contains an error (or
        uncertainty), the error is also returned.

        """
        error = None
        upper_bound = None
        if re.match(r'[-\d]', value):
            value_type = models.NumericalValue.ACCURATE
        elif value.startswith('<'):
            value_type = models.NumericalValue.UPPER_BOUND
            value = value[1:]
        elif value.startswith('>'):
            value_type = models.NumericalValue.LOWER_BOUND
            value = value[1:]
        elif value.startswith(('≈', '~')):
            value_type = models.NumericalValue.APPROXIMATE
            value = value[1:]
        if '(' in value:
            if '(0' in value:
                value = re.sub(r'\(0+', '(', value)
            left_paren_start = value.find('(')
            right_paren_start = value.find(')')
            error = value[left_paren_start+1:right_paren_start]
            if '.' not in error and left_paren_start > len(error):
                error = re.sub('[1-9]', '0',
                               value[:left_paren_start-len(error)]) + error
            value = value[:left_paren_start]
        elif '±' in value:
            value, error = value.split('±')
        elif '...' in value:
            value, upper_bound = value.split('...')
        return float(value), value_type, error, upper_bound

    def add_numerical_value(numerical_values, errors, upper_bounds, value,
                            is_secondary=False, counter=0):
        """Clean and add a numerical value to a list.

        numerical_values: list
            list that contains numerical values that will be created
            by a bulk_create once the list is complete
        error: list
            same as numerical_values but for errors
        value: string
            numerical value to be processed and added to the list
        is_secondary: boolean
            whether the numerical value is of secondary or primary
            type
        counter: int
            numerical value counter

        """
        numerical_value = models.NumericalValue(created_by=request.user)
        if is_secondary:
            numerical_value.qualifier = models.NumericalValue.SECONDARY
        if counter > 0:
            numerical_value.counter = counter
        value, value_type, error, upper_bound = clean_value(value)
        numerical_value.value = value
        numerical_value.value_type = value_type
        numerical_values.append(numerical_value)
        errors.append(error)
        upper_bounds.append(upper_bound)

    def add_datapoint_ids(values, n_values, n_datapoints):
        """Set datapoint_id for all elements in an array.

        The data points must already have been created using
        bulk_create. Now, fetch the ids of the latest data points and
        manually attach them to each element in "values". After this
        is done, bulk_create may be called on "values".

        The number of values and datapoints are necessary to determine
        how many values are associated with each data point.

        """
        if n_values == 0:
            return
        step = int(n_values/n_datapoints)
        n_datapoints = int(len(values)/step)
        pks = list(models.Datapoint.objects.all().order_by(
            '-pk')[:n_datapoints].values_list('pk', flat=True))
        for i_pk, pk in enumerate(reversed(pks)):
            for i_step in range(step):
                values[step*i_pk+i_step].datapoint_id = pk

    def generate_numerical_value_ids(array, model):
        """Set numerical_value_id for all elements in array.

        This is similar to add_datapoint_ids, except the structure of
        the array is different. Some or all elements in the array may
        be None. Filter out non-None elements and return an array that
        may be given as argument to bulk_create.

        """
        pks = list(models.NumericalValue.objects.all().order_by(
            '-pk')[:len(array)].values_list('pk', flat=True))
        filtered_list = []
        for i, pk in enumerate(reversed(pks)):
            if array[i]:
                filtered_list.append(model(created_by=request.user,
                                           numerical_value_id=pk,
                                           value=array[i]))
        return filtered_list

    def error_and_return(form, dataset=None, text=None):
        """Shortcut for returning with info about the error."""
        if form.cleaned_data['return_url']:
            base_template = 'mainproject/base.html'
        else:
            base_template = 'materials/base.html'
        if dataset:
            dataset.delete()
        if text:
            messages.error(request, text)
        return render(request, AddDataView.template_name, {
            'main_form': form,
            'reference_form': forms.AddReferenceForm(),
            'system_form': forms.AddSystemForm(),
            'property_form': forms.AddPropertyForm(),
            'unit_form': forms.AddUnitForm(),
            'base_template': base_template
        })

    def skip_this_line(line):
        """Test whether the line is empty or a comment."""
        return re.match(r'\s*#', line) or not line or line == '\r'

    def create_input_file(dataset, import_file_name, data_as_str, i_subset,
                          multiple_subsets):
        """Read data points from the input form and save as file.

        If the name of the original file from which the data was
        imported is on the form, use that name for creating the
        file. If not and if multiple_subsets, then the files are named
        data1.txt, data2.txt, etc. Otherwise, a single file called
        data.txt is created and i_subset is ignored.

        """
        if data_as_str:
            if import_file_name:
                file_name = import_file_name
            elif multiple_subsets:
                file_name = f'data{i_subset}.txt'
            else:
                file_name = 'data.txt'
            f = SimpleUploadedFile(file_name, data_as_str.encode())
            dataset.input_files.create(created_by=dataset.created_by,
                                       dataset_file=f)

    form = forms.AddDataForm(request.POST)
    if not form.is_valid():
        # Show formatted field labels in the error message, not the
        # dictionary keys
        errors_save = form._errors.copy()
        for field in form:
            if field.name in form._errors:
                form._errors[field.label] = form._errors.pop(field.name)
        messages.error(request, form.errors)
        form._errors = errors_save
        return error_and_return(form)
    # Create data set
    dataset = models.Dataset(created_by=request.user)
    dataset.system = form.cleaned_data['select_system']
    dataset.reference = form.cleaned_data['select_reference']
    dataset.caption = form.cleaned_data['caption']
    dataset.primary_property = form.cleaned_data['primary_property']
    dataset.primary_unit = form.cleaned_data['primary_unit']
    dataset.primary_property_label = form.cleaned_data[
        'primary_property_label']
    if form.cleaned_data['two_axes']:
        dataset.secondary_property = form.cleaned_data['secondary_property']
        dataset.secondary_unit = form.cleaned_data['secondary_unit']
        dataset.secondary_property_label = form.cleaned_data[
            'secondary_property_label']
    dataset.visible = form.cleaned_data['visible_to_public']
    dataset.is_figure = form.cleaned_data['is_figure']
    dataset.is_experimental = (
        form.cleaned_data['origin_of_data'] == 'is_experimental')
    dataset.dimensionality = form.cleaned_data[
        'dimensionality_of_the_inorganic_component']
    dataset.sample_type = form.cleaned_data['sample_type']
    dataset.space_group = form.cleaned_data['space_group']
    dataset.extraction_method = form.cleaned_data['extraction_method']
    # Make representative by default if first entry of its kind
    dataset.representative = not bool(models.Dataset.objects.filter(
        system=dataset.system).filter(
            primary_property=dataset.primary_property))
    dataset.save()
    logger.info(f'Create dataset #{dataset.pk}')
    # Uploaded files
    for f in request.FILES.getlist('uploaded_files'):
        dataset.files.create(created_by=request.user, dataset_file=f)
    # Synthesis method
    if form.cleaned_data['with_synthesis_details']:
        synthesis = models.SynthesisMethod(created_by=request.user,
                                           dataset=dataset)
        synthesis.starting_materials = form.cleaned_data['starting_materials']
        synthesis.product = form.cleaned_data['product']
        synthesis.description = form.cleaned_data['synthesis_description']
        synthesis.save()
        logger.info(f'Creating synthesis details #{synthesis.pk}')
        if form.cleaned_data['synthesis_comment']:
            models.Comment.objects.create(
                synthesis_method=synthesis,
                created_by=request.user,
                text=form.cleaned_data['synthesis_comment'])
    # Experimental details
    if form.cleaned_data['with_experimental_details']:
        experimental = models.ExperimentalDetails(created_by=request.user,
                                                  dataset=dataset)
        experimental.method = form.cleaned_data['experimental_method']
        experimental.description = form.cleaned_data[
            'experimental_description']
        experimental.save()
        logger.info(f'Creating experimental details #{experimental.pk}')
        if form.cleaned_data['experimental_comment']:
            models.Comment.objects.create(
                experimental_details=experimental,
                created_by=request.user,
                text=form.cleaned_data['experimental_comment'])
    # Computational details
    if form.cleaned_data['with_computational_details']:
        computational = models.ComputationalDetails(created_by=request.user,
                                                    dataset=dataset)
        computational.code = form.cleaned_data['code']
        computational.level_of_theory = form.cleaned_data['level_of_theory']
        computational.xc_functional = form.cleaned_data['xc_functional']
        computational.k_point_grid = form.cleaned_data['k_point_grid']
        computational.level_of_relativity = form.cleaned_data[
            'level_of_relativity']
        computational.basis_set_definition = form.cleaned_data[
            'basis_set_definition']
        computational.numerical_accuracy = form.cleaned_data[
            'numerical_accuracy']
        computational.save()
        logger.info(f'Creating computational details #{computational.pk}')
        if form.cleaned_data['computational_comment']:
            models.Comment.objects.create(
                computational_details=computational,
                created_by=request.user,
                text=form.cleaned_data['computational_comment'])
        if form.cleaned_data['external_repositories']:
            for url in form.cleaned_data['external_repositories'].split():
                if not requests.head(url).ok:
                    return error_and_return(form, dataset,
                                            'Could not process url for the '
                                            f'external repository: "{url}"')
                models.ExternalRepository.objects.create(
                    computational_details=computational,
                    created_by=request.user,
                    url=url)
    # For best performance, the main data should be inserted with
    # calls to bulk_create. The following work arrays are are
    # populated with data during the loop over subsets and then
    # inserted into the database after the main loop.
    datapoints = []
    symbols = []
    numerical_values = []
    errors = []
    upper_bounds = []
    multiple_subsets = int(form.cleaned_data['number_of_subsets']) > 1
    for i_subset in range(1, int(form.cleaned_data['number_of_subsets']) + 1):
        # Create data subset
        subset = models.Subset(created_by=request.user, dataset=dataset)
        subset.crystal_system = form.cleaned_data[f'crystal_system_{i_subset}']
        if f'subset_label_{i_subset}' in form.cleaned_data:
            subset.label = form.cleaned_data[f'subset_label_{i_subset}']
        subset.save()
        # Go through exceptional cases first. Some properties such as
        # "atomic structure" require special treatment.
        if dataset.primary_property.name == 'atomic structure':
            create_input_file(
                dataset,
                form.cleaned_data[f'import_file_name_{i_subset}'],
                form.cleaned_data[f'atomic_coordinates_{i_subset}'],
                i_subset,
                multiple_subsets)
            for symbol, key in (('a', 'a'), ('b', 'b'), ('c', 'c'),
                                ('α', 'alpha'), ('β', 'beta'), ('γ', 'gamma')):
                datapoint = models.Datapoint.objects.create(
                    created_by=request.user, subset=subset)
                datapoint.symbols.create(created_by=request.user, value=symbol)
                name = f'lattice_constant_{key}_{i_subset}'
                value, value_type, error, upper_bound = clean_value(
                    form.cleaned_data[name])
                models.NumericalValue.objects.create(created_by=request.user,
                                                     datapoint=datapoint,
                                                     value_type=value_type,
                                                     value=value)
                if error:
                    models.Error.objects.create(
                        created_by=request.user,
                        numerical_value=models.NumericalValue.objects.last(),
                        value=float(error))
                if upper_bound:
                    models.UpperBound.objects.create(
                        created_by=request.user,
                        numerical_value=models.NumericalValue.objects.last(),
                        value=float(upper_bound))
            lattice_vectors = []
            lattice_errors = []  # dummy
            lattice_upper_bounds = []  # dummy
            for line in form.cleaned_data[
                    f'atomic_coordinates_{i_subset}'].split('\n'):
                if form.cleaned_data[f'geometry_format_{i_subset}'] != 'aims':
                    break
                try:
                    m = re.match(r'\s*lattice_vector' +
                                 3*r'\s+(-?\d+(?:\.\d+)?)' + r'\b', line)
                    if m:
                        coords = m.groups()
                        models.Datapoint.objects.create(
                            created_by=request.user, subset=subset)
                        for i_coord, coord in enumerate(coords):
                            add_numerical_value(lattice_vectors,
                                                lattice_errors,
                                                lattice_upper_bounds,
                                                coord,
                                                counter=i_coord)
                    else:
                        m = re.match(
                            r'\s*(atom|atom_frac)\s+' +
                            3*r'(-?\d+(?:\.\d+)?(?:\(\d+\))?)\s+' +
                            r'(\w+)\b', line)
                        coord_type, *coords, element = m.groups()
                        datapoints.append(models.Datapoint(
                            created_by=request.user, subset=subset))
                        symbols.append(models.Symbol(created_by=request.user,
                                                     value=coord_type))
                        symbols.append(models.Symbol(created_by=request.user,
                                                     value=element, counter=1))
                        for i_coord, coord in enumerate(coords):
                            add_numerical_value(numerical_values,
                                                errors,
                                                upper_bounds,
                                                coord,
                                                counter=i_coord)
                except AttributeError:
                    # Skip comments and empty lines
                    if not re.match(r'(?:\r?$|#|//)', line):
                        return error_and_return(
                            form, dataset, f'Could not process line: {line}')
            add_datapoint_ids(lattice_vectors, 9, 3)
            models.NumericalValue.objects.bulk_create(lattice_vectors)
        elif dataset.primary_property.name == 'band structure':
            # Get kpoints
            k_labels = []
            for line in form.cleaned_data[
                    f'subset_datapoints_{i_subset}'].splitlines():
                if skip_this_line(line):
                    continue
                k_labels.append(line.split())
            # Get files
            files = []
            for f in dataset.files.all():
                if re.match(r'band10\d+\.out',
                            os.path.basename(f.dataset_file.name)):
                    files.append(f.dataset_file)
                if os.path.basename(f.dataset_file.name) in [
                        'band_structure_full.png', 'band_structure_small.png']:
                    return error_and_return(
                        form, dataset,
                        f'Rename {os.path.basename(f.dataset_file.name)} '
                        '(this name is reserved)')
            # The band files need to be alphabeticaly sorted
            for i in range(len(files)):
                for j in range(i+1, len(files)):
                    if files[i].name > files[j].name:
                        files[i], files[j] = files[j], files[i]
            utils.plot_band_structure(k_labels, files, dataset)
        elif dataset.primary_property.name.startswith('phase transition '):
            value, value_type, error, upper_bound = clean_value(
                form.cleaned_data[f'phase_transition_value_{i_subset}'])
            crystal_f = f'phase_transition_crystal_system_final_{i_subset}'
            space_group_i = f'phase_transition_space_group_initial_{i_subset}'
            space_group_f = f'phase_transition_space_group_final_{i_subset}'
            direction = f'phase_transition_direction_{i_subset}'
            hysteresis = f'phase_transition_hysteresis_{i_subset}'
            subset.phase_transitions.create(
                created_by=request.user,
                crystal_system_final=form.cleaned_data[crystal_f],
                space_group_initial=form.cleaned_data[space_group_i],
                space_group_final=form.cleaned_data[space_group_f],
                direction=form.cleaned_data[direction],
                hysteresis=form.cleaned_data[hysteresis],
                value=value,
                value_type=value_type,
                error=error,
                upper_bound=upper_bound)
        elif form.cleaned_data['two_axes']:
            create_input_file(
                dataset,
                form.cleaned_data[f'import_file_name_{i_subset}'],
                form.cleaned_data[f'subset_datapoints_{i_subset}'],
                i_subset,
                multiple_subsets)
            try:
                for line in form.cleaned_data[
                        f'subset_datapoints_{i_subset}'].splitlines():
                    if skip_this_line(line):
                        continue
                    x_value, y_value = line.split()[:2]
                    datapoints.append(models.Datapoint(
                        created_by=request.user, subset=subset))
                    add_numerical_value(numerical_values,
                                        errors,
                                        upper_bounds,
                                        x_value,
                                        is_secondary=True)
                    add_numerical_value(
                        numerical_values, errors, upper_bounds, y_value)
            except ValueError:
                return error_and_return(
                    form, dataset, f'Could not process line: {line}')
        else:
            create_input_file(
                dataset,
                form.cleaned_data[f'import_file_name_{i_subset}'],
                form.cleaned_data[f'subset_datapoints_{i_subset}'],
                i_subset,
                multiple_subsets)
            try:
                for line in form.cleaned_data[
                        f'subset_datapoints_{i_subset}'].splitlines():
                    if skip_this_line(line):
                        continue
                    for value in line.split():
                        datapoints.append(models.Datapoint(
                            created_by=request.user, subset=subset))
                        add_numerical_value(
                            numerical_values, errors, upper_bounds, value)
            except ValueError:
                return error_and_return(
                    form, dataset, f'Could not process line: {line}')
        # Fixed properties
        counter = 0
        for key in form.cleaned_data:
            if key.startswith(f'fixed_property_{i_subset}_'):
                suffix = key.split('fixed_property_')[1]
                value, value_type, error, upper_bound = clean_value(
                    form.cleaned_data['fixed_value_' + suffix])
                subset.fixed_values.create(
                    created_by=request.user,
                    counter=counter,
                    physical_property=form.cleaned_data[
                        'fixed_property_' + suffix],
                    unit=form.cleaned_data['fixed_unit_' + suffix],
                    value=value,
                    value_type=value_type,
                    error=error,
                    upper_bound=upper_bound)
                counter += 1
    # Insert the main data into the database
    models.Datapoint.objects.bulk_create(datapoints)
    add_datapoint_ids(numerical_values, len(numerical_values), len(datapoints))
    models.NumericalValue.objects.bulk_create(numerical_values)
    models.Error.objects.bulk_create(
        generate_numerical_value_ids(errors, models.Error))
    models.UpperBound.objects.bulk_create(
        generate_numerical_value_ids(upper_bounds, models.UpperBound))
    add_datapoint_ids(symbols, len(symbols), len(datapoints))
    models.Symbol.objects.bulk_create(symbols)
    # Linked data sets
    for pk in form.cleaned_data['related_data_sets'].split():
        try:
            dataset.linked_to.add(models.Dataset.objects.get(pk=pk))
        except models.Dataset.DoesNotExist:
            return error_and_return(
                form, dataset, f'Related data set {pk} does not exist')
    # Create static files for Qresp
    qresp.create_static_files(request, dataset)
    # Import data from Qresp
    if form.cleaned_data['qresp_fetch_url']:
        paper_detail = requests.get(
            form.cleaned_data['qresp_fetch_url'], verify=False).json()
        download_url = paper_detail['fileServerPath']
        chart_detail = paper_detail['charts'][
            form.cleaned_data['qresp_chart_nr']]
        chart = requests.get(f'{download_url}/{chart_detail["imageFile"]}',
                             verify=False)
        file_name = chart_detail["imageFile"].replace('/', '_')
        f = SimpleUploadedFile(file_name, chart.content)
        dataset.files.create(created_by=dataset.created_by, dataset_file=f)
    # If all went well, let the user know how much data was
    # successfully added
    n_data_points = 0
    for subset in dataset.subsets.all():
        n_data_points += subset.datapoints.count()
    if n_data_points > 0:
        message = (f'{n_data_points} new '
                   f'data point{"s" if n_data_points != 1 else ""} '
                   'successfully added to the database.')
    else:
        message = 'New data successfully added to the database.'
    dataset_url = reverse('materials:dataset', kwargs={'pk': dataset.pk})
    message = mark_safe(message +
                        f' <a href="{dataset_url}">View</a> the data set.')
    if form.cleaned_data['qresp_search_url']:
        messages.success(request, message)
        return redirect('/materials/import-data', kwargs={
            'qresp_search_url': form.cleaned_data['qresp_search_url'],
            'qresp_chart_nr': form.cleaned_data['qresp_chart_nr'],
        })
    elif form.cleaned_data['return_url']:
        return redirect(
            f'{form.cleaned_data["return_url"]}?pk={dataset.pk}')
    else:
        messages.success(request, message)
        return redirect(reverse('materials:add_data'))


def resolve_return_url(pk, view_name):
    """Determine URL from the view name and other arguments.

    This is useful for the data set buttons such as delete, which can
    then return to the same address.

    """
    if view_name == 'dataset':
        return redirect(reverse('materials:dataset', kwargs={'pk': pk}))
    elif view_name == 'reference':
        ref_pk = models.Dataset.objects.get(pk=pk).reference.pk
        return redirect(reverse('materials:reference', kwargs={'pk': ref_pk}))
    elif view_name == 'system':
        sys_pk = models.Dataset.objects.get(pk=pk).system.pk
        return redirect(reverse('materials:system', kwargs={'pk': sys_pk}))
    elif view_name == 'property_all_entries':
        sys_pk = models.Dataset.objects.get(pk=pk).system.pk
        prop_pk = models.Dataset.objects.get(pk=pk).primary_property.pk
        return redirect(reverse(
            'materials:property_all_entries',
            kwargs={'system_pk': sys_pk, 'prop_pk': prop_pk}))
    elif view_name == 'linked_data':
        return redirect(reverse('materials:linked_data', kwargs={'pk': pk}))
    else:
        return Http404


@dataset_author_check
def toggle_visibility(request, pk, view_name):
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.visible = not dataset.visible
    dataset.save()
    return resolve_return_url(pk, view_name)


@dataset_author_check
def toggle_is_figure(request, pk, view_name):
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.is_figure = not dataset.is_figure
    dataset.save()
    return resolve_return_url(pk, view_name)


@dataset_author_check
def delete_dataset(request, pk, view_name):
    """Delete current data set and all associated files."""
    return_url = resolve_return_url(pk, view_name)
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.delete()
    return return_url


@staff_status_required
def verify_dataset(request, pk, view_name):
    """Verify the correctness of the data."""
    return_url = resolve_return_url(pk, view_name)
    dataset = models.Dataset.objects.get(pk=pk)
    if request.user in dataset.verified_by.all():
        dataset.verified_by.remove(request.user)
    else:
        dataset.verified_by.add(request.user)
    return return_url


def autofill_input_data(request):
    """Process an AJAX request to autofill the data textareas."""
    content = UploadedFile(request.FILES['file']).read().decode('utf-8')
    lines = content.splitlines()
    for i_line, line in enumerate(lines):
        if re.match(r'\s*#', line) or not line or line == '\r':
            del lines[i_line]
    return HttpResponse('\n'.join(lines))


def data_for_chart(request, pk):
    dataset = models.Dataset.objects.get(pk=pk)
    if dataset.primary_unit:
        primary_unit_label = dataset.primary_unit.label
    else:
        primary_unit_label = ''
    if dataset.secondary_unit:
        secondary_unit_label = dataset.secondary_unit.label
    else:
        secondary_unit_label = ''
    response = {'primary-property': dataset.primary_property.name,
                'primary-unit': primary_unit_label,
                'secondary-property': dataset.secondary_property.name,
                'secondary-unit': secondary_unit_label,
                'data': []}
    if dataset.primary_property_label:
        response['primary-property'] = dataset.primary_property_label
    if dataset.secondary_property_label:
        response['secondary-property'] = (
            f'{dataset.secondary_property.name} '
            f'({dataset.secondary_property_label})')
    for subset in dataset.subsets.all():
        response['data'].append({})
        this_subset = response['data'][-1]
        this_subset['subset-label'] = subset.label
        fixed_values = []
        for value in models.NumericalValueFixed.objects.filter(subset=subset):
            fixed_values.append(f' {value.physical_property} = '
                                f'{value.formatted()} {value.unit}')
        if this_subset['subset-label']:
            this_subset['subset-label'] = (
                f"{this_subset['subset-label']}:{','.join(fixed_values)}")
        else:
            this_subset['subset-label'] = (','.join(fixed_values)).lstrip()
        this_subset['subset-label'] += (
            f' ({models.Subset.CRYSTAL_SYSTEMS[subset.crystal_system][1]})')
        values = models.NumericalValue.objects.filter(
            datapoint__subset=subset).order_by(
                'datapoint_id', 'qualifier').values_list('value', flat=True)
        this_subset['values'] = []
        for i in range(0, len(values), 2):
            this_subset['values'].append({'y': values[i], 'x': values[i+1]})
    return JsonResponse(response)


def get_subset_values(request, pk):
    """Return the numerical values of a subset as a formatted list."""
    values = models.NumericalValue.objects.filter(
        datapoint__subset__pk=pk).select_related(
            'error').select_related('upperbound').order_by(
                'qualifier', 'datapoint__pk')
    total_len = len(values)
    y_len = total_len
    # With both x- and y-values, the y-values make up half the list.
    if values.last().qualifier == models.NumericalValue.SECONDARY:
        y_len = int(y_len/2)
    response = []
    for i in range(y_len):
        response.append({'y': values[i].formatted()})
    for i in range(y_len, total_len):
        response[i-y_len]['x'] = values[i].formatted()
    return JsonResponse(response, safe=False)


def get_atomic_coordinates(request, pk):
    return JsonResponse(utils.atomic_coordinates_as_json(pk))


def get_jsmol_input(request, pk):
    """Return a statement to be executed by JSmol.

    Go through the atomic structure data subsets of the representative
    data set of the given system. Pick the first one that comes with a
    geometry file and construct the "load data ..." statement for
    JSmol. If there are no geometry files return an empty response.

    """
    dataset = models.Dataset.objects.get(pk=pk)
    if not dataset:
        return HttpResponse()
    if dataset.input_files.exists():
        filename = os.path.basename(
            dataset.input_files.first().dataset_file.path)
        return HttpResponse(
            f'load /media/data_files/dataset_{dataset.pk}/{filename} '
            '{1 1 1}')
    return HttpResponse()


def report_issue(request):
    pk = request.POST['pk']
    description = request.POST['description']
    user = request.user
    if user.is_authenticated:
        body = (f'Description:<blockquote>{description}</blockquote>'
                f'This report was issued by {escape(user.username)} '
                f'({escape(user.email)}).<br>'
                f'Data set location: {request.scheme}://'
                f'{request.get_host()}/materials/dataset/{pk}.')
        email_addresses = list(User.objects.filter(
            is_superuser=True).values_list('email', flat=True))
        send_mail(
            f'Issue report about dataset {pk}', '', 'matd3info',
            email_addresses,
            fail_silently=False,
            html_message=body,
        )
        messages.success(request, 'Your report has been registered.')
    else:
        messages.error(request,
                       'You must be logged in to perform this action.')
    return redirect(request.POST['return-path'])


def extract_k_from_control_in(request):
    """Extract the k-point path from the provided control.in."""
    content = UploadedFile(request.FILES['file']).read().decode('utf-8')
    k_labels = []
    for line in content.splitlines():
        if re.match(r' *output\b\s* band', line):
            words = line.split()
            k_labels.append(f'{words[-2]} {words[-1]}')
    return HttpResponse('\n'.join(k_labels))


def prefilled_form(request, pk):
    """Return a mostly filled form as json.

    The form is filled based on data set pk. Fields such the actual
    numerical values are not filled in.

    """
    def pk_or_none(obj):
        if obj:
            return obj.pk
        return None

    def bool_to_text(value):
        """Return boolean as text.

        Due to the way the templating system work, this is required
        for certain inputs.

        """
        if value:
            return 'True'
        return 'False'
    dataset = get_object_or_404(models.Dataset, pk=pk)
    form = {
        'values': {
            'select_reference': pk_or_none(dataset.reference),
            'select_system': dataset.system.pk,
            'primary_property': dataset.primary_property.pk,
            'primary_unit': pk_or_none(dataset.primary_unit),
            'secondary_property': pk_or_none(dataset.secondary_property),
            'secondary_unit': pk_or_none(dataset.secondary_unit),
            'caption': dataset.caption,
            'extraction_method': dataset.extraction_method,
            'primary_property_label': dataset.primary_property_label,
            'secondary_property_label': dataset.secondary_property_label,
            'is_figure': dataset.is_figure,
            'visible_to_public': dataset.visible,
            'two_axes': bool(dataset.secondary_property),
            'origin_of_data': ('is_experimental' if dataset.is_experimental
                               else 'is_theoretical'),
            'sample_type': dataset.sample_type,
            'dimensionality_of_the_inorganic_component': (
                dataset.dimensionality),
            'with_synthesis_details': bool_to_text(dataset.synthesis.exists()),
            'with_experimental_details': bool_to_text(
                dataset.experimental.exists()),
            'with_computational_details': bool_to_text(
                dataset.computational.exists())
        },
    }

    def change_key(dictionary, key_old, key_new):
        dictionary[key_new] = dictionary[key_old]
        del dictionary[key_old]

    if dataset.synthesis.exists():
        synthesis = dataset.synthesis.first()
        for field in filter(lambda field: type(field) is TextField,
                            models.SynthesisMethod._meta.get_fields()):
            form['values'][field.name] = getattr(synthesis, field.name)
        change_key(form['values'], 'description', 'synthesis_description')
        if hasattr(synthesis, 'comment'):
            form['values']['synthesis_comment'] = synthesis.comment.text
    if dataset.experimental.exists():
        experimental = dataset.experimental.first()
        for field in filter(lambda field: type(field) is TextField,
                            models.ExperimentalDetails._meta.get_fields()):
            form['values'][field.name] = getattr(experimental, field.name)
        change_key(form['values'], 'method', 'experimental_method')
        change_key(form['values'], 'description', 'experimental_description')
        if hasattr(experimental, 'comment'):
            form['values']['experimental_comment'] = experimental.comment.text
    if dataset.computational.exists():
        comp = dataset.computational.first()
        for field in filter(lambda field: type(field) is TextField,
                            models.ComputationalDetails._meta.get_fields()):
            form['values'][field.name] = getattr(comp, field.name)
        if hasattr(comp, 'comment'):
            form['values']['computational_comment'] = comp.comment.text
    return JsonResponse(form)


class MintDoiView(StaffStatusMixin, generic.TemplateView):
    """Authenticate user on Figshare."""

    def get(self, request, *args, **kwargs):
        request.session['MINT_DOI_RETURN_URL'] = request.META.get(
            'HTTP_REFERER')
        request.session['MINT_DOI_DATASET_PK'] = self.kwargs['pk']
        if 'FIGSHARE_ACCESS_TOKEN' in request.session:
            return redirect(reverse('materials:figshare_callback'))
        else:
            return render(request, 'materials/figshare_client_id.html', {
                'host_url': request.get_host()
            })

    def post(self, request, *args, **kwargs):
        return redirect(
            'https://figshare.com/account/applications/authorize?'
            'response_type=token&'
            f'client_id={request.POST["consumer-id"]}')


def figshare_callback(request):
    """"Upload data to Figshare and generate a DOI."""
    def error_and_return(result):
        messages.error(request, result.json())
        return redirect(request.session['MINT_DOI_RETURN_URL'])

    if 'FIGSHARE_ACCESS_TOKEN' not in request.session:
        request.session['FIGSHARE_ACCESS_TOKEN'] = request.GET['access_token']
    headers = {
        'Authorization': f'token {request.session["FIGSHARE_ACCESS_TOKEN"]}'
    }
    dataset = models.Dataset.objects.get(
        pk=request.session['MINT_DOI_DATASET_PK'])
    title = dataset.caption
    data_location = (
        f'https://{request.get_host()}/materials/dataset/{dataset.pk}')
    data = {
        'title': title if title else f'Data set {dataset.pk}',
        'description': f'Data location: {data_location}',
        'keywords': [dataset.primary_property.name],
        'categories': [110],
        'defined_type': 'dataset',
    }
    result = requests.post('https://api.figshare.com/v2/account/articles',
                           headers=headers,
                           data=json.dumps(data))
    if result.status_code >= 400:
        return error_and_return(result)
    article_location = result.json()['location']
    data = {'link': data_location}
    result = requests.post(
        f'{article_location}/files', headers=headers, data=json.dumps(data))
    # Generate and publish DOI
    result = requests.post(f'{article_location}/reserve_doi', headers=headers)
    if result.status_code >= 400:
        return error_and_return(result)
    dataset.doi = result.json()['doi']
    dataset.save()
    result = requests.post(f'{article_location}/publish', headers=headers)
    if result.status_code >= 400:
        return error_and_return(result)
    messages.success(request,
                     'A DOI was generated and the data set was published.')
    return redirect(request.session['MINT_DOI_RETURN_URL'])
