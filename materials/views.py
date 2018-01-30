# -*- coding: utf-8 -*-

from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from django.db.models import Q

from materials.forms import *

from .models import System, AtomicPositions, ExcitonEmission, BandGap, BandStructure
from accounts.models import UserProfile

# Create your views here.
from myproject.settings.prod import MEDIA_ROOT, MEDIA_URL
import csv
import os
from .rangeparser import parserange
from .plotting.pl_plotting import plotpl
from .plotting.bs_plotting import plotbs

dictionary = {
"exciton_emission": ExcitonEmission,
"band_gap": BandGap,
"band_structure": BandStructure
}

# Download a specific entry type
def data_dl(request, type, id):
    # Create the HttpResponse object with the text/plain header.
    response = HttpResponse(content_type='text/plain')
    dictionary['atomic_positions'] = AtomicPositions
    obj = dictionary[type].objects.get(id=id)
    # need to find a way to change type of file based on the property being described
    # file_ext = "txt"

    def write_headers():
        response.write("#Hybrid3 Materials Database\n\n")
        response.write("#System: ")
        response.write(p_obj.compound_name)
        response.write("\n#Temperature: ")
        response.write(obj.temperature)
        response.write("\n#Phase: ")
        response.write(obj.phase)
        response.write("\n#Author: ")
        response.write(obj.publication.author)
        response.write("\n#Journal: ")
        response.write(obj.publication.journal)
        response.write("\n#Source: ")
        if obj.publication.doi_isbn:
            response.write(obj.publication.doi_isbn)
        else:
            response.write("N/A")

    if type == "atomic_positions":
        p_obj = System.objects.get(atomicpositions=obj)
        write_headers()
        response.write("\n#a: ")
        response.write(obj.a)
        response.write("\n#b: ")
        response.write(obj.b)
        response.write("\n#c: ")
        response.write(obj.c)
        response.write("\n#&alpha;: ")
        response.write(obj.alpha)
        response.write("\n#&beta;: ")
        response.write(obj.beta)
        response.write("\n#&gamma;: ")
        response.write(obj.gamma)
        response.write("\n\n")
        fileloc = MEDIA_ROOT + '/uploads/%s_%s_%s.in' % (obj.phase, p_obj.organic, p_obj.inorganic)
        if(os.path.isfile(fileloc)):
            with open(fileloc) as f:
                lines = f.read().splitlines()
                for line in lines:
                    response.write(line + "\n")
            # file_ext = "in"
        else:
            response.write("#-Atomic Positions input file not available-")
        # return redirect(MEDIA_URL + 'uploads/%s_%s_%s.in' % (obj.phase, p_obj.organic, p_obj.inorganic))
    elif type == "exciton_emission":
        p_obj = System.objects.get(excitonemission=obj)
        write_headers()
        response.write("\n#Exciton Emission Peak: ")
        response.write(obj.excitonemission)
    elif type == "band_gap":
        p_obj = System.objects.get(bandgap=obj)
        write_headers()
        response.write("\n#Band Gap: ")
        response.write(obj.bandgap)
    elif type == "band_structure":
        p_obj = System.objects.get(bandstructure=obj)
        write_headers()
        response.write("\n#Band Structure: ")
        response.write(obj.bandstructure)

    # with open(MEDIA_ROOT + '/uploads/%s_%s_%s.in' % (obj.phase, p_obj.organic, p_obj.inorganic)) as f:
    #     lines = f.read().splitlines()
    #     for line in lines:
    #         response.write(line + "\n")
    # might need to work on a more efficient method
    response['Content-Disposition'] = 'attachment; filename=%s_%s_%s_%s' % (obj.phase, p_obj.organic, p_obj.inorganic, type)
    return response

# The following two defines views for each specific entry type
def all_a_pos(request, id):
    template_name = 'materials/all_a_pos.html'
    obj = System.objects.get(id=id)
    compound_name = System.objects.get(id=id).compound_name
    obj = obj.atomicpositions_set.all
    return render(request, template_name, {'object': obj, 'compound_name': compound_name})

def all_entries(request, id, type):
    template_name = 'materials/all_%ss.html' % type
    obj = System.objects.get(id=id)
    compound_name = System.objects.get(id=id).compound_name
    obj = dictionary[type].objects.filter(system__id=id)
    return render(request, template_name, {'object': obj, 'compound_name': compound_name, 'data_type': type})

#The following two views make up a WIP ajax search
def search_entries(request):
    if request.method == 'POST':
        search_text = request.POST['search_text']
    else:
        search_text = ''

    systems = System.objects.filter(compound_name__icontains=search_text)

    return render(request, 'materials/materials_search_results.html', {'systems': systems})

