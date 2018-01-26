from django import forms
from materials.models import *

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

# class SearchAuthor(forms.Form):
#     search_text = forms.CharField(label='Search author', max_length=100)
class AddPublication(forms.ModelForm):
    all_fields = ('title', 'journal', 'vol', 'pages_start', 'pages_end', 'year', 'doi_isbn')
    class Meta:
        model = Publication
        exclude = ('author',)
        # fields = ('author', 'title', 'journal', 'vol', 'pages_start', 'pages_end', 'year', 'doi_isbn',)

    def __init__(self, *args, **kwargs):
        super(AddPublication, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddTag(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('tag',)

class AddPhase(forms.ModelForm):
    class Meta:
        model = Phase
        fields = '__all__'

class AddSystem(forms.ModelForm):
    all_fields = ('compound_name', 'group', 'formula', 'organic', 'inorganic', 'description', 'tags')
    class Meta:
        model = System
        exclude = ('last_update',)
        widgets = {
            "description": forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(AddSystem, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddExcitonEmission(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'exciton_emission')
    class Meta:
        model = ExcitonEmission
        exclude = ('contributor', 'publication', 'system')
        labels = {
            "exciton_emission": "Exciton Emission (eV)"
        }

    def __init__(self, *args, **kwargs):
        super(AddExcitonEmission, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddBandGap(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'band_gap')
    class Meta:
        model = BandGap
        exclude = ('contributor', 'publication', 'system')
        labels = {
            "band_gap": "Band Gap (eV)"
        }

    def __init__(self, *args, **kwargs):
        super(AddBandGap, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddBandStructure(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments')
    band_structure_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = BandStructure
        exclude = ('contributor', 'publication', 'system', 'folder_location')

    def __init__(self, *args, **kwargs):
        super(AddBandStructure, self).__init__(*args, **kwargs)
        # self.fields['band_structure_files'].widget.attrs['class'] = "btn btn-default"
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = "form-control"

class AddAtomicPositions(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method', 'comments', 'fhi_file', 'a', 'b', 'c', 'alpha', 'beta', 'gamma', 'volume', 'Z')
    class Meta:
        model = AtomicPositions
        exclude = ('contributor', 'publication', 'system')

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
