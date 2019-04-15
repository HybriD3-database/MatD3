import datetime
import functools
import io
import logging
import matplotlib
import numpy
import operator
import os
import re
import zipfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import reverse
from django.views import generic

from accounts.models import UserProfile
from mainproject import settings
from materials import forms
from materials import models
import materials.rangeparser


matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def dataset_author_check(view):
    """Test whether the logged on user is the creator of the data set."""
    @login_required
    def wrap(request, *args, **kwargs):
        dataset = get_object_or_404(models.Dataset, pk=kwargs['dataset_pk'])
        if dataset.created_by == request.user:
            return view(request, *args, **kwargs)
        else:
            logger.warning(f'Data set was created by {dataset.created_by} but '
                           'an attempt was made to delete it by '
                           f'{request.user}',
                           extra={'request': request})
            return PermissionDenied
    wrap.__doc__ = view.__doc__
    wrap.__name__ = view.__name__
    return wrap


def data_dl(request, data_type, pk, bandgap=False):
    """Download a specific entry type"""
    response = HttpResponse(content_type='text/fhi-aims')
    if data_type == 'band_gap':
        data_type = 'band_structure'
        bandgap = True

    def write_headers():
        if data_type not in ['all_atomic_positions']:
            if not bandgap:
                response.write(str('#HybriD³ Materials Database\n'))
            response.write(str('\n#System: '))
            response.write(str(p_obj.compound_name))
        response.write(str('\n#Temperature: '))
        response.write(str(obj.temperature + ' K'))
        response.write(str('\n#Phase: '))
        response.write(str(obj.phase.phase))
        authors = obj.reference.author_set.all()
        response.write(str('\n#Authors ('+str(authors.count())+'): '))
        for author in authors:
            response.write('\n    ')
            response.write(author.first_name + ' ')
            response.write(author.last_name)
            response.write(', ' + author.institution)
        response.write(str('\n#Journal: '))
        response.write(str(obj.reference.journal))
        response.write(str('\n#Source: '))
        if obj.reference.doi_isbn:
            response.write(str(obj.reference.doi_isbn))
        else:
            response.write(str('N/A'))

    def write_a_pos():
        response.write('\n#a: ')
        response.write(obj.a)
        response.write('\n#b: ')
        response.write(obj.b)
        response.write('\n#c: ')
        response.write(obj.c)
        response.write('\n#alpha: ')
        response.write(obj.alpha)
        response.write('\n#beta: ')
        response.write(obj.beta)
        response.write('\n#gamma: ')
        response.write(obj.gamma)
        response.write('\n\n')

    if data_type == 'atomic_positions':
        obj = models.AtomicPositions.objects.get(pk=pk)
        p_obj = models.System.objects.get(atomicpositions=obj)
        write_headers()
        write_a_pos()
        fileloc = (settings.MEDIA_ROOT + '/uploads/%s_%s_%s_apos.in' %
                   (obj.phase, p_obj.organic, p_obj.inorganic))
        if(os.path.isfile(fileloc)):
            with open(fileloc, encoding='utf-8', mode='r+') as f:
                lines = f.read().splitlines()
                for line in lines:
                    response.write(line + '\n')
        else:
            response.write('#-Atomic Positions input file not available-')
        response['Content-Disposition'] = (
            'attachment; filename=%s_%s_%s_%s.in' % (
                obj.phase, p_obj.organic, p_obj.inorganic, data_type))
    elif data_type == 'all_atomic_positions':  # all the a_pos entries
        p_obj = models.System.objects.get(pk=pk)
        response.write(str('#HybriD³ Materials Database\n\n'))
        name = p_obj.compound_name
        response.write(str('#'*(len(name)+22) + '\n'))
        response.write(str('#####  System: '))
        response.write(str(name))
        response.write(str('  #####\n#' + '#'*(len(name)+22) + '\n'))
        for obj in p_obj.atomicpositions_set.all():
            write_headers()
            write_a_pos()
        response['Content-Disposition'] = (
            'attachment; filename=%s_%s_%s_%s.in' % (obj.phase, p_obj.organic,
                                                     p_obj.inorganic, 'ALL'))
    elif data_type == 'exciton_emission':
        obj = models.ExcitonEmission.objects.get(pk=pk)
        p_obj = models.System.objects.get(excitonemission=obj)
        file_name_prefix = '%s_%s_%s_pl' % (obj.phase, p_obj.organic,
                                            p_obj.inorganic)
        dir_in_str = os.path.join(settings.MEDIA_ROOT, 'uploads')
        meta_filename = file_name_prefix + '.txt'
        meta_filepath = os.path.join(dir_in_str, meta_filename)
        with open(meta_filepath, encoding='utf-8', mode='w+') as meta_file:
            meta_file.write(str('#HybriD³ Materials Database\n'))
            meta_file.write(str('\n#System: '))
            meta_file.write(str(p_obj.compound_name))
            meta_file.write(str('\n#Temperature: '))
            meta_file.write(str(obj.temperature))
            meta_file.write(str('\n#Phase: '))
            meta_file.write(str(obj.phase.phase))
            meta_file.write(str('\n#Authors: '))
            for author in obj.reference.author_set.all():
                meta_file.write('\n    ')
                meta_file.write(author.first_name + ' ')
                meta_file.write(author.last_name)
                meta_file.write(', ' + author.institution)
            meta_file.write(str('\n#Journal: '))
            meta_file.write(str(obj.reference.journal))
            meta_file.write(str('\n#Source: '))
            meta_file.write(str(obj.reference.doi_isbn))
            meta_file.write(str('\n#Exciton Emission Peak: '))
            meta_file.write(str(obj.excitonemission))
        pl_file_csv = os.path.join(dir_in_str, file_name_prefix + '.csv')
        pl_file_html = os.path.join(dir_in_str, file_name_prefix + '.html')
        filenames = []
        filenames.append(meta_filepath)
        filenames.append(pl_file_csv)
        filenames.append(pl_file_html)

        zip_dir = file_name_prefix
        zip_filename = '%s.zip' % zip_dir
        # change response type and content deposition type
        string = io.BytesIO()
        zf = zipfile.ZipFile(string, 'w')

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_dir, fname)
            zf.write(fpath, zip_path)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(string.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           zip_filename)
    elif data_type == 'synthesis':
        obj = models.SynthesisMethodOld.objects.get(pk=pk)
        p_obj = models.System.objects.get(synthesismethodold=obj)
        file_name_prefix = '%s_%s_%s_syn' % (obj.phase, p_obj.organic,
                                             p_obj.inorganic)
        meta_filename = file_name_prefix + '.txt'
        response = HttpResponse(content_type='text/plain')
        response.write(str('#HybriD³ Materials Database\n'))
        response.write(str('\n#System: '))
        response.write(str(p_obj.compound_name))
        response.write(str('\n#Temperature: '))
        response.write(str(obj.temperature))
        response.write(str('\n#Phase: '))
        response.write(str(obj.phase.phase))
        response.write(str('\n#Authors: '))
        for author in obj.reference.author_set.all():
            response.write('\n    ')
            response.write(author.first_name + ' ')
            response.write(author.last_name)
            response.write(', ' + author.institution)
        response.write(str('\n#Journal: '))
        response.write(str(obj.reference.journal))
        response.write(str('\n#Source: '))
        response.write(str(obj.reference.doi_isbn))
        if obj.synthesis_method:
            response.write(str('\n#Synthesis Method: '))
            response.write(str(obj.synthesis_method))
        if obj.starting_materials:
            response.write(str('\n#Starting Materials: '))
            response.write(str(obj.starting_materials))
        if obj.remarks:
            response.write(str('\n#Remarks: '))
            response.write(str(obj.remarks))
        if obj.product:
            response.write(str('\n#Product: '))
            response.write(str(obj.product))
        response.encoding = 'utf-8'
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           (meta_filename))
    elif data_type == 'band_structure' and bandgap:
        obj = models.BandStructure.objects.get(pk=pk)
        p_obj = models.System.objects.get(bandstructure=obj)
        filename = '%s_%s_%s_bg.txt' % (obj.phase, p_obj.organic,
                                        p_obj.inorganic)
        response.write(str('#HybriD³ Materials Database\n\n'))
        response.write('****************\n')
        response.write('Band gap: ')
        if obj.band_gap != '':
            response.write(obj.band_gap + ' eV')
        else:
            response.write('N/A')
        response.write('\n****************\n')
        write_headers()
        response.encoding = 'utf-8'
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           (filename))
    elif data_type == 'band_structure':
        obj = models.BandStructure.objects.get(pk=pk)
        p_obj = models.System.objects.get(bandstructure=obj)
        file_name_prefix = '%s_%s_%s_%s_bs' % (obj.phase, p_obj.organic,
                                               p_obj.inorganic, obj.pk)
        dir_in_str = os.path.join(settings.MEDIA_ROOT, obj.folder_location)
        compound_name = dir_in_str.split('/')[-1]
        meta_filename = file_name_prefix + '.txt'
        meta_filepath = os.path.join(dir_in_str, meta_filename)
        with open(meta_filepath, encoding='utf-8', mode='w+') as meta_file:
            meta_file.write('#HybriD3 Materials Database\n')
            meta_file.write('\n#System: ')
            meta_file.write(p_obj.compound_name)
            meta_file.write('\n#Temperature: ')
            meta_file.write(obj.temperature)
            meta_file.write('\n#Phase: ')
            meta_file.write(str(obj.phase.phase))
            meta_file.write(str('\n#Authors: '))
            for author in obj.reference.author_set.all():
                meta_file.write('\n    ')
                meta_file.write(author.first_name + ' ')
                meta_file.write(author.last_name)
                meta_file.write(', ' + author.institution)
            meta_file.write('\n#Journal: ')
            meta_file.write(str(obj.reference.journal))
            meta_file.write('\n#Source: ')
            meta_file.write(str(obj.reference.doi_isbn))
        bs_full = os.path.join(dir_in_str, file_name_prefix + '_full.png')
        bs_mini = os.path.join(dir_in_str, file_name_prefix + '_min.png')
        filenames = []
        filenames.append(bs_full)
        filenames.append(bs_mini)
        for f in os.listdir(dir_in_str):
            filename = os.fsdecode(f)
            if filename.endswith('.in') or filename.endswith('.out') or (
                    filename.endswith('.txt')):
                full_filename = os.path.join(dir_in_str, filename)
                filenames.append(full_filename)
        zip_dir = compound_name
        zip_filename = '%s.zip' % zip_dir
        # change response type and content deposition type
        string = io.BytesIO()
        zf = zipfile.ZipFile(string, 'w')

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_dir, fname)
            zf.write(fpath, zip_path)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(string.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           zip_filename)
    elif data_type == 'input_files':
        obj = models.BandStructure.objects.get(pk=pk)
        p_obj = models.System.objects.get(bandstructure=obj)
        file_name_prefix = '%s_%s_%s_%s_bs' % (obj.phase, p_obj.organic,
                                               p_obj.inorganic, obj.pk)
        dir_in_str = os.path.join(settings.MEDIA_ROOT, obj.folder_location)
        compound_name = dir_in_str.split('/')[-1]
        filenames = []
        for F in ('control.in', 'geometry.in'):
            if os.path.exists(f'{dir_in_str}/{F}'):
                filenames.append(f'{dir_in_str}/{F}')
        zip_dir = compound_name
        zip_filename = f'{zip_dir}.zip'
        # change response type and content deposition type
        string = io.BytesIO()
        zf = zipfile.ZipFile(string, 'w')
        for fpath in filenames:
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_dir, fname)
            zf.write(fpath, zip_path)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(string.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           zip_filename)
    return response


