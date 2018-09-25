# -*- coding: utf-8-*-
from django import forms
from materials.models import (
    Author, Tag, Publication, Phase, System, ExcitonEmission, SynthesisMethod,
    BandStructure, AtomicPositions, BondAngle, BondLength, MaterialProperty)


class SearchForm(forms.Form):
    search_text = forms.CharField(label='Search term', max_length=100)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['search_text'].widget.attrs['class'] = 'form-control'


class AddAuthor(forms.ModelForm):
    all_fields = ('first_name', 'last_name', 'institution')

    class Meta:
        model = Author
        fields = ('first_name', 'last_name', 'institution', 'publication')
        exclude = ('publication',)

    def __init__(self, *args, **kwargs):
        super(AddAuthor, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddTag(forms.ModelForm):
    all_fields = ('tag',)

    class Meta:
        model = Tag
        fields = ('tag',)

    def __init__(self, *args, **kwargs):
        super(AddTag, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddPublication(forms.ModelForm):
    all_fields = ('title', 'journal', 'vol', 'pages_start', 'pages_end',
                  'year', 'doi_isbn')

    class Meta:
        model = Publication
        exclude = ('author',
                   'author_count')
        labels = {
            'journal': 'Journal or Publisher',
            'vol': 'Volume',
            'doi_isbn': 'doi or ISBN',
            'author_count': 'Number of Authors'
        }

    def __init__(self, *args, **kwargs):
        super(AddPublication, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddPhase(forms.ModelForm):
    class Meta:
        model = Phase
        fields = '__all__'


class AddSystem(forms.ModelForm):
    all_fields = ('compound_name', 'formula', 'group', 'organic', 'inorganic',
                  'description', 'tags')

    class Meta:
        model = System
        exclude = ('last_update',)
        labels = {
            'compound_name': 'Compound name (most common name)',
            'formula': 'Chemical formula',
            'group': 'Alternate Names',
            'organic': 'Organic component',
            'inorganic': 'Inorganic component',
        }
        help_texts = {
            'group': 'Please list all possible variations of this compound '
            '(besides those entered above), including different uses of '
            'parentheses -- this is necessary to make this compound easily '
            'searchable.'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'group': forms.TextInput(attrs={
                'placeholder': 'List alternate names, e.g. AEQTPbI4, '
                '(AEQT)PbI4, AE4TPbI4, (AE4T)PbI4 ...'})
        }

    def __init__(self, *args, **kwargs):
        super(AddSystem, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddExcitonEmission(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method',
                  'comments', 'exciton_emission', 'source',
                  'data_extraction_method')

    class Meta:
        model = ExcitonEmission
        exclude = ('contributor', 'publication', 'system', 'plotted',
                   'synthesis_method')
        labels = {
            'pl_file': 'PL file',
            'exciton_emission': 'Exciton Emission Peak (nm)',
            'phase': 'Crystal system',
            'temperature': 'Temperature (K)'
        }

    def __init__(self, *args, **kwargs):
        super(AddExcitonEmission, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddSynthesisMethod(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'comments', 'synthesis_method',
                  'source', 'data_extraction_method', 'starting_materials',
                  'remarks', 'product')
    field_order = ('source', 'data_extraction_method', 'temperature', 'phase',
                   'synthesis_method', 'starting_materials', 'remarks',
                   'product', 'comments')

    class Meta:
        model = SynthesisMethod
        exclude = ('contributor', 'publication', 'system', 'method',
                   'specific_method')
        labels = {
            'syn_file': 'Synthesis Method File (optional)',
            'synthesis_method': 'Synthesis Method',
            'phase': 'Crystal system',
            'temperature': 'Temperature (K)'
        }
        widgets = {
            'synthesis_method': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g. expirimental, solution grown'}),
            'starting_materials': forms.Textarea(attrs={'rows': 4}),
            'remarks': forms.Textarea(attrs={'rows': 6}),
            'product': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, *args, **kwargs):
        super(AddSynthesisMethod, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddBandStructure(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method',
                  'comments', 'source', 'data_extraction_method', 'band_gap')
    band_structure_files = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': True}), required=False)
    control_in_file = forms.FileField(label='"control.in" file',
                                      required=False)
    geometry_in_file = forms.FileField(label='"geometry.in" file',
                                       required=False)

    class Meta:
        model = BandStructure
        exclude = ('contributor', 'publication', 'system', 'folder_location',
                   'plotted', 'synthesis_method')
        labels = {
            'phase': 'Crystal system',
            'band_gap': 'Band gap (eV)',
            'temperature': 'Temperature (K)'
        }

    def __init__(self, *args, **kwargs):
        super(AddBandStructure, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddAtomicPositions(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method',
                  'comments', 'fhi_file', 'a', 'b', 'c', 'alpha', 'beta',
                  'gamma', 'volume', 'Z', 'source', 'data_extraction_method')

    class Meta:
        model = AtomicPositions
        exclude = ('contributor', 'publication', 'system', 'synthesis_method')
        labels = {
            'fhi_file': '"geometry.in" file',
            'phase': 'Crystal system',
            'a': 'a',
            'b': 'b',
            'c': 'c',
            'alpha': 'α',
            'beta': 'β',
            'gamma': 'γ',
            'temperature': 'Temperature (K)'
        }

    def __init__(self, *args, **kwargs):
        super(AddAtomicPositions, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'
            if(fieldname == 'fhi_file'):
                self.fields[fieldname].widget.attrs['class'] = (
                    'form-control-file')


class AddBondAngle(forms.ModelForm):
    class Meta:
        model = BondAngle
        fields = '__all__'


class AddBondLength(forms.ModelForm):
    class Meta:
        model = BondLength
        fields = '__all__'


class AddMaterialProperty(forms.ModelForm):
    all_fields = ('temperature', 'phase', 'method', 'specific_method',
                  'comments', 'source', 'data_extraction_method', 'property',
                  'value')
    field_order = ('source', 'data_extraction_method', 'temperature', 'phase',
                   'method', 'specific_method', 'property', 'value',
                   'comments')

    class Meta:
        model = MaterialProperty
        exclude = ('contributor', 'publication', 'system')
        labels = {
            'phase': 'Crystal system',
            'temperature': 'Temperature (K)',
            'value': 'Value of Property'
        }

    def __init__(self, *args, **kwargs):
        super(AddMaterialProperty, self).__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'
