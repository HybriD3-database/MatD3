# This file is covered by the BSD license. See LICENSE in the root directory.
import datetime
import io
import logging
import matplotlib
import numpy
import os
import re
import requests
import zipfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import BooleanField
from django.db.models import Case
from django.db.models import Q
from django.db.models import Value
from django.db.models import When
from django.db.models.fields import TextField
from django.forms import formset_factory
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from . import forms
from . import models
from . import utils
from mainproject import settings

matplotlib.use('Agg')
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
        ['organic', 'Organic Component'],
        ['inorganic', 'Inorganic Component'],
        ['author', 'Author']
    ]

    def get(self, request):
        return render(request, self.template_name,
                      {'search_terms': self.search_terms})

    def post(self, request):
        template_name = 'materials/search_results.html'
        form = forms.SearchForm(request.POST)
        search_text = ''
        # default search_term
        search_term = 'formula'
        if form.is_valid():
            search_text = form.cleaned_data['search_text']
            search_term = request.POST.get('search_term')
            systems_info = []
            systems = utils.search_result(search_term, search_text)

        args = {
            'systems': systems,
            'search_term': search_term,
            'systems_info': systems_info
        }
        return render(request, template_name, args)


class AddPubView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_reference.html'

    def get(self, request):
        search_form = forms.SearchForm()
        pub_form = forms.AddReference()
        return render(request, self.template_name, {
            'search_form': search_form,
            'pub_form': pub_form,
            'initial_state': True
        })

    def post(self, request):
        authors_info = {}
        for key in request.POST:
            if key.startswith('form-'):
                value = request.POST[key].strip()
                authors_info[key] = value
                if value == '':
                    return JsonResponse(
                        {'feedback': 'failure',
                         'text': ('Failed to submit, '
                                  'author information is incomplete.')})
        # sanity check: each author must have first name, last name,
        # institution
        assert(len(authors_info) % 3 == 0)
        author_count = len(authors_info) // 3
        pub_form = forms.AddReference(request.POST)
        if pub_form.is_valid():
            form = pub_form.save(commit=False)
            doi_isbn = pub_form.cleaned_data['doi_isbn']
            # check if doi_isbn is unique/valid, except when field is empty
            if len(doi_isbn) == 0 or len(
                    models.Reference.objects.filter(doi_isbn=doi_isbn)) == 0:
                form.author_count = author_count
                form.save()
                newPub = form
                text = 'Save success!'
                feedback = 'success'
            else:
                text = 'Failed to submit, reference is already in database.'
                feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'
        if feedback == 'failure':
            return JsonResponse({'feedback': feedback, 'text': text})
        # create and save new author objects, linking them to the
        # saved reference
        for i in range(author_count):  # for each author
            data = {}
            data['first_name'] = authors_info['form-%d-first_name' % i]
            data['last_name'] = authors_info['form-%d-last_name' % i]
            data['institution'] = authors_info['form-%d-institution' % i]
            preexistingAuthors = (
                models.Author.objects.filter(
                    first_name__iexact=data['first_name']).filter(
                        last_name__iexact=data['last_name']).filter(
                            institution__iexact=data['institution']))
            if preexistingAuthors.count() > 0:
                # use the prexisting author object
                preexistingAuthors[0].reference.add(newPub)
            else:  # this is a new author, so create a new object
                author_form = forms.AddAuthor(data)
                if(not author_form.is_valid()):
                    text = ('Failed to submit, author not valid. '
                            'Please fix the errors, and try again.')
                    feedback = 'failure'
                    break
                else:  # author_form is valid
                    form = author_form.save()
                    form.reference.add(newPub)
                    form.save()
                    text = 'Save success!'
                    feedback = 'success'
        args = {
                'feedback': feedback,
                'text': text,
                }
        return JsonResponse(args)


class SearchPubView(generic.TemplateView):
    template_name = 'materials/dropdown_list_pub.html'

    def post(self, request):
        search_form = forms.SearchForm(request.POST)
        search_text = ''
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
            author_search = (
                models.Reference.objects.filter(
                    Q(author__first_name__icontains=search_text) |
                    Q(author__last_name__icontains=search_text) |
                    Q(author__institution__icontains=search_text)).distinct())
            if len(author_search) > 0:
                search_result = author_search
            else:
                search_result = models.Reference.objects.filter(
                    Q(title__icontains=search_text) |
                    Q(journal__icontains=search_text)
                )
        return render(request, self.template_name,
                      {'search_result': search_result})