def all_a_pos(request, pk):
    """Defines views for each specific entry type."""
    def sortEntries(entry):
        """Sort by temperature, but temperature is a charFields"""
        try:
            return int(entry.temperature)
        except Exception:
            # temperature field contains something other than digits (e.g. N/A)
            temp = ''
            for c in entry.temperature:
                if c.isdigit():
                    temp += c
                else:
                    if temp != '':
                        return int(temp)
            # no temperature, so make this entry last
            return 9999999

    template_name = 'materials/all_a_pos.html'
    obj = models.System.objects.get(pk=pk)
    compound_name = models.System.objects.get(pk=pk).compound_name
    obj = obj.atomicpositions_set.all()
    obj = sorted(obj, key=sortEntries)
    return render(request, template_name,
                  {'object': obj, 'compound_name': compound_name, 'key': pk})


def all_entries(request, pk, data_type):
    str_to_model = {
        'atomic_positions': models.AtomicPositions,
        'exciton_emission': models.ExcitonEmission,
        'synthesis': models.SynthesisMethodOld,
        'band_structure': models.BandStructure,
    }
    template_name = 'materials/all_%ss.html' % data_type
    compound_name = models.System.objects.get(pk=pk).compound_name
    obj = str_to_model[data_type].objects.filter(system__pk=pk)
    return render(request, template_name, {
        'object': obj,
        'compound_name': compound_name,
        'data_type': data_type,
        'key': pk
    })


