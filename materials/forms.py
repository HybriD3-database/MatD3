from django import forms

from materials import models


class SearchForm(forms.Form):
    search_text = forms.CharField(label='Search term', max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['search_text'].widget.attrs['class'] = 'form-control'


class AddAuthor(forms.ModelForm):
    all_fields = ('first_name', 'last_name', 'institution')

    class Meta:
        model = models.Author
        fields = ('first_name', 'last_name', 'institution', 'publication')
        exclude = ('publication',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddTag(forms.ModelForm):
    all_fields = ('tag',)

    class Meta:
        model = models.Tag
        fields = ('tag',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddPublication(forms.ModelForm):
    all_fields = ('title', 'journal', 'vol', 'pages_start', 'pages_end',
                  'year', 'doi_isbn')

    class Meta:
        model = models.Publication
        exclude = ('author',
                   'author_count')
        labels = {
            'journal': 'Journal or Publisher',
            'vol': 'Volume',
            'doi_isbn': 'doi or ISBN',
            'author_count': 'Number of Authors'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddPhase(forms.ModelForm):
    class Meta:
        model = models.Phase
        fields = '__all__'


class AddSystem(forms.ModelForm):
    all_fields = ('compound_name', 'formula', 'group', 'organic', 'inorganic',
                  'description', 'tags')

    class Meta:
        model = models.System
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
        super().__init__(*args, **kwargs)
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
        model = models.BandStructure
        exclude = ('contributor', 'publication', 'system', 'folder_location',
                   'plotted', 'synthesis_method')
        labels = {
            'phase': 'Crystal system',
            'band_gap': 'Band gap (eV)',
            'temperature': 'Temperature (K)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.all_fields:
            self.fields[fieldname].widget.attrs['class'] = 'form-control'


class AddBondAngle(forms.ModelForm):
    class Meta:
        model = models.BondAngle
        fields = '__all__'


class AddBondLength(forms.ModelForm):
    class Meta:
        model = models.BondLength
        fields = '__all__'


class AddDataForm(forms.Form):
    """Main form for submitting data."""
    class CharField(forms.CharField):
        def __init__(self, model=None, field=None, *args, **kwargs):
            if model:
                max_length = model._meta.get_field(field).max_length
            else:
                max_length = None
            super().__init__(required=False, max_length=max_length,
                             *args, **kwargs)

    class PropertySelect(forms.Select):
        """Include require_input_files for each option."""
        def create_option(self, name, value, label, selected, index,
                          subindex=None, attrs=None):
            options = super().create_option(name, value, label, selected,
                                            index, subindex=None, attrs=None)
            if isinstance(value, int):
                options['attrs']['require_input_files'] = str(
                    models.Property.objects.get(
                        pk=int(value)).require_input_files)
            return options

    class ModelChoiceField(forms.ModelChoiceField):
        def __init__(self, *args, **kwargs):
            super().__init__(empty_label='none', required=False,
                             *args, **kwargs)

    # General
    data_set_label = CharField(
        model=models.Dataset, field='label',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Description of the data set.')
    primary_property = ModelChoiceField(
        queryset=models.Property.objects.all().order_by('name'),
        widget=PropertySelect(attrs={'class': 'form-control'}),
        help_text='Define the primary property of interest (in a figure, this '
        'typically denotes the y-axis). If the property of interest missing '
        'here, add it under "Define new property".')
    primary_unit = ModelChoiceField(
        queryset=models.Unit.objects.all().order_by('label'),
        widget=forms.Select(attrs={'class': 'form-control',
                                   'disabled': 'true'}),
        help_text='Define the primary unit of interest (in a figure, this '
        'typically denotes the unit of the y-axis). For dimensionless '
        'physical properties, select "none". If the data is in arbitray '
        'units, select "a.u." (note that this is different from "none"). If '
        'the unit of interest missing here, add it under "Define new unit".')
    secondary_property = ModelChoiceField(
        queryset=models.Property.objects.filter(
            require_input_files=False).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Define the secondary property of interest (in a figure, '
        'this typically denotes the x-axis). When inserting values that have '
        'no direct dependence on a physical property (e.g., a list of phonon '
        'energies), the secondary property may be left empty. If the property '
        'of interest missing here, add it under "Define new property".')
    secondary_unit = ModelChoiceField(
        queryset=models.Unit.objects.all().order_by('label'),
        widget=forms.Select(attrs={'class': 'form-control',
                                   'disabled': 'true'}),
        help_text='Define the secondry unit of interest (in a figure, this '
        'typically denotes the unit of the x-axis). If the unit of interest '
        'missing here, add it under "Define new unit".')
    extraction_method = CharField(
        model=models.Dataset, field='extraction_method',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='How was the current data set obtained? For example, '
        'manually extracted from a publication, from author, from another '
        'database, ...')

    # Synthesis
    starting_materials = CharField(
        model=models.SynthesisMethod, field='starting_materials',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Specify starting materials.')
    product = CharField(
        model=models.SynthesisMethod, field='product',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Specify the final product of synthesis.')
    synthesis_description = CharField(
        label='Description',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        help_text='Describe the steps of the synthesis process.')
    synthesis_comment = CharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Additional information not revelant or suitable for the '
        'description part.')

    # Experimental
    experimental_comment = CharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Additional information not revelant or suitable for the '
        'description part.')

    # Computational
    computational_comment = CharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Additional information not revelant or suitable for the '
        'description part.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