def materials(request):
    args = {}
    # args.update(csrf(request))
    args['materials'] = System.objects.all()

    return render(request, 'materials/materials_ajax_search.html', args)

def search_result(search_term, search_text):
    search_results = {
        'formula': System.objects.filter(formula__icontains=search_text),
        'organic': System.objects.filter(organic__icontains=search_text),
        'inorganic': System.objects.filter(inorganic__icontains=search_text),
        # 'exciton_emission': System.objects.filter(excitonemission__exciton_emission__icontains=search_text)
    }
    return search_results[search_term]

# materials search form
class SearchFormView(generic.TemplateView):
    template_name = 'materials/materials_home.html'
    search_terms = [
        ['formula','Chemical Formula'],
        ['organic', 'Organic Component'],
        ['inorganic', 'Inorganic Component'],
        ['exciton_emission', 'Exciton Emission']
    ]

    def get(self, request):
        return render(request, self.template_name, {'search_terms': self.search_terms})

    def post(self, request):
        template_name = 'materials/materials_search_results.html'
        form = SearchForm(request.POST)
        search_text = ""
        # default search_term
        search_term = "formula"
        if form.is_valid():
            print(form.cleaned_data)
            search_text = form.cleaned_data['search_text']
            search_term = request.POST.get('search_term')
            if search_term == 'exciton_emission':
                searchrange = parserange(search_text)
                if len(searchrange) > 0:
                    if searchrange[0] == "bidirectional":
                        if searchrange[3] == ">=":
                            systems = System.objects.filter(excitonemission__exciton_emission__gte=searchrange[1])
                        elif searchrange[3] == ">":
                            systems = System.objects.filter(excitonemission__exciton_emission__gt=searchrange[1])
                        if searchrange[4] == "<=":
                            systems = systems.filter(excitonemission__exciton_emission__lte=searchrange[2])
                        elif searchrange[4] == "<":
                            systems = systems.filter(excitonemission__exciton_emission__lt=searchrange[2])
                    elif searchrange[0] == "unidirectional":
                        if searchrange[2] == ">=":
                            systems = System.objects.filter(excitonemission__exciton_emission__gte=searchrange[1])
                        elif searchrange[2] == ">":
                            systems = System.objects.filter(excitonemission__exciton_emission__gt=searchrange[1])
                        elif searchrange[2] == "<=":
                            systems = System.objects.filter(excitonemission__exciton_emission__lte=searchrange[1])
                        elif searchrange[2] == "<":
                            systems = System.objects.filter(excitonemission__exciton_emission__lt=searchrange[1])
        # systems = System.objects.filter(compound_name__icontains=search_text)
            else:
                systems = search_result(search_term, search_text)

        args = {
            'systems': systems,
            'search_terms': self.search_terms
        }

        return render(request, template_name, args)

class AddAPosView(generic.TemplateView):
    template_name = 'materials/add_a_pos.html'

    def get(self, request):
        search_form = SearchForm()
        a_pos_form = AddAtomicPositions()
        return render(request, self.template_name, {
        'search_form': search_form,
        'a_pos_form': a_pos_form,
        'initial_state': True,
        })

    def post(self, request):
        form = AddAtomicPositions(request.POST, request.FILES)
        print(request.FILES)
        if form.is_valid():
            print("form is valid")
            apos_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            print("system pk is: " + sys_pk)
            text = ""
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                apos_form.publication = Publication.objects.get(pk=pub_pk)
                apos_form.system = System.objects.get(pk=sys_pk)
                text += "Publication and System obtained, "
                if request.user.is_authenticated:
                    apos_form.contributor = UserProfile.objects.get(user=request.user)
                    # print apos_form.contributor
                    text += "UserProfile obtained. Form successfully saved"
                    apos_form.save()
                else:
                    text = "Failed to submit, please login and try again."
        else:
            text = "Failed to submit, please fix the errors, and try again."

        args = {'form': form, 'text': text}

        return HttpResponse(text)