def getAuthorSearchResult(search_text):
    keyWords = search_text.split()
    results = models.System.objects.\
        filter(functools.reduce(operator.or_, (
            Q(atomicpositions__reference__author__last_name__icontains=x) for
            x in keyWords)) | functools.reduce(operator.or_, (
                Q(synthesismethodold__reference__author__last_name__icontains=x)
                for x in keyWords)) | functools.reduce(operator.or_, (
                        Q(excitonemission__reference__author__last_name__icontains=x)
                        for x in keyWords)) | functools.reduce(operator.or_, (
                                Q(bandstructure__reference__author__last_name__icontains=x)
                                for x in keyWords))
         ).distinct()
    return results


def search_result(search_term, search_text):
    if search_term == 'formula':
        return models.System.objects.filter(
            Q(formula__icontains=search_text) |
            Q(group__icontains=search_text) |
            Q(compound_name__icontains=search_text)).order_by('formula')
    elif search_term == 'organic':
        return models.System.objects.filter(
            organic__icontains=search_text).order_by('organic')
    elif search_term == 'inorganic':
        return models.System.objects.filter(
            inorganic__icontains=search_text).order_by('inorganic')
    elif search_term == 'author':
        return getAuthorSearchResult(search_text)
    else:
        raise KeyError('Invalid search term.')