class AddAuthorsToReferenceView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_authors_to_reference.html'

    def post(self, request):
        author_count = request.POST['author_count']
        # variable number of author forms
        author_formset = formset_factory(
            forms.AddAuthor, extra=int(author_count))
        return render(request, self.template_name,
                      {'entered_author_count': author_count,
                       'author_formset': author_formset})


class SearchAuthorView(generic.TemplateView):
    """This is for add reference page"""
    template_name = 'materials/dropdown_list_author.html'

    def post(self, request):
        search_form = forms.SearchForm(request.POST)
        search_text = ''
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
            search_result = models.Author.objects.filter(
                Q(first_name__icontains=search_text) |
                Q(last_name__icontains=search_text) |
                Q(institution__icontains=search_text))
        return render(request, self.template_name,
                      {'search_result': search_result})


class AddAuthorView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_author.html'

    def get(self, request):
        input_form = forms.AddAuthor()
        return render(request, self.template_name, {
            'input_form': input_form,
        })

    def post(self, request):
        # search_form = forms.SearchForm()
        input_form = forms.AddAuthor(request.POST)
        if input_form.is_valid():
            first_name = input_form.cleaned_data['first_name'].lower()
            last_name = input_form.cleaned_data['last_name'].lower()
            institution = input_form.cleaned_data['institution'].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                models.Author.objects.filter(first_name__iexact=first_name)
                .filter(last_name__iexact=last_name)
                .filter(institution__icontains=institution)
                )
            if q_set_len == 0:
                input_form.save()
                text = 'Author successfully added!'
                feedback = 'success'
            else:
                text = 'Failed to submit, author is already in database.'
                feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'
        args = {
                # 'input_form': input_form,
                'feedback': feedback,
                'text': text
                }
        return JsonResponse(args)


class SearchSystemView(generic.TemplateView):
    template_name = 'materials/dropdown_list_system.html'

    def post(self, request):
        form = forms.SearchForm(request.POST)
        related_synthesis = ('related_synthesis' in request.POST and
                             request.POST['related_synthesis'] == 'True')
        search_text = ''
        if form.is_valid():
            search_text = form.cleaned_data['search_text']
        search_result = models.System.objects.filter(
            Q(compound_name__icontains=search_text) |
            Q(group__icontains=search_text) |
            Q(formula__icontains=search_text)
        )
        # ajax version
        return render(request, self.template_name,
                      {'search_result': search_result,
                       'related_synthesis': related_synthesis})


class AddSystemView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_system.html'

    def get(self, request):
        form = forms.AddSystem()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = forms.AddSystem(request.POST)
        if form.is_valid():
            compound_name = form.cleaned_data['compound_name'].lower()
            formula = form.cleaned_data['formula'].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                models.System.objects.filter(
                    Q(compound_name__iexact=compound_name) |
                    Q(formula__iexact=formula)
                )
            )
            if q_set_len == 0:
                form.save()
                text = 'System successfully added!'
                feedback = 'success'
            else:
                text = 'Failed to submit, system is already in database.'
                feedback = 'failure'
        else:
            # return render(request, self.template_name, {'form': form})
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'
        args = {'feedback': feedback, 'text': text}
        return JsonResponse(args)


class AddDataView(StaffStatusMixin, generic.TemplateView):
    template_name = 'materials/add_data.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'main_form': forms.AddDataForm(),
            'property_form': forms.AddPropertyForm(),
            'unit_form': forms.AddUnitForm(),
        })


class SystemUpdateView(generic.UpdateView):
    model = models.System
    template_name = 'materials/system_update_form.html'
    form_class = forms.AddSystem
    success_url = '/materials/{pk}'


@login_required
def add_property(request):
    name = request.POST['property_name']
    models.Property.objects.create(created_by=request.user, name=name)
    messages.success(request,
                     f'New property "{name}" successfully added to '
                     'the database!')
    return redirect(reverse('materials:add_data'))


