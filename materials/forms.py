# -*- coding: utf-8-*-
from django import forms
from materials.models import *
from django.db.models.signals import post_save

class SearchForm(forms.Form):
    search_text = forms.CharField(label='Search term', max_length=100)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['search_text'].widget.attrs['class'] = "form-control"

class AddAuthor(forms.ModelForm):
    all_fields = ('first_name', 'last_name', 'institution')
    class Meta:
        model = Author
        fields = ('first_name', 'last_name', 'institution')

    def __init__(self, *args, **kwargs):
        super(AddAuthor, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddTag(forms.ModelForm):
    all_fields = ('tag',)
    class Meta:
        model = Tag
        fields = ('tag',)

    def __init__(self, *args, **kwargs):
        super(AddTag, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"
# class SearchAuthor(forms.Form):
#     search_text = forms.CharField(label='Search author', max_length=100)
class AddPublication(forms.ModelForm):
    all_fields = ('title', 'journal', 'vol', 'pages_start', 'pages_end', 'year', 'doi_isbn')
    class Meta:
        model = Publication
        exclude = ('author',)
        labels = {
            "journal": "Journal or Publisher",
            "vol": "Volume",
            "doi_isbn": "doi or ISBN"
        }
        # fields = ('author', 'title', 'journal', 'vol', 'pages_start', 'pages_end', 'year', 'doi_isbn',)

    def __init__(self, *args, **kwargs):
        super(AddPublication, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddPhase(forms.ModelForm):
    class Meta:
        model = Phase
        fields = '__all__'

class AddSystem(forms.ModelForm):
    all_fields = ('compound_name', 'formula', 'group', 'organic', 'inorganic', 'description', 'tags')
    class Meta:
        model = System
        exclude = ('last_update',)
        labels = {
            "formula": "Chemical formula",
            "group": "Common formula",
            "organic": "Organic component",
            "inorganic": "Inorganic component",
        }
        widgets = {
            "description": forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(AddSystem, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddExcitonEmission(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'exciton_emission', 'source', 'data_extraction_method')
    class Meta:
        model = ExcitonEmission
        exclude = ('contributor', 'publication', 'system', 'plotted')
        labels = {
            "pl_file": "PL file",
            "exciton_emission": "Exciton Emission Peak (nm)",
            "phase": "Crystal system"
        }

    def __init__(self, *args, **kwargs):
        super(AddExcitonEmission, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddSynthesisMethod(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'synthesis_method', 'source', 'data_extraction_method')
    class Meta:
        model = SynthesisMethod
        exclude = ('contributor', 'publication', 'system')
        labels = {
            "syn_file": "Synthesis Method (optional)",
            "synthesis_method": "Instructions",
            "phase": "Crystal system"
        }

    def __init__(self, *args, **kwargs):
        super(AddSynthesisMethod, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddBandStructure(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'source', 'data_extraction_method')
    band_structure_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    control_in_file = forms.FileField(label="\"control.in\" file")
    geometry_in_file = forms.FileField(label="\"geometry.in\" file")
    class Meta:
        model = BandStructure
        exclude = ('contributor', 'publication', 'system', 'folder_location', 'plotted')
        labels = {
            "phase": "Crystal system"
        }

    def __init__(self, *args, **kwargs):
        super(AddBandStructure, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddAtomicPositions(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'fhi_file', 'a', 'b', 'c', 'alpha', 'beta', 'gamma', 'volume', 'Z', 'source', 'data_extraction_method')
    class Meta:
        model = AtomicPositions
        exclude = ('contributor', 'publication', 'system')
        labels = {
            "fhi_file": "\"geometry.in\" file",
            "phase": "Crystal system",
            "a": "a",
            "b": "b",
            "c": "c",
            "alpha": "α",
            "beta": "β",
            "gamma": "γ"
        }

    def __init__(self, *args, **kwargs):
        super(AddAtomicPositions, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"
            if(fieldname == 'fhi_file'):
                self.fields[fieldname].widget.attrs['class'] = "form-control-file"

class AddBondAngle(forms.ModelForm):
    class Meta:
        model = BondAngle
        fields = '__all__'

class AddBondLength(forms.ModelForm):
    class Meta:
        model = BondLength
        fields = '__all__'