class SearchFormView(generic.TemplateView):
    """Search for system page"""
    template_name = 'materials/search.html'
    search_terms = [
        ['formula', 'Formula'],
        ['organic', 'Organic Component'],
        ['inorganic', 'Inorganic Component'],
        ['exciton_emission', 'Exciton Emission'],
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
            if search_term == 'exciton_emission':
                searchrange = materials.rangeparser.parserange(search_text)
                if len(searchrange) > 0:
                    if searchrange[0] == 'bidirectional':
                        if searchrange[3] == '>=':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__gte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[3] == '>':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__gt=searchrange[1]).order_by(
                                    '-exciton_emission')
                        if searchrange[4] == '<=':
                            systems = systems.filter(
                                exciton_emission__lte=searchrange[2]).order_by(
                                    '-exciton_emission')
                        elif searchrange[4] == '<':
                            systems = systems.filter(
                                exciton_emission__lt=searchrange[2]).order_by(
                                    '-exciton_emission')
                    elif searchrange[0] == 'unidirectional':
                        if searchrange[2] == '>=':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__gte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '>':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__gt=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '<=':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__lte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '<':
                            systems = models.ExcitonEmission.objects.filter(
                                exciton_emission__lt=searchrange[1]).order_by(
                                    '-exciton_emission')
                    for ee in systems:
                        system_info = {}
                        system_info['compound_name'] = ee.system.compound_name
                        system_info['common_formula'] = ee.system.group
                        system_info['chemical_formula'] = ee.system.formula
                        system_info['ee'] = str(ee.exciton_emission)
                        system_info['sys_pk'] = ee.system.pk
                        system_info['ee_pk'] = ee.pk
                        if ee.system.synthesismethodold_set.count() > 0:
                            system_info['syn_pk'] = (
                                ee.system.synthesismethodold_set.first().pk)
                        else:
                            system_info['syn_pk'] = 0
                        if ee.system.atomicpositions_set.count() > 0:
                            system_info['apos_pk'] = (
                                ee.system.atomicpositions_set.first().pk)
                        else:
                            system_info['apos_pk'] = 0
                        if ee.system.bandstructure_set.count() > 0:
                            system_info['bs_pk'] = (
                                ee.system.bandstructure_set.first().pk)
                        else:
                            system_info['bs_pk'] = 0
                        systems_info.append(system_info)
            else:
                systems = search_result(search_term, search_text)

        args = {
            'systems': systems,
            'search_term': search_term,
            'systems_info': systems_info
        }
        return render(request, template_name, args)


def makeCorrections(form):
    # alter user input if necessary
    try:
        temp = form.temperature
        if temp.endswith('K') or temp.endswith('C'):
            temp = temp[:-1].strip()
            form.temperature = temp
        return form
    except Exception:  # just in case
        return form


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
                # 'search_form': search_form,
                # 'pub_form': pub_form,
                'feedback': feedback,
                'text': text,
                # 'initial_state': True,
                }
        # return render(request, self.template_name, args)
        # ajax version below
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
        author_formset = formset_factory(forms.AddAuthor, extra=int(author_count))
        return render(request, self.template_name,
                      {'entered_author_count': author_count,
                       'author_formset': author_formset})


class SearchAuthorView(generic.TemplateView):
    """This is for add reference page"""
    # template_name = 'materials/add_reference.html'
    template_name = 'materials/dropdown_list_author.html'

    def post(self, request):
        search_form = forms.SearchForm(request.POST)
        # pub_form = forms.AddReference()
        search_text = ''
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
            search_result = models.Author.objects.filter(
                Q(first_name__icontains=search_text) |
                Q(last_name__icontains=search_text) |
                Q(institution__icontains=search_text))
            # add last_name filter
        # args = {
        #     'search_form': search_form,
        #     'search_result': search_result,
        #     'pub_form': pub_form
        # }
        # return render(request, self.template_name, args)
        # ajax version
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