class AddPubView(generic.TemplateView):
    template_name = 'materials/add_publication.html'

    def get(self, request):
        search_form = SearchForm()
        pub_form = AddPublication()
        return render(request, self.template_name, {
        'search_form': search_form,
        'pub_form': pub_form,
        'initial_state': True,
        })

    def post(self, request):
        # check if is ajax
        # if request.is_ajax():
        #     print "is ajax"
        # else:
        #     print "not ajax"
        search_form = SearchForm()
        pub_form = AddPublication(request.POST)
        if pub_form.is_valid():
            form = pub_form.save(commit=False)
            doi_isbn = pub_form.cleaned_data["doi_isbn"]
            pk = request.POST.get('author')
            # check if author is found
            if pk > 0:
                # check if doi_isbn is unique/valid, except when field is empty
                if len(doi_isbn) == 0 or len(Publication.objects.filter(doi_isbn=doi_isbn)) == 0:
                    form.author = Author.objects.get(pk=pk)
                    form.save()
                    text = "Success!"
                else:
                    text = "Failed to submit, publication is already in database."
            else:
                text = "Failed to submit, author not found, please try again."
        else:
            text = "Failed to submit, please fix the errors, and try again."
        args = {
                'search_form': search_form,
                'pub_form': pub_form,
                'text': text,
                'initial_state': True,
                }
        # return render(request, self.template_name, args)
        # ajax version below
        return HttpResponse(text)


class SearchPubView(generic.TemplateView):
    template_name = 'materials/pub_dropdown_list.html'
    from itertools import chain
    def post(self, request):
        search_form = SearchForm(request.POST)
        search_text = ""
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
        author_search = Author.objects.filter(
            Q(first_name__icontains=search_text) | Q(last_name__icontains=search_text) | Q(institution__icontains=search_text)
            )
        if len(author_search) > 0:
            author = author_search[0]
        else:
            author = None
        search_result = Publication.objects.filter(
            Q(title__icontains=search_text) | Q(journal__icontains=search_text) | Q(author=author)
            )
        return render(request, self.template_name, {'search_result': search_result})

# This is for add publication page
class SearchAuthorView(generic.TemplateView):
    # template_name = 'materials/add_publication.html'
    template_name = 'materials/author_dropdown_list.html'

    def post(self, request):
        search_form = SearchForm(request.POST)
        pub_form = AddPublication()
        search_text = ""
        if search_form.is_valid():
            search_text = search_form.cleaned_data['search_text']
        search_result = Author.objects.filter(
            Q(first_name__icontains=search_text) | Q(last_name__icontains=search_text) | Q(institution__icontains=search_text)
            )
            # add last_name filter
        args = {
                'search_form': search_form,
                'search_result': search_result,
                'pub_form': pub_form
                }
        # return render(request, self.template_name, args)
        # ajax version
        return render(request, self.template_name, {'search_result': search_result})

class AddAuthorView(generic.TemplateView):
    template_name = 'materials/add_author.html'

    def get(self, request):
        # search_form = SearchForm()
        input_form = AddAuthor()
        # pub_form = AddPublication()
        return render(request, self.template_name, {
        'input_form': input_form,
        })

    def post(self, request):
        search_form = SearchForm()
        input_form = AddAuthor(request.POST)
        if input_form.is_valid():
            first_name = input_form.cleaned_data["first_name"].lower()
            last_name = input_form.cleaned_data["last_name"].lower()
            institution = input_form.cleaned_data["institution"].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                Author.objects.filter(first_name__iexact=first_name)
                .filter(last_name__iexact=last_name)
                .filter(institution__icontains=institution)
                )
            if q_set_len == 0:
                input_form.save()
                text = "Author successfully added!"
            else:
                text = "Failed to submit, author is already in database."
        else:
            text = "Failed to submit, please fix the errors, and try again."
        args = {
                'input_form': input_form,
                'text': text
                }

        return HttpResponse(text);

class AddTag(generic.TemplateView):
    template_name = 'materials/form.html'

    def get(self, request):
        form = AddTag()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddTag(request.POST)
        if form.is_valid():
            form.save()
            text = form.cleaned_data['email']

        args = {'form': form, 'text': text}

        return render(request, self.template_name, args)

class SearchSystemView(generic.TemplateView):
    template_name = 'materials/system_dropdown_list.html'

    def post(self, request):
        form = SearchForm(request.POST)
        search_text = ""
        if form.is_valid():
            search_text = form.cleaned_data['search_text']

        search_result = System.objects.filter(compound_name__icontains=search_text)
        # ajax version
        return render(request, self.template_name, {'search_result': search_result})

