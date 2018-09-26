# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import generic
from django.db.models import Q
from django.forms import formset_factory

from materials.forms import (
    System, SearchForm, AddAtomicPositions, AddPublication, AddAuthor, AddTag,
    AddSystem, AddExcitonEmission, AddSynthesisMethod, AddBandStructure,
    AddMaterialProperty)

from materials.models import (
    ExcitonEmission, SynthesisMethod, BandStructure, MaterialProperty,
    AtomicPositions, Publication, Author, Tag)
from accounts.models import UserProfile

from mainproject.settings.base import MEDIA_ROOT
from .rangeparser import parserange

import os
import zipfile
from io import BytesIO
from functools import reduce
import operator

dictionary = {
    'atomic_positions': AtomicPositions,
    'exciton_emission': ExcitonEmission,
    'synthesis': SynthesisMethod,
    'band_structure': BandStructure,
    'material_prop': MaterialProperty
}


def data_dl(request, type, id, bandgap=False):
    """Download a specific entry type"""
    # Create the HttpResponse object with the text/plain header.
    response = HttpResponse(content_type='text/fhi-aims')
    if type == 'band_gap':
        type = 'band_structure'
        bandgap = True
    # need to find a way to change type of file based on the property
    # being described file_ext = 'txt'

    def write_headers():
        if type not in ['all_atomic_positions']:
            if not bandgap:
                response.write(str('#HybriD³ Materials Database\n'))
            response.write(str('\n#System: '))
            response.write(str(p_obj.compound_name))
        response.write(str('\n#Temperature: '))
        response.write(str(obj.temperature + ' K'))
        response.write(str('\n#Phase: '))
        response.write(str(obj.phase.phase))
        authors = obj.publication.author_set.all()
        response.write(str('\n#Authors ('+str(authors.count())+'): '))
        for author in authors:
            response.write('\n    ')
            response.write(author.first_name + ' ')
            response.write(author.last_name)
            response.write(', ' + author.institution)
        response.write(str('\n#Journal: '))
        response.write(str(obj.publication.journal))
        response.write(str('\n#Source: '))
        if obj.publication.doi_isbn:
            response.write(str(obj.publication.doi_isbn))
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

    if type == 'atomic_positions':
        obj = dictionary[type].objects.get(id=id)
        p_obj = System.objects.get(atomicpositions=obj)
        write_headers()
        write_a_pos()
        fileloc = (MEDIA_ROOT + '/uploads/%s_%s_%s_apos.in' %
                   (obj.phase, p_obj.organic, p_obj.inorganic))
        if(os.path.isfile(fileloc)):
            with open(fileloc, encoding='utf-8', mode='r+') as f:
                lines = f.read().splitlines()
                for line in lines:
                    response.write(line + '\n')
        else:
            response.write('#-Atomic Positions input file not available-')
        # return redirect(MEDIA_URL + 'uploads/%s_%s_%s.in' % \
        #                 (obj.phase, p_obj.organic, p_obj.inorganic))
        response['Content-Disposition'] = (
            'attachment; filename=%s_%s_%s_%s.in' % (obj.phase, p_obj.organic,
                                                     p_obj.inorganic, type))
    elif type == 'all_atomic_positions':  # all the a_pos entries
        p_obj = System.objects.get(id=id)
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
    elif type == 'exciton_emission':
        obj = dictionary[type].objects.get(id=id)
        p_obj = System.objects.get(excitonemission=obj)
        file_name_prefix = '%s_%s_%s_pl' % (obj.phase, p_obj.organic,
                                            p_obj.inorganic)
        # response = HttpResponse(content_type='text/csv')
        # response['Content-Disposition'] = \
        #     'attachment; filename=%s_%s_%s_%s.csv' % \
        #     (obj.phase, p_obj.organic, p_obj.inorganic, type)
        # writer = csv.writer(response)
        # with open(filename, encoding='utf-8', mode='r+') as csvfile:
        #     plots =  csv.reader(csvfile, delimiter=',')
        #     for row in plots:
        #         response.write(row)
        dir_in_str = os.path.join(MEDIA_ROOT, 'uploads')
        # directory = os.fsencode(dir_in_str)
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
            for author in obj.publication.author_set.all():
                meta_file.write('\n    ')
                meta_file.write(author.first_name + ' ')
                meta_file.write(author.last_name)
                meta_file.write(', ' + author.institution)
            meta_file.write(str('\n#Journal: '))
            meta_file.write(str(obj.publication.journal))
            meta_file.write(str('\n#Source: '))
            meta_file.write(str(obj.publication.doi_isbn))
            meta_file.write(str('\n#Exciton Emission Peak: '))
            meta_file.write(str(obj.excitonemission))
        pl_file_csv = os.path.join(dir_in_str, file_name_prefix + '.csv')
        pl_file_html = os.path.join(dir_in_str, file_name_prefix + '.html')
        filenames = []
        filenames.append(meta_filepath)
        filenames.append(pl_file_csv)
        filenames.append(pl_file_html)
        # print('Filenames')
        print(filenames)

        zip_dir = file_name_prefix
        zip_filename = '%s.zip' % zip_dir
        # change response type and content deposition type
        string = BytesIO()

        zf = zipfile.ZipFile(string, 'w')

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_dir, fname)

            # Add file, at correct path
            print('Fpath')
            print(fpath)
            print('Zip Path')
            print(zip_path)
            zf.write(fpath, zip_path)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(string.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           zip_filename)
    elif type == 'synthesis':
        obj = dictionary[type].objects.get(id=id)
        p_obj = System.objects.get(synthesismethod=obj)
        file_name_prefix = '%s_%s_%s_syn' % (obj.phase, p_obj.organic,
                                             p_obj.inorganic)
        meta_filename = file_name_prefix + '.txt'
        # meta_filepath = os.path.join(dir_in_str, meta_filename)
        response = HttpResponse(content_type='text/plain')
        # with open(meta_filepath, encoding='utf-8', mode='w+') as meta_file:
        response.write(str('#HybriD³ Materials Database\n'))
        response.write(str('\n#System: '))
        response.write(str(p_obj.compound_name))
        response.write(str('\n#Temperature: '))
        response.write(str(obj.temperature))
        response.write(str('\n#Phase: '))
        response.write(str(obj.phase.phase))
        response.write(str('\n#Authors: '))
        for author in obj.publication.author_set.all():
            response.write('\n    ')
            response.write(author.first_name + ' ')
            response.write(author.last_name)
            response.write(', ' + author.institution)
        response.write(str('\n#Journal: '))
        response.write(str(obj.publication.journal))
        response.write(str('\n#Source: '))
        response.write(str(obj.publication.doi_isbn))
        if obj.synthesis_method:
            response.write(str('\n#Synthesis Method: '))
            response.write(str(obj.synthesis_method))
        print('syn method', obj.synthesis_method)
        if obj.starting_materials:
            response.write(str('\n#Starting Materials: '))
            response.write(str(obj.starting_materials))
        if obj.remarks:
            response.write(str('\n#Remarks: '))
            response.write(str(obj.remarks))
        if obj.product:
            response.write(str('\n#Product: '))
            response.write(str(obj.product))
        # upload_file_txt = os.path.join(dir_in_str, file_name_prefix + '.txt')
        # filenames = []
        # filenames.append(meta_filepath)
        # filenames.append(upload_file_txt)
        # # print('Filenames')
        # print(filenames)

        # zip_dir = file_name_prefix
        # zip_filename = '%s.zip' % zip_dir
        # # change response type and content deposition type
        # string = BytesIO()
        #
        # zf = zipfile.ZipFile(string, 'w')
        #
        # for fpath in filenames:
        #     # Calculate path for file in zip
        #     fdir, fname = os.path.split(fpath)
        #     zip_path = os.path.join(zip_dir, fname)
        #
        #     # Add file, at correct path
        #     print('Fpath')
        #     print(fpath)
        #     print('Zip Path')
        #     print(zip_path)
        #     zf.write(fpath, zip_path)
        # # Must close zip for all contents to be written
        # zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response.encoding = 'utf-8'
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           (meta_filename))
    elif type == 'band_structure' and bandgap:
        obj = dictionary[type].objects.get(id=id)
        p_obj = System.objects.get(bandstructure=obj)
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
    elif type == 'band_structure':
        obj = dictionary[type].objects.get(id=id)
        p_obj = System.objects.get(bandstructure=obj)
        file_name_prefix = '%s_%s_%s_%s_bs' % (obj.phase, p_obj.organic,
                                               p_obj.inorganic, obj.pk)
        # write_headers()
        dir_in_str = obj.folder_location
        compound_name = dir_in_str.split('/')[-1]
        print(dir_in_str)
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
            for author in obj.publication.author_set.all():
                meta_file.write('\n    ')
                meta_file.write(author.first_name + ' ')
                meta_file.write(author.last_name)
                meta_file.write(', ' + author.institution)
            meta_file.write('\n#Journal: ')
            meta_file.write(str(obj.publication.journal))
            meta_file.write('\n#Source: ')
            meta_file.write(str(obj.publication.doi_isbn))
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
                # response.write('\n')
                # response.write(full_filename)
        print('Filenames')
        print(filenames)

        zip_dir = compound_name
        zip_filename = '%s.zip' % zip_dir
        # change response type and content deposition type
        string = BytesIO()

        zf = zipfile.ZipFile(string, 'w')

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_dir, fname)

            # Add file, at correct path
            print('Fpath')
            print(fpath)
            print('Zip Path')
            print(zip_path)
            zf.write(fpath, zip_path)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(string.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = ('attachment; filename=%s' %
                                           zip_filename)
    # might need to work on a more efficient method
    return response


def all_a_pos(request, id):
    """Defines views for each specific entry type."""
    def sortEntries(entry):
        """Sort by temperature, but temperature is a charFields"""
        try:
            return int(entry.temperature)
        except:
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
    obj = System.objects.get(id=id)
    compound_name = System.objects.get(id=id).compound_name
    obj = obj.atomicpositions_set.all()
    obj = sorted(obj, key=sortEntries)
    return render(request, template_name,
                  {'object': obj, 'compound_name': compound_name, 'key': id})


def all_entries(request, id, type):
    template_name = 'materials/all_%ss.html' % type
    # This has no effect and will be overwritten
    obj = System.objects.get(id=id)
    compound_name = System.objects.get(id=id).compound_name
    obj = dictionary[type].objects.filter(system__id=id)
    return render(request, template_name,
                  {'object': obj, 'compound_name': compound_name,
                   'data_type': type, 'key': id})


def getAuthorSearchResult(search_text):
    keyWords = search_text.split()
    print(keyWords)
    results = System.objects.\
        filter(reduce(operator.or_, (
            Q(atomicpositions__publication__author__last_name__icontains=x) for
            x in keyWords)) | reduce(operator.or_, (
                Q(synthesismethod__publication__author__last_name__icontains=x)
                for x in keyWords)) | reduce(operator.or_, (
                        Q(excitonemission__publication__author__last_name__icontains=x)
                        for x in keyWords)) | reduce(operator.or_, (
                                Q(bandstructure__publication__author__last_name__icontains=x)
                                for x in keyWords))
         ).distinct()
    print('**************************RESULTS******************************')
    print(results)
    print('***************************************************************')
    return results


def search_result(search_term, search_text):
    if search_term == 'formula':
        return System.objects.filter(
            Q(formula__icontains=search_text) |
            Q(group__icontains=search_text) |
            Q(compound_name__icontains=search_text)).order_by('formula')
    elif search_term == 'organic':
        return System.objects.filter(
            organic__icontains=search_text).order_by('organic')
    elif search_term == 'inorganic':
        return System.objects.filter(
            inorganic__icontains=search_text).order_by('inorganic')
    elif search_term == 'author':
        return getAuthorSearchResult(search_text)
    else:
        raise KeyError('Invalid search term.')


class SearchFormView(generic.TemplateView):
    """Search for system page"""
    template_name = 'materials/materials_search.html'
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
        template_name = 'materials/materials_search_results.html'
        form = SearchForm(request.POST)
        search_text = ''
        # default search_term
        search_term = 'formula'
        if form.is_valid():
            print(form.cleaned_data)
            search_text = form.cleaned_data['search_text']
            search_term = request.POST.get('search_term')
            systems_info = []
            if search_term == 'exciton_emission':
                searchrange = parserange(search_text)
                if len(searchrange) > 0:
                    if searchrange[0] == 'bidirectional':
                        if searchrange[3] == '>=':
                            systems = ExcitonEmission.objects.filter(
                                exciton_emission__gte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[3] == '>':
                            systems = ExcitonEmission.objects.filter(
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
                            systems = ExcitonEmission.objects.filter(
                                exciton_emission__gte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '>':
                            systems = ExcitonEmission.objects.filter(
                                exciton_emission__gt=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '<=':
                            systems = ExcitonEmission.objects.filter(
                                exciton_emission__lte=searchrange[1]).order_by(
                                    '-exciton_emission')
                        elif searchrange[2] == '<':
                            systems = ExcitonEmission.objects.filter(
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
                        if ee.system.synthesismethod_set.count() > 0:
                            system_info['syn_pk'] = (
                                ee.system.synthesismethod_set.first().pk)
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
                    print(systems_info)
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
    except:  # just in case
        return form


class AddAPosView(generic.TemplateView):
    template_name = 'materials/add_a_pos.html'

    def get(self, request):
        search_form = SearchForm()
        a_pos_form = AddAtomicPositions()
        return render(request, self.template_name, {
            'search_form': search_form,
            'a_pos_form': a_pos_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': True
        })

    def post(self, request):
        form = AddAtomicPositions(request.POST, request.FILES)
        if form.is_valid():
            print('a_pos form is valid')
            apos_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            syn_pk = request.POST.get('synthesis-methods')
            print('synthesis method pk is: ' + syn_pk)
            try:
                apos_form.synthesis_method = SynthesisMethod.objects.get(
                    pk=int(syn_pk))
            except:
                # no synthesis method was chosen (or maybe an error occurred)
                pass
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                apos_form.publication = Publication.objects.get(pk=pub_pk)
                apos_form.system = System.objects.get(pk=sys_pk)
                # text += 'Publication and System obtained, '
                if request.user.is_authenticated:
                    apos_form.contributor = UserProfile.objects.get(
                        user=request.user)
                    # print apos_form.contributor
                    text = 'Save success!'
                    feedback = 'success'
                    apos_form = makeCorrections(apos_form)
                    apos_form.save()
                else:
                    text = 'Failed to submit, please login and try again.'
                    feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'

        args = {'feedback': feedback, 'text': text}

        return JsonResponse(args)


class AddPubView(generic.TemplateView):
    template_name = 'materials/add_publication.html'

    def get(self, request):
        search_form = SearchForm()
        pub_form = AddPublication()
        return render(request, self.template_name, {
            'search_form': search_form,
            'pub_form': pub_form,
            'initial_state': True
        })

    def post(self, request):
        # check if is ajax
        # if request.is_ajax():
        #     print 'is ajax'
        # else:
        #     print 'not ajax'
        # search_form = SearchForm()  # dead code?
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
        pub_form = AddPublication(request.POST)
        if pub_form.is_valid():
            form = pub_form.save(commit=False)
            doi_isbn = pub_form.cleaned_data['doi_isbn']
            # check if doi_isbn is unique/valid, except when field is empty
            if len(doi_isbn) == 0 or len(
                    Publication.objects.filter(doi_isbn=doi_isbn)) == 0:
                form.author_count = author_count
                form.save()
                newPub = form
                text = 'Save success!'
                feedback = 'success'
            else:
                text = 'Failed to submit, publication is already in database.'
                feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'
        if feedback == 'failure':
            return JsonResponse({'feedback': feedback, 'text': text})
        # create and save new author objects, linking them to the
        # saved publication
        for i in range(author_count):  # for each author
            data = {}
            data['first_name'] = authors_info['form-%d-first_name' % i]
            data['last_name'] = authors_info['form-%d-last_name' % i]
            data['institution'] = authors_info['form-%d-institution' % i]
            preexistingAuthors = (
                Author.objects.filter(
                    first_name__iexact=data['first_name']).filter(
                        last_name__iexact=data['last_name']).filter(
                            institution__iexact=data['institution']))
            print(preexistingAuthors)
            if preexistingAuthors.count() > 0:
                # use the prexisting author object
                print('This author is already in the database.',
                      preexistingAuthors)
                preexistingAuthors[0].publication.add(newPub)
            else:  # this is a new author, so create a new object
                print('This is a new author.', data)
                author_form = AddAuthor(data)
                if(not author_form.is_valid()):
                    text = ('Failed to submit, author not valid. '
                            'Please fix the errors, and try again.')
                    feedback = 'failure'
                    break
                else:  # author_form is valid
                    form = author_form.save()
                    form.publication.add(newPub)
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
    from itertools import chain

    def post(self, request):
        search_form = SearchForm(request.POST)
        search_text = ''
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
            print(search_text)
            author_search = (
                Publication.objects.filter(
                    Q(author__first_name__icontains=search_text) |
                    Q(author__last_name__icontains=search_text) |
                    Q(author__institution__icontains=search_text)).distinct())
            print('authors:', author_search)
            if len(author_search) > 0:
                search_result = author_search
            else:
                search_result = Publication.objects.filter(
                    Q(title__icontains=search_text) |
                    Q(journal__icontains=search_text)
                )
        return render(request, self.template_name,
                      {'search_result': search_result})


class AddAuthorsToPublicationView(generic.TemplateView):
    template_name = 'materials/add_authors_to_publication.html'

    def post(self, request):
        author_count = request.POST['author_count']
        # variable number of author forms
        author_formset = formset_factory(AddAuthor, extra=int(author_count))
        return render(request, self.template_name,
                      {'entered_author_count': author_count,
                       'author_formset': author_formset})


class SearchAuthorView(generic.TemplateView):
    """This is for add publication page"""
    # template_name = 'materials/add_publication.html'
    template_name = 'materials/dropdown_list_author.html'

    def post(self, request):
        search_form = SearchForm(request.POST)
        # pub_form = AddPublication()
        search_text = ''
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
            search_result = Author.objects.filter(
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


class AddAuthorView(generic.TemplateView):
    template_name = 'materials/add_author.html'

    def get(self, request):
        # search_form = SearchForm()
        input_form = AddAuthor()
        # pub_form = AddPublication()
        print(input_form)
        return render(request, self.template_name, {
            'input_form': input_form,
        })

    def post(self, request):
        # search_form = SearchForm()
        input_form = AddAuthor(request.POST)
        if input_form.is_valid():
            first_name = input_form.cleaned_data['first_name'].lower()
            last_name = input_form.cleaned_data['last_name'].lower()
            institution = input_form.cleaned_data['institution'].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                Author.objects.filter(first_name__iexact=first_name)
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


class AddTagView(generic.TemplateView):
    template_name = 'materials/add_tag.html'

    def get(self, request):
        input_form = AddTag()
        return render(request, self.template_name, {
            'input_form': input_form,
        })

    def post(self, request):
        # search_form = SearchForm()
        input_form = AddTag(request.POST)
        if input_form.is_valid():
            tag = input_form.cleaned_data['tag'].lower()
            q_set_len = len(
                Tag.objects.filter(tag__iexact=tag)
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
        form = SearchForm(request.POST)
        related_synthesis = (request.POST['related_synthesis'] == 'True')
        search_text = ''
        if form.is_valid():
            search_text = form.cleaned_data['search_text']

        search_result = System.objects.filter(
            Q(compound_name__icontains=search_text) |
            Q(group__icontains=search_text) |
            Q(formula__icontains=search_text)
        )
        # ajax version
        return render(request, self.template_name,
                      {'search_result': search_result,
                       'related_synthesis': related_synthesis})


class AddSystemView(generic.TemplateView):
    template_name = 'materials/add_system.html'

    def get(self, request):
        form = AddSystem()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddSystem(request.POST)
        if form.is_valid():
            compound_name = form.cleaned_data['compound_name'].lower()
            formula = form.cleaned_data['formula'].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                System.objects.filter(
                    Q(compound_name__iexact=compound_name) |
                    Q(formula__iexact=formula)
                )
            )
            print(q_set_len)
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
        print(args)
        return JsonResponse(args)


class AddPhase(generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = AddPhase()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddPhase(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']
        args = {'form': form, 'text': text}
        return render(request, self.template_name, args)


class AddTemperature(generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = AddTemperature()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddTemperature(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']

        args = {'form': form, 'text': text}

        return render(request, self.template_name, args)


class AddExcitonEmissionView(generic.TemplateView):
    template_name = 'materials/add_exciton_emission.html'

    def get(self, request):
        search_form = SearchForm()
        exciton_emission_form = AddExcitonEmission()
        return render(request, self.template_name, {
            'search_form': search_form,
            'exciton_emission_form': exciton_emission_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': True
        })

    def post(self, request):
        form = AddExcitonEmission(request.POST, request.FILES)
        if form.is_valid():
            print('form is valid')
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            # print 'file: ', request.FILES.get('pl_file')
            syn_pk = request.POST.get('synthesis-methods')
            print('synthesis method pk is: ' + syn_pk)
            try:
                new_form.synthesis_method = SynthesisMethod.objects.get(
                    pk=int(syn_pk))
            except:
                # no synthesis method was chosen (or maybe an error occurred)
                pass
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                # text += 'Publication and System obtained, '
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(
                        user=request.user)
                    # print apos_form.contributor
                    text = 'Save success!'
                    feedback = 'success'
                    ee_model = new_form.save()
                    print(ee_model)
                else:
                    text = 'Failed to submit, please login and try again.'
                    feedback = 'failure'
        else:
            text = 'Failed to submit, please fix the errors, and try again.'
            feedback = 'failure'

        args = {'feedback': feedback, 'text': text}
        print(args)
        return JsonResponse(args)


class AddSynthesisMethodView(generic.TemplateView):
    template_name = 'materials/add_synthesis.html'

    def get(self, request):
        search_form = SearchForm()
        synthesis_form = AddSynthesisMethod()
        return render(request, self.template_name, {
            'search_form': search_form,
            'synthesis_form': synthesis_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': False
        })

    def post(self, request):
        form = AddSynthesisMethod(request.POST, request.FILES)
        if form.is_valid():
            print('form is valid')
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            print('system pk is: ' + sys_pk)
            # text = ''
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                # text += 'Publication and System obtained, '
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(
                        user=request.user)
                    # print apos_form.contributor
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


class AddBandStructureView(generic.TemplateView):
    template_name = 'materials/add_band_structure.html'

    def get(self, request):
        search_form = SearchForm()
        band_structure_form = AddBandStructure()
        return render(request, self.template_name, {
            'search_form': search_form,
            'band_structure_form': band_structure_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': True
        })

    def post(self, request):
        form = AddBandStructure(request.POST, request.FILES)
        if form.is_valid():
            print('Form is valid')
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            syn_pk = request.POST.get('synthesis-methods')
            print('synthesis method pk is: ' + syn_pk)
            try:
                new_form.synthesis_method = SynthesisMethod.objects.get(
                    pk=int(syn_pk))
            except:
                # no synthesis method was chosen (or maybe an error occurred)
                pass
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                # text += 'Settings ready. '
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(
                        user=request.user)
                    # save so a pk can be created for use in the
                    # folder location
                    new_form.save()
                    print('PK:', new_form.pk)
                    bs_folder_loc = (MEDIA_ROOT + '/uploads/%s_%s_%s_%s_bs' %
                                     (new_form.phase, new_form.system.organic,
                                      new_form.system.inorganic, new_form.pk))
                    new_form.folder_location = bs_folder_loc
                    try:
                        os.mkdir(bs_folder_loc)
                    except:
                        pass
                    band_files = request.FILES.getlist('band_structure_files')
                    control_file = request.FILES.get('control_in_file')
                    geometry_file = request.FILES.get('geometry_in_file')
                    band_files.append(control_file)
                    band_files.append(geometry_file)
                    for f in band_files:
                        filename = f.name
                        print('filename is: {}', (f.name))
                        full_filename = os.path.join(bs_folder_loc, filename)
                        print('file writen to: {}', (full_filename))
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


class AddMaterialPropertyView(generic.TemplateView):
    template_name = 'materials/add_material_property.html'

    def get(self, request):
        search_form = SearchForm()
        material_property_form = AddMaterialProperty()
        return render(request, self.template_name, {
            'search_form': search_form,
            'material_property_form': material_property_form,
            'initial_state': True,
            # determines whether this field appears on the form
            'related_synthesis': False
        })

    def post(self, request):
        form = AddMaterialProperty(request.POST)
        if form.is_valid():
            print('form is valid')
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            print('system pk is: ' + sys_pk)
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(
                        user=request.user)
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


class AddBondLength(generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = AddBondLength()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddBondLength(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']

        args = {'form': form, 'text': text}

        return render(request, self.template_name, args)


class AddDataView(generic.TemplateView):
    template_name = 'materials/add_data.html'

    def get(self, request):
        return render(request, self.template_name)


class SystemView(generic.DetailView):
    template_name = 'materials/materials_system.html'
    model = System


class SpecificSystemView(generic.TemplateView):
    template_name = 'materials/materials_system_specific.html'

    def get(self, request, pk, pk_aa, pk_syn, pk_ee, pk_bs):
        system = System.objects.get(pk=pk)
        exciton_emission = system.excitonemission_set.get(pk=pk_ee)
        if system.synthesismethod_set.count() > 0:
            synthesis = system.synthesismethod_set.get(pk=pk_syn)
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
        print(args)
        return render(request, self.template_name, args)


class SystemUpdateView(generic.UpdateView):
    model = System
    template_name = 'materials/system_update_form.html'
    form_class = AddSystem
    success_url = '/materials/{id}'


class AtomicPositionsUpdateView(generic.UpdateView):
    model = AtomicPositions
    template_name = 'materials/update_a_pos.html'
    form_class = AddAtomicPositions

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/all-a-pos' % str(pk)


class AtomicPositionsDeleteView(generic.DeleteView):
    model = AtomicPositions
    template_name = 'materials/delete_a_pos.html'
    form_class = AddAtomicPositions

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/all-a-pos' % str(pk)


class SynthesisMethodUpdateView(generic.UpdateView):
    model = SynthesisMethod
    template_name = 'materials/update_synthesis.html'
    form_class = AddSynthesisMethod

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/synthesis' % str(pk)


class SynthesisMethodDeleteView(generic.DeleteView):
    model = SynthesisMethod
    template_name = 'materials/delete_synthesis.html'
    form_class = AddSynthesisMethod

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/synthesis' % str(pk)


class ExcitonEmissionUpdateView(generic.UpdateView):
    model = ExcitonEmission
    template_name = 'materials/update_exciton_emission.html'
    form_class = AddExcitonEmission

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/exciton_emission' % str(pk)


class ExcitonEmissionDeleteView(generic.DeleteView):
    model = ExcitonEmission
    template_name = 'materials/delete_exciton_emission.html'
    form_class = AddExcitonEmission

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/exciton_emission' % str(pk)


class BandStructureUpdateView(generic.UpdateView):
    model = BandStructure
    template_name = 'materials/update_band_structure.html'
    form_class = AddBandStructure

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/band_structure' % str(pk)


class BandStructureDeleteView(generic.DeleteView):
    model = BandStructure
    template_name = 'materials/delete_band_structure.html'
    form_class = AddBandStructure

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/band_structure' % str(pk)


class PropertyUpdateView(generic.UpdateView):
    model = MaterialProperty
    template_name = 'materials/update_material_property.html'
    form_class = AddMaterialProperty

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/material_prop' % str(pk)


class PropertyDeleteView(generic.DeleteView):
    model = MaterialProperty
    template_name = 'materials/delete_material_property.html'
    form_class = AddMaterialProperty

    def get_success_url(self):
        pk = self.object.system.pk
        return '/materials/%s/material_prop' % str(pk)