class AddTagView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_tag.html'

    def get(self, request):
        input_form = forms.AddTag()
        return render(request, self.template_name, {
            'input_form': input_form,
        })

    def post(self, request):
        # search_form = forms.SearchForm()
        input_form = forms.AddTag(request.POST)
        if input_form.is_valid():
            tag = input_form.cleaned_data['tag'].lower()
            q_set_len = len(
                models.Tag.objects.filter(tag__iexact=tag)
                )
            if q_set_len == 0:
                input_form.save()
                text = 'Tag successfully added!'
                feedback = 'success'
            else:
                text = 'Failed to submit, tag is already in database.'
                feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'
        args = {
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


class AddPhase(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = forms.AddPhase()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = forms.AddPhase(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']
        args = {'form': form, 'text': text}
        return render(request, self.template_name, args)


class AddTemperature(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = forms.AddTemperature()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = forms.AddTemperature(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']

        args = {'form': form, 'text': text}

        return render(request, self.template_name, args)


class AddBandStructureView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_band_structure.html'

    def get(self, request):
        search_form = forms.SearchForm()
        band_structure_form = forms.AddBandStructure()
        return render(request, self.template_name, {
            'search_form': search_form,
            'band_structure_form': band_structure_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': True
        })

    def post(self, request):
        form = forms.AddBandStructure(request.POST, request.FILES)
        if form.is_valid():
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('reference')
            sys_pk = request.POST.get('system')
            syn_pk = request.POST.get('synthesis-methods')
            try:
                new_form.synthesis_method = models.SynthesisMethodOld.objects.get(
                    pk=int(syn_pk))
            except Exception:
                # no synthesis method was chosen (or maybe an error occurred)
                pass
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.reference = models.Reference.objects.get(pk=pub_pk)
                new_form.system = models.System.objects.get(pk=sys_pk)
                # text += 'Settings ready. '
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(
                        user=request.user)
                    # save so a pk can be created for use in the
                    # folder location
                    new_form.save()
                    bs_folder_loc = ('uploads/%s_%s_%s_%s_bs' %
                                     (new_form.phase, new_form.system.organic,
                                      new_form.system.inorganic, new_form.pk))
                    new_form.folder_location = bs_folder_loc
                    try:
                        os.mkdir(bs_folder_loc)
                    except Exception:
                        pass
                    band_files = request.FILES.getlist('band_structure_files')
                    control_file = request.FILES.get('control_in_file')
                    geometry_file = request.FILES.get('geometry_in_file')
                    band_files.append(control_file)
                    band_files.append(geometry_file)
                    for f in band_files:
                        filename = f.name
                        full_filename = os.path.join(bs_folder_loc, filename)
                        with open(full_filename, 'wb+') as write_bs:
                            for chunk in f.chunks():
                                write_bs.write(chunk)
                    # have a script that goes through the band gaps
                    # and spits out some states set plotstate field to
                    # False, save once done, tell user that upload is
                    # successful after this thing, call another
                    # function that plots the BS. Once done, update
                    # the plotted state to done plotbs(bs_folder_loc)
                    new_form = makeCorrections(new_form)
                    text = 'Save success!'
                    feedback = 'success'
                    new_form.save()
                else:
                    text = 'Failed to submit, please login and try again.'
                    feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'

        args = {'feedback': feedback, 'text': text}

        return JsonResponse(args)


class AddDataView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'materials/add_data.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': forms.AddDataForm(),
        })


@login_required
def add_property(request):
    name = request.POST['property-name']
    models.Property.objects.create(created_by=request.user, name=name)
    messages.success(request,
                     f'New property "{name}" successfully added to '
                     'the database!')
    return redirect(reverse('materials:add_data'))


@login_required
def add_unit(request):
    label = request.POST['unit-label']
    models.Unit.objects.create(created_by=request.user, label=label)
    messages.success(request,
                     f'New unit "{label}" successfully added to '
                     'the database!')
    return redirect(reverse('materials:add_data'))


@login_required
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

    def add_datapoint_ids(values, step):
        """Set datapoint_id for all elements in an array.

        The data points must already have been created using
        bulk_create. Now, fetch the ids of the latest data points and
        manually attach them to each element in "values". After this
        is done, bulk_create may be called on "values".

        The step argument tells how many numerical values are
        associated with each data point.

        """
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

    def add_comment(model, label, form):
        """Shortcut for conditionally attaching comments to a model instance.

        The purpose of this shortcut is to avoid checking the presence
        of a particular type of comment in form and the created_by and
        updated_by fields with every call.

        """
        if label in form.cleaned_data:
            model.comment_set.create(created_by=request.user,
                                     text=form.cleaned_data[label])
            logger.info(f'Creating {label} comment '
                        f'#{model.comment_set.all()[0].pk}')

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
        return render(request, 'materials/add_data.html', {'form': form})
    # Create data set
    dataset = models.Dataset(created_by=request.user)
    dataset.system = form.cleaned_data['select_system']
    dataset.reference = form.cleaned_data['select_reference']
    dataset.label = form.cleaned_data['data_set_label']
    dataset.primary_property = form.cleaned_data['primary_property']
    dataset.primary_unit = form.cleaned_data['primary_unit']
    dataset.secondary_property = form.cleaned_data['secondary_property']
    dataset.secondary_unit = form.cleaned_data['secondary_unit']
    dataset.visible = form.cleaned_data['visible_to_public']
    dataset.plotted = form.cleaned_data['plotted']
    dataset.experimental = (
        form.cleaned_data['origin_of_data'] == 'experimental')
    dataset.dimensionality = form.cleaned_data['dimensionality_of_the_system']
    dataset.sample_type = form.cleaned_data['sample_type']
    dataset.crystal_system = form.cleaned_data['crystal_system']
    dataset.extraction_method = form.cleaned_data['extraction_method']
    # Make representative by default if first entry of its kind
    dataset.representative = not bool(models.Dataset.objects.filter(
        system=dataset.system).filter(
            primary_property=dataset.primary_property))
    dataset.has_files = False
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
        add_comment(synthesis, 'synthesis_comment', form)
    # Experimental details
    if form.cleaned_data['with_experimental_details']:
        experimental = models.ExperimentalDetails(created_by=request.user,
                                                  dataset=dataset)
        experimental.method = form.cleaned_data['experimental_method']
        experimental.description = form.cleaned_data[
            'experimental_description']
        experimental.save()
        logger.info(f'Creating experimental details #{experimental.pk}')
        add_comment(experimental, 'experimental_comment', form)
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
        add_comment(computational, 'computational_comment', form)
    # For best performance, the main data should be inserted with
    # calls to bulk_create. The following work arrays are are
    # populated with data during the loop over series and then
    # inserted into the database after the main loop.
    datapoints = []
    symbols = []
    numerical_values = []
    errors = []
    for i_series in range(1,
                          int(form.cleaned_data['number_of_data_series']) + 1):
        # Create data series
        dataseries = models.Dataseries(created_by=request.user,
                                       dataset=dataset)
        if 'series_label_' + str(i_series) in form.cleaned_data:
            dataseries.label = form.cleaned_data[
                'series_label_' + str(i_series)]
        dataseries.save()
        # Go through exceptional cases first. Some properties such as
        # "lattice parameter" require special treatment.
        if dataset.primary_property.require_input_files:
            pass
        elif dataset.primary_property.name == 'lattice parameter':
            for symbol, key in (('a', 'a'), ('b', 'b'), ('c', 'c'),
                                ('α', 'alpha'), ('β', 'beta'), ('γ', 'gamma')):
                datapoint = models.Datapoint.objects.create(
                    created_by=request.user, dataseries=dataseries)
                datapoint.symbol_set.create(created_by=request.user,
                                            value=symbol)
                name = 'lattice_constant_' + key + '_' + str(i_series)
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
                    'atomic_coordinates_' + str(i_series)].split('\n'):
                try:
                    if line.startswith('lattice_vector'):
                        m = re.match(r'\s*lattice_vector' +
                                     3*r'\s+(-?\d+(?:\.\d+)?)' + r'\b', line)
                        coords = m.groups()
                        models.Datapoint.objects.create(
                            created_by=request.user, dataseries=dataseries)
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
                            created_by=request.user, dataseries=dataseries))
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
                        messages.error(request,
                                       'Could not process input for '
                                       f'atomic coordinates: {line}')
                        dataset.delete()
                        return render(request, 'materials/add_data.html',
                                      {'form': form})
            add_datapoint_ids(lattice_vectors, 3)
            models.NumericalValue.objects.bulk_create(lattice_vectors)
        elif form.cleaned_data['two_axes']:
            for line in form.cleaned_data[
                    'series_datapoints_' + str(i_series)].split('\n'):
                if line.startswith('#') or not line or line == '\r':
                    continue
                x_value, y_value = line.split()
                datapoints.append(models.Datapoint(
                    created_by=request.user, dataseries=dataseries))
                add_numerical_value(numerical_values, errors, x_value,
                                    is_secondary=True)
                add_numerical_value(numerical_values, errors, y_value)
        else:
            for value in form.cleaned_data[
                    'series_datapoints_' + str(i_series)].split():
                if value.startswith('#') or not value:
                    continue
                datapoints.append(models.Datapoint(
                    created_by=request.user, dataseries=dataseries))
                add_numerical_value(numerical_values, errors, value)
        # Fixed properties
        counter = 0
        for key in form.cleaned_data:
            if key.startswith('fixed_property_' + str(i_series) + '_'):
                suffix = key.split('fixed_property_')[1]
                fixed_value = models.NumericalValueFixed(
                    created_by=request.user,
                    dataseries=dataseries,
                    counter=counter)
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
    add_datapoint_ids(numerical_values,
                      int(len(numerical_values)/len(datapoints)))
    models.NumericalValue.objects.bulk_create(numerical_values)
    models.Error.objects.bulk_create(generate_numerical_value_ids(errors))
    add_datapoint_ids(symbols, int(len(symbols)/len(datapoints)))
    models.Symbol.objects.bulk_create(symbols)
    # If all went well, let the user know how much data was
    # successfully added
    n_data_points = 0
    for series in dataset.dataseries_set.all():
        n_data_points += series.datapoint_set.all().count()
    if n_data_points > 0:
        messages.success(request,
                         f'{n_data_points} new data point'
                         f'{"s" if n_data_points != 1 else ""} '
                         'successfully added to the database!')
    else:
        messages.success(request,
                         'New data successfully added to the database!')
    return redirect(reverse('materials:add_data'))