class AddSystemView(generic.TemplateView):
    template_name = 'materials/add_system.html'

    def get(self, request):
        form = AddSystem()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddSystem(request.POST)
        if form.is_valid():
            compound_name = form.cleaned_data["compound_name"].lower()
            formula = form.cleaned_data["formula"].lower()
            # checks to see if the author is already in database
            q_set_len = len(
                System.objects.filter(
                    Q(compound_name__iexact=compound_name) | Q(formula__iexact=formula)
                )
            )
            print(q_set_len)
            if q_set_len == 0:
                form.save()
                text = "System successfully added!"
            else:
                text = "Failed to submit, system is already in database."
        else:
            return render(request, self.template_name, {'form': form})

        return HttpResponse(text);

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
        })

    def post(self, request):
        form = AddExcitonEmission(request.POST, request.FILES)
        if form.is_valid():
            print("form is valid")
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            # print "file: ", request.FILES.get('pl_file')
            print("system pk is: " + sys_pk)
            text = ""
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                # text += "Publication and System obtained, "
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(user=request.user)
                    # print apos_form.contributor
                    text += "Form successfully saved"
                    ee_model = new_form.save()
                    print(ee_model)
                    pl_file_loc = MEDIA_ROOT + "/uploads/%s_%s_%s_pl.csv" % (new_form.phase, new_form.system.organic, new_form.system.inorganic)
                    # print pl_file_loc

                    # Testing feature: automatically populate exciton_emission field with ee peak obtained from graph
                    # if pl_file_loc:
                    #     exciton_emission_peak = plotpl(pl_file_loc)
                    #     print("Model pk")
                    #     print(ee_model.pk)
                    #     ee_object = ExcitonEmission.objects.get(pk=ee_model.pk)
                    #     ee_object.exciton_emission = exciton_emission_peak
                    #     ee_object.save()
                    # add function to set the exciton emission peak to what is reflected in the graph
                else:
                    text = "Failed to submit, please login and try again."
        else:
            text = "Failed to submit, please fix the errors, and try again."

        args = {'form': form, 'text': text}

        return HttpResponse(text)

class AddBandGapView(generic.TemplateView):
    template_name = 'materials/add_band_gap.html'

    def get(self, request):
        search_form = SearchForm()
        band_gap_form = AddBandGap()
        return render(request, self.template_name, {
        'search_form': search_form,
        'band_gap_form': band_gap_form,
        'initial_state': True,
        })

    def post(self, request):
        form = AddBandGap(request.POST, request.FILES)
        if form.is_valid():
            print("form is valid")
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            print("system pk is: " + sys_pk)
            text = ""
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                text += "Publication and System obtained, "
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(user=request.user)
                    # print apos_form.contributor
                    text += "UserProfile obtained. Form successfully saved"
                    new_form.save()
                else:
                    text = "Failed to submit, please login and try again."
        else:
            text = "Failed to submit, please fix the errors, and try again."

        args = {'form': form, 'text': text}

        return HttpResponse(text)

class AddBandStructureView(generic.TemplateView):
    template_name = 'materials/add_band_structure.html'

    def get(self, request):
        search_form = SearchForm()
        band_structure_form = AddBandStructure()
        return render(request, self.template_name, {
        'search_form': search_form,
        'band_structure_form': band_structure_form ,
        'initial_state': True,
        })

    def post(self, request):
        form = AddBandStructure(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            new_form = form.save(commit=False)
            pub_pk = request.POST.get('publication')
            sys_pk = request.POST.get('system')
            # print("system pk is: " + sys_pk)
            text = ""
            if int(pub_pk) > 0 and int(sys_pk) > 0:
                new_form.publication = Publication.objects.get(pk=pub_pk)
                new_form.system = System.objects.get(pk=sys_pk)
                text += "Settings ready. "
                if request.user.is_authenticated:
                    new_form.contributor = UserProfile.objects.get(user=request.user)
                    # print apos_form.contributor
                    bs_folder_loc = MEDIA_ROOT + "/uploads/%s_%s_%s_bs" % (new_form.phase, new_form.system.organic, new_form.system.inorganic)
                    new_form.folder_location = bs_folder_loc
                    try:
                        os.mkdir(bs_folder_loc)
                    except:
                        pass
                    files = request.FILES.getlist("band_structure_files")
                    for f in files:
                        filename = f.name
                        print("filename is: {}", (f.name))
                        full_filename = os.path.join(bs_folder_loc, filename)
                        print("file writen to: {}", (full_filename))
                        with open(full_filename, 'wb+') as write_bs:
                            for chunk in f.chunks():
                                write_bs.write(chunk)
                    text += "Band structure files uploaded. "
                    plotbs(bs_folder_loc)
                    text += "Band structure plotted. "
                    new_form.save()
                else:
                    text = "Failed to submit, please login and try again."
        else:
            text = "Failed to submit, please fix the errors, and try again."

        args = {'form': form, 'text': text}

        return HttpResponse(text)

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

class HomeView(generic.ListView):
    template_name = 'materials/materials_home.html'
    queryset = System.objects.all().order_by('id')
    context_object_name = 'systems_list'

class SystemView(generic.DetailView):
    template_name = 'materials/materials_system.html'
    model = System