@login_required
def add_unit(request):
    label = request.POST['unit_label']
    models.Unit.objects.create(created_by=request.user, label=label)
    messages.success(request,
                     f'New unit "{label}" successfully added to '
                     'the database!')
    return redirect(reverse('materials:add_data'))


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
        return float(value), value_type, error

    def add_numerical_value(numerical_values, errors, value,
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
        value, value_type, error = clean_value(value)
        numerical_value.value = value
        numerical_value.value_type = value_type
        numerical_values.append(numerical_value)
        errors.append(error)

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

    def generate_numerical_value_ids(array):
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
                filtered_list.append(models.Error(created_by=request.user,
                                                  numerical_value_id=pk,
                                                  value=array[i]))
        return filtered_list

    def error_and_return(dataset, text, form):
        """Shortcut for returning with info about the error."""
        messages.error(request, text)
        dataset.delete()
        return render(request, 'materials/add_data.html', {'main_form': form})

    def skip_this_line(line):
        """Test whether the line is empty or a comment."""
        return re.match(r'\s*#', line) or not line or line == '\r'

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
        return render(request, 'materials/add_data.html', {'main_form': form})
    # Create data set
    dataset = models.Dataset(created_by=request.user)
    dataset.system = form.cleaned_data['select_system']
    dataset.reference = form.cleaned_data['select_reference']
    dataset.label = form.cleaned_data['label']
    dataset.primary_property = form.cleaned_data['primary_property']
    dataset.primary_unit = form.cleaned_data['primary_unit']
    dataset.primary_property_label = form.cleaned_data[
        'primary_property_label']
    dataset.secondary_property = form.cleaned_data['secondary_property']
    dataset.secondary_unit = form.cleaned_data['secondary_unit']
    dataset.secondary_property_label = form.cleaned_data[
        'secondary_property_label']
    dataset.visible = form.cleaned_data['visible_to_public']
    dataset.is_figure = form.cleaned_data['is_figure']
    dataset.is_experimental = (
        form.cleaned_data['origin_of_data'] == 'is_experimental')
    dataset.dimensionality = form.cleaned_data['dimensionality_of_the_system']
    dataset.sample_type = form.cleaned_data['sample_type']
    dataset.crystal_system = form.cleaned_data['crystal_system']
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
        computational.kgrid = form.cleaned_data['k_point_grid']
        computational.relativity_level = form.cleaned_data[
            'level_of_relativity']
        computational.basis = form.cleaned_data['basis_set_definition']
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
                    return error_and_return(dataset,
                                            'Could not process url for the '
                                            f'external repository: "{url}"',
                                            form)
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
    for i_subset in range(1, int(form.cleaned_data['number_of_subsets']) + 1):
        # Create data subset
        subset = models.Subset(created_by=request.user, dataset=dataset)
        if 'subset_label_' + str(i_subset) in form.cleaned_data:
            subset.label = form.cleaned_data['subset_label_' + str(i_subset)]
        subset.save()
        # Go through exceptional cases first. Some properties such as
        # "atomic structure" require special treatment.
        if dataset.primary_property.name == 'atomic structure':
            for symbol, key in (('a', 'a'), ('b', 'b'), ('c', 'c'),
                                ('α', 'alpha'), ('β', 'beta'), ('γ', 'gamma')):
                datapoint = models.Datapoint.objects.create(
                    created_by=request.user, subset=subset)
                datapoint.symbols.create(created_by=request.user, value=symbol)
                name = 'lattice_constant_' + key + '_' + str(i_subset)
                value, value_type, error = clean_value(form.cleaned_data[name])
                models.NumericalValue.objects.create(created_by=request.user,
                                                     datapoint=datapoint,
                                                     value_type=value_type,
                                                     value=value)
                if error:
                    models.Error.objects.create(
                        created_by=request.user,
                        numerical_value=models.NumericalValue.objects.last(),
                        value=float(error))
            lattice_vectors = []
            lattice_errors = []  # dummy
            for line in form.cleaned_data[
                    'atomic_coordinates_' + str(i_subset)].split('\n'):
                try:
                    if line.startswith('lattice_vector'):
                        m = re.match(r'\s*lattice_vector' +
                                     3*r'\s+(-?\d+(?:\.\d+)?)' + r'\b', line)
                        coords = m.groups()
                        models.Datapoint.objects.create(
                            created_by=request.user, subset=subset)
                        for i_coord, coord in enumerate(coords):
                            add_numerical_value(lattice_vectors,
                                                lattice_errors,
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
                            add_numerical_value(numerical_values, errors,
                                                coord, counter=i_coord)
                except AttributeError:
                    # Skip comments and empty lines
                    if not re.match(r'(?:\r?$|#|//)', line):
                        return error_and_return(
                            dataset, f'Could not process line: {line}', form)
            add_datapoint_ids(lattice_vectors, 9, 3)
            models.NumericalValue.objects.bulk_create(lattice_vectors)
        elif dataset.primary_property.name == 'band structure':
            # Get kpoints
            k_labels = []
            for line in form.cleaned_data[
                    'subset_datapoints_' + str(i_subset)].splitlines():
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
                        dataset,
                        f'Rename {os.path.basename(f.dataset_file.name)} '
                        '(this name is reserved)', form)
            # The band files need to be alphabeticaly sorted
            for i in range(len(files)):
                for j in range(i+1, len(files)):
                    if files[i].name > files[j].name:
                        files[i], files[j] = files[j], files[i]
            utils.plot_band_structure(k_labels, files, dataset)
        elif form.cleaned_data['two_axes']:
            try:
                for line in form.cleaned_data[
                        'subset_datapoints_' + str(i_subset)].splitlines():
                    if skip_this_line(line):
                        continue
                    x_value, y_value = line.split()[:2]
                    datapoints.append(models.Datapoint(
                        created_by=request.user, subset=subset))
                    add_numerical_value(numerical_values, errors, x_value,
                                        is_secondary=True)
                    add_numerical_value(numerical_values, errors, y_value)
            except ValueError:
                return error_and_return(
                    dataset, f'Could not process line: {line}', form)
        else:
            try:
                for line in form.cleaned_data[
                        'subset_datapoints_' + str(i_subset)].splitlines():
                    if skip_this_line(line):
                        continue
                    for value in line.split():
                        datapoints.append(models.Datapoint(
                            created_by=request.user, subset=subset))
                        add_numerical_value(numerical_values, errors, value)
            except ValueError:
                return error_and_return(
                    dataset, f'Could not process line: {line}', form)
        # Fixed properties
        counter = 0
        for key in form.cleaned_data:
            if key.startswith('fixed_property_' + str(i_subset) + '_'):
                suffix = key.split('fixed_property_')[1]
                fixed_value = models.NumericalValueFixed(
                    created_by=request.user, subset=subset, counter=counter)
                fixed_value.physical_property = (
                    form.cleaned_data['fixed_property_' + suffix])
                fixed_value.unit = form.cleaned_data['fixed_unit_' + suffix]
                value, value_type, error = clean_value(
                    form.cleaned_data['fixed_value_' + suffix])
                fixed_value.value = value
                fixed_value.value_type = value_type
                if error:
                    fixed_value.error = error
                fixed_value.save()
                counter += 1
    # Insert the main data into the database
    models.Datapoint.objects.bulk_create(datapoints)
    add_datapoint_ids(numerical_values, len(numerical_values), len(datapoints))
    models.NumericalValue.objects.bulk_create(numerical_values)
    models.Error.objects.bulk_create(generate_numerical_value_ids(errors))
    add_datapoint_ids(symbols, len(symbols), len(datapoints))
    models.Symbol.objects.bulk_create(symbols)
    # Linked data sets
    for pk in form.cleaned_data['related_data_sets'].split():
        try:
            dataset.linked_to.add(models.Dataset.objects.get(pk=pk))
        except models.Dataset.DoesNotExist:
            return error_and_return(
                dataset, f'Related data set {pk} does not exist', form)
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
    messages.success(request, message)
    return redirect(reverse('materials:add_data'))


@dataset_author_check
def toggle_visibility(request, pk, return_url):
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.visible = not dataset.visible
    dataset.save()
    return redirect(return_url)


@dataset_author_check
def toggle_is_figure(request, pk, return_url):
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.is_figure = not dataset.is_figure
    dataset.save()
    return redirect(return_url)


@dataset_author_check
def delete_dataset(request, pk, return_url):
    """Delete current data set and all associated files."""
    dataset = models.Dataset.objects.get(pk=pk)
    dataset.delete()
    if not return_url.startswith('/'):
        return_url = '/' + return_url
    return redirect(return_url)


def dataset_files(request, pk):
    dataset = models.Dataset.objects.get(pk=pk)
    in_memory_object = io.BytesIO()
    zf = zipfile.ZipFile(in_memory_object, 'w')
    for file_ in (f.dataset_file.path for f in dataset.files.all()):
        zf.write(file_, os.path.join('files', os.path.basename(file_)))
    zf.close()
    response = HttpResponse(in_memory_object.getvalue(),
                            content_type='application/x-zip-compressed')
    response['Content-Disposition'] = f'attachment; filename=files.zip'
    return response


def dataset_data(request, pk):
    """Return the data set as a text file."""
    dataset = models.Dataset.objects.get(pk=pk)
    subset = dataset.subsets.first()
    text = ''
    x_value = ''
    y_value = ''
    for datapoint in subset.datapoints.all():
        for value in datapoint.values.all():
            if value.qualifier == models.NumericalValue.SECONDARY:
                x_value = value.value
            elif value.qualifier == models.NumericalValue.PRIMARY:
                y_value = value.value
        text += f'{x_value} {y_value}\n'
    return HttpResponse(text, content_type='text/plain')


def dataset_image(request, pk):
    """Return a png image of the data set."""
    from matplotlib import pyplot
    dataset = models.Dataset.objects.get(pk=pk)
    subset = dataset.subsets.first()
    datapoints = subset.datapoints.all()
    x_values = numpy.zeros(len(datapoints))
    y_values = numpy.zeros(len(datapoints))
    for i_dp, datapoint in enumerate(datapoints):
        x_value = datapoint.values.get(
            qualifier=models.NumericalValue.SECONDARY)
        x_values[i_dp] = x_value.value
        y_value = datapoint.values.get(qualifier=models.NumericalValue.PRIMARY)
        y_values[i_dp] = y_value.value
    pyplot.plot(x_values, y_values, '-o', linewidth=0.5, ms=3)
    pyplot.title(dataset.label)
    pyplot.ylabel(f'{dataset.primary_property.name}, '
                  f'{dataset.primary_unit.label}')
    pyplot.xlabel(f'{dataset.secondary_property.name}, '
                  f'{dataset.secondary_unit.label}')
    in_memory_object = io.BytesIO()
    pyplot.savefig(in_memory_object, format='png')
    image = in_memory_object.getvalue()
    pyplot.close()
    in_memory_object.close()
    return HttpResponse(image, content_type='image/png')


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
            'error').order_by('qualifier', 'datapoint__pk')
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
    data set of the given system. Pick the first one where the lattice
    vectors and atomic coordinates are present and can be converted to
    floats. Construct the "load data ..." inline statement suitable
    for JSmol. If there are no atomic structure data or none of the
    data sets are usable (some lattice parameters or atomic
    coordinates missing or not valid numbers) return an empty
    response.

    """
    datasets = models.Dataset.objects.filter(system__pk=pk).filter(
        primary_property__name='atomic structure')
    if not datasets:
        return HttpResponse()
    dataset = datasets.get(representative=True)
    for subset in dataset.subsets.all():
        data = utils.atomic_coordinates_as_json(subset.pk)
        lattice_vectors = []
        try:
            for vector in data['vectors']:
                lattice_vectors.append([float(x) for x in vector])
            if len(lattice_vectors) == 3:
                coord_type = data['coord-type']
                response = io.StringIO()
                response.write("load data 'model'|#AIMS|")
                if coord_type == 'atom_frac':
                    for symbol, *coords in data['coordinates']:
                        coords_f = [float(x) for x in coords]
                        x, y, z = [sum(
                            [coords_f[i_dir]*lattice_vectors[i_dir][comp]
                             for i_dir in range(3)]) for comp in range(3)]
                        response.write(f'atom {x} {y} {z} {symbol}|')
                else:
                    for symbol, coord_x, coord_y, coord_z in data[
                            'coordinates']:
                        response.write(
                            f'atom {coord_x} {coord_y} {coord_z} {symbol}|')
                response.write("end 'model' unitcell [")
                for x, y, z in data['vectors']:
                    response.write(f' {x} {y} {z}')
                response.write(']')
                return HttpResponse(response.getvalue())
        except (KeyError, ValueError):
            pass
    return HttpResponse()


def get_dropdown_options(request, name):
    """Return a list of options for Selectize."""
    model_types = {
        'reference': models.Reference,
        'system': models.System,
        'property': models.Property,
        'unit': models.Unit,
    }
    model = re.sub(r'^.*(reference|system|property|unit).*$', r'\1', name)
    data = []
    for obj in model_types[model].objects.all():
        data.append({'value': obj.pk, 'text': str(obj)})
    return JsonResponse(data, safe=False)


def report_issue(request):
    pk = request.POST['pk']
    description = request.POST['description']
    user = request.user
    if user.is_authenticated:
        body = (f'Description:\n\n<blockquote>{description}</blockquote>'
                'This report was issued by the user '
                f'{user.username} ({user.email})')
        email_addresses = list(User.objects.filter(
            is_superuser=True).values_list('email', flat=True))
        send_mail(
            f'Issue report about dataset {pk}',
            '',
            'report@hybrid3',
            email_addresses,
            fail_silently=False,
            html_message=body,
        )
        messages.success(request, 'Your report has been registered.')
    else:
        messages.error(request,
                       'You must be logged in to perform this action.')
    return redirect(request.POST['return-path'])


def reference_data(request, pk):
    """Return a key-value representation of the data set.

    The representation conforms to the one used in Qresp
    (http://qresp.org/).

    """
    data = {}
    data['info'] = {
        'downloadPath': request.get_host(),
        'fileServerPath': '',
        'folderAbsolutePath': '',
        'insertedBy': {
            'firstName': '',
            'lastName': '',
            'middleName': ''
        },
        'isPublic': 'true',
        'notebookFile': '',
        'notebookPath': '',
        'serverPath': request.get_host(),
        'timeStamp': datetime.datetime.now()
    }
    reference = models.Reference.objects.get(pk=pk)
    data['reference'] = {}
    data['reference']['journal'] = {
        'abbrevName': reference.journal,
        'fullName': reference.journal,
        'kind': 'journal',
        'page': reference.pages_start,
        'publishedAbstract': '',
        'publishedDate': '',
        'receivedDate': '',
        'title': reference.title,
        'volume': reference.vol,
        'year': reference.year,
    }
    data['reference']['authors'] = []
    for author in reference.author_set.all():
        data['reference']['authors'].append({
            'firstname': author.first_name,
            'lastname': author.last_name,
        })
    data['PIs'] = []
    data['PIs'].append({'firstname': '', 'lastname': ''})
    data['collections'] = []
    data['collections'].append('')
    datasets = reference.dataset_set.all()
    data['charts'] = []
    dataset_counter = 1
    for dataset in datasets:
        chart = {
            'caption': dataset.label,
            'files': [f'/materials/dataset-{dataset.pk}/data.txt'],
            'id': '',
            'imageFile': f'/materials/dataset-{dataset.pk}/image.png',
            'kind': 'figure' if dataset.is_figure else 'table',
            'notebookFile': '',
            'number': dataset_counter,
            'properties': [],
        }
        if dataset.secondary_property:
            chart['properties'].append(dataset.secondary_property.name)
        if dataset.primary_property:
            chart['properties'].append(dataset.primary_property.name)
        loc = os.path.join(settings.MEDIA_ROOT,
                           f'uploads/dataset_{dataset.pk}')
        if os.path.isdir(loc):
            for file_ in os.listdir(loc):
                chart['files'].append(settings.MEDIA_URL +
                                      f'uploads/dataset_{dataset.pk}/{file_}')
        data['charts'].append(chart)
        dataset_counter += 1
    response = JsonResponse(data)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response


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
            'label': dataset.label,
            'extraction_method': dataset.extraction_method,
            'primary_property_label': dataset.primary_property_label,
            'secondary_property_label': dataset.secondary_property_label,
            'is_figure': dataset.is_figure,
            'visible_to_public': dataset.visible,
            'two_axes': bool(dataset.secondary_property),
            'origin_of_data': ('is_experimental' if dataset.is_experimental
                               else 'is_theoretical'),
            'sample_type': dataset.sample_type,
            'dimensionality_of_the_system': dataset.dimensionality,
            'crystal_system': dataset.crystal_system,
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