@dataset_author_check
def toggle_dataset_visibility(request, system_pk, dataset_pk, return_path):
    dataset = models.Dataset.objects.get(pk=dataset_pk)
    dataset.visible = not dataset.visible
    dataset.save()
    return redirect(return_path)


@dataset_author_check
def toggle_dataset_plotted(request, system_pk, dataset_pk, return_path):
    dataset = models.Dataset.objects.get(pk=dataset_pk)
    dataset.plotted = not dataset.plotted
    dataset.save()
    return redirect(return_path)


def download_dataset_files(request, pk):
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


def download_input_files(request, pk):
    loc = os.path.join(settings.MEDIA_ROOT, f'input_files/dataset_{pk}')
    files = os.listdir(loc)
    file_full_paths = [os.path.join(loc, f) for f in files]
    zip_dir = 'files'
    zip_filename = 'files.zip'
    in_memory_object = io.BytesIO()
    zf = zipfile.ZipFile(in_memory_object, 'w')
    for file_path, file_name in zip(file_full_paths, files):
        zf.write(file_path, os.path.join(zip_dir, file_name))
    zf.close()
    response = HttpResponse(in_memory_object.getvalue(),
                            content_type='application/x-zip-compressed')
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'
    return response


@dataset_author_check
def delete_dataset_and_files(request, system_pk, dataset_pk, return_path):
    """Delete current data set and all associated files."""
    dataset = models.Dataset.objects.get(pk=dataset_pk)
    dataset.delete()
    return redirect(return_path)


class SystemDetailView(generic.DetailView):
    model = models.System


class ReferenceDetailView(generic.DetailView):
    model = models.Reference


class SpecificSystemView(generic.TemplateView):
    template_name = 'materials/system_specific.html'

    def get(self, request, pk, pk_aa, pk_syn, pk_ee, pk_bs):
        system = models.System.objects.get(pk=pk)
        exciton_emission = system.excitonemission_set.get(pk=pk_ee)
        if system.synthesismethodold_set.count() > 0:
            synthesis = system.synthesismethodold_set.get(pk=pk_syn)
        else:
            synthesis = None
        if system.atomicpositions_set.count() > 0:
            atomic_positions = system.atomicpositions_set.get(pk=pk_aa)
        else:
            atomic_positions = None
        if system.bandstructure_set.count() > 0:
            band_structure = system.bandstructure_set.get(pk=pk_bs)
        else:
            band_structure = None
        args = {
            'system': system,
            'atomic_positions': atomic_positions,
            'synthesis': synthesis,
            'exciton_emission': exciton_emission,
            'band_structure': band_structure
        }
        return render(request, self.template_name, args)


class SystemUpdateView(generic.UpdateView):
    model = models.System
    template_name = 'materials/system_update_form.html'
    form_class = forms.AddSystem
    success_url = '/materials/{pk}'


class BandStructureUpdateView(generic.UpdateView):
    model = models.BandStructure
    template_name = 'materials/update_band_structure.html'
    form_class = forms.AddBandStructure

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/band_structure' % str(pk)


class BandStructureDeleteView(generic.DeleteView):
    model = models.BandStructure
    template_name = 'materials/delete_band_structure.html'
    form_class = forms.AddBandStructure

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/band_structure' % str(pk)


def dataset_image(request, pk):
    """Return a png image of the data set."""
    from matplotlib import pyplot
    dataset = models.Dataset.objects.get(pk=pk)
    dataseries = dataset.dataseries_set.first()
    datapoints = dataseries.datapoint_set.all()
    x_values = numpy.zeros(len(datapoints))
    y_values = numpy.zeros(len(datapoints))
    for i_dp, datapoint in enumerate(datapoints):
        x_value = datapoint.numericalvalue_set.get(
            qualifier=models.NumericalValue.SECONDARY)
        x_values[i_dp] = x_value.value
        y_value = datapoint.numericalvalue_set.get(
            qualifier=models.NumericalValue.PRIMARY)
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


def dataset_data(request, pk):
    """Return the data set as a text file."""
    dataset = models.Dataset.objects.get(pk=pk)
    dataseries = dataset.dataseries_set.first()
    text = ''
    x_value = ''
    y_value = ''
    for datapoint in dataseries.datapoint_set.all():
        for value in datapoint.numericalvalue_set.all():
            if value.qualifier == models.NumericalValue.SECONDARY:
                x_value = value.value
            elif value.qualifier == models.NumericalValue.PRIMARY:
                y_value = value.value
        text += f'{x_value} {y_value}\n'
    return HttpResponse(text, content_type='text/plain')


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
            'kind': 'figure' if dataset.plotted else 'table',
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
    return JsonResponse(data)


def autofill_input_data(request):
    """Process an AJAX request to autofill the data textareas."""
    content = UploadedFile(request.FILES['file']).read().decode('utf-8')
    output = io.StringIO()
    for line in content.split('\n'):
        output.write(line)
        output.write('\n')
    return HttpResponse(output.getvalue())


class PropertyAllEntriesView(generic.ListView):
    """Display all data sets for a given property and system."""
    template_name = 'materials/property_all_entries.html'

    def get_queryset(self, **kwargs):
        return models.Dataset.objects.filter(
            system__pk=self.kwargs['system_pk']).filter(
                primary_property__pk=self.kwargs['prop_pk'])


def data_for_chart(request, pk):
    dataset = models.Dataset.objects.get(pk=pk)
    response = {'primary-property': dataset.primary_property.name,
                'primary-unit': dataset.primary_unit.label,
                'secondary-property': dataset.secondary_property.name,
                'secondary-unit': dataset.secondary_unit.label,
                'data': []}
    dataseries = dataset.dataseries_set.first()
    response['series-label'] = dataseries.label
    values = models.NumericalValue.objects.filter(
        datapoint__dataseries=dataseries).order_by(
            'datapoint_id', 'qualifier').values_list('value', flat=True)
    for i in range(0, len(values), 2):
        response['data'].append({'y': values[i], 'x': values[i+1]})
    return JsonResponse(response)


def get_series_values(request, pk):
    """Return the numerical values of a series as a formatted list."""
    values = models.NumericalValue.objects.filter(
        datapoint__dataseries__pk=pk).select_related(
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
    """Get atomic coordinates from the lattice parameter list.

    The first six entries of the "lattice parameter" property are the
    lattice constants and angles. These need to be skipped when
    fetching for the atomic coordinates.

    """
    series = models.Dataseries.objects.get(pk=pk)
    vectors = models.NumericalValue.objects.filter(
        datapoint__dataseries=series).filter(
           datapoint__symbol__isnull=True).order_by(
               'datapoint_id', 'counter').values_list('value', flat=True)
    data = {'vectors':
            [list(vectors[:3]), list(vectors[3:6]), list(vectors[6:9])]}
    # Here counter=1 filters out the first six entries
    symbols = models.Symbol.objects.filter(
        datapoint__dataseries=series).filter(counter=1).order_by(
            'datapoint_id').values_list('value', flat=True)
    coords = models.NumericalValue.objects.filter(
        datapoint__dataseries=series).filter(
            datapoint__symbol__counter=1).select_related('error').order_by(
                'counter', 'datapoint_id')
    data['coordinates'] = []
    N = int(len(coords)/3)
    for symbol, coord_x, coord_y, coord_z in zip(
            symbols, coords[:N], coords[N:2*N], coords[2*N:3*N]):
        data['coordinates'].append((symbol,
                                    coord_x.formatted(),
                                    coord_y.formatted(),
                                    coord_z.formatted()))
    return JsonResponse(data)


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
