from django import forms
from django.utils.safestring import mark_safe

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

    # General
    select_publication = forms.ModelChoiceField(
        queryset=models.Publication.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Select publication where the data to be inserted is published. If ')
    select_system = forms.ModelChoiceField(
        queryset=models.System.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Select the system that is associated with the inserted data.')
    data_set_label = CharField(
        model=models.Dataset, field='label',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Description of the data set.')
    extraction_method = CharField(
        model=models.Dataset, field='extraction_method',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'How was the current data set obtained? For example, manually '
        'extracted from a publication, from author, from another '
        'database, ...')
    primary_property = forms.ModelChoiceField(
        queryset=models.Property.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Define the primary property of interest (in a figure, this typically '
        'denotes the y-axis). If the property of interest is missing here, '
        'add it under "Define new property".')
    primary_unit = forms.ModelChoiceField(
        queryset=models.Unit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control',
                                   'disabled': 'true'}),
        help_text=''
        'Define the primary unit of interest. For dimensionless physical '
        'properties, leave empty. If the data is in arbitray units, select '
        '"a.u." (note that this is different from empty). If the unit of '
        'interest is missing here, add it under "Define new unit".')
    secondary_property = forms.ModelChoiceField(
        queryset=models.Property.objects.all(),
        required=False,
        label='Secondary property (x-axis)',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Define the secondary property of interest (in a figure, this '
        'typically denotes the x-axis). If the property of interest is '
        'missing here, add it under "Define new property".')
    secondary_unit = forms.ModelChoiceField(
        queryset=models.Unit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control',
                                   'disabled': 'true'}),
        help_text=''
        'Define the secondary unit of interest. If the unit of interest '
        'missing here, add it under "Define new unit".')
    visible_to_public = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=True,
        required=False,
        help_text=''
        'Choose whether the data should be initially visible on the website. '
        'If not, only you can view the data. This setting can be easily '
        'toggled later.')
    two_axes = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=False,
        required=False,
        help_text=''
        'Select this if your data has independent (x) and dependent (y) '
        'variables.')
    plotted = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        help_text=''
        'Choose whether the data is more suitably presented as a figure or as '
        'a table. Especially for a large amount of data points, a figure '
        '("plotted") might make more sense. This setting can be easily '
        'toggled later.')
    origin_of_data = forms.ChoiceField(
        initial='experimental',
        choices=(
            ('experimental', 'experimental'), ('theoretical', 'theoretical')),
        widget=forms.RadioSelect(),
        help_text=''
        'Select whether the origin of data is experimental or theoretical.')
    dimensionality_of_the_system = forms.ChoiceField(
        initial=models.Dataset.DIMENSIONALITIES[0],
        choices=(models.Dataset.DIMENSIONALITIES),
        widget=forms.RadioSelect(),
        help_text='Select the dimensionality of the system.')
    sample_type = forms.ChoiceField(
        initial=models.Dataset.SAMPLE_TYPES[0],
        choices=(models.Dataset.SAMPLE_TYPES),
        widget=forms.RadioSelect(),
        help_text='Select the type of the sample.')
    crystal_system = forms.ChoiceField(
        initial=models.Dataset.CRYSTAL_SYSTEMS[0],
        choices=(models.Dataset.CRYSTAL_SYSTEMS),
        widget=forms.RadioSelect(),
        help_text='Select the crystal system.')

    # Synthesis
    with_synthesis_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
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
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Experimental
    with_experimental_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
    experimental_method = CharField(
        label='Method',
        model=models.ExperimentalDetails, field='method',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Short name of the method used, e.g., "X-ray diffraction".')
    experimental_description = CharField(
        label='Description',
        model=models.ExperimentalDetails, field='description',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        help_text='Describe all experimental steps here.')
    experimental_comment = CharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Computational
    with_computational_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
    code = CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Abinit, Quantum espresso...',
        }),
        help_text=''
        'Name of the code(s) used for calculations. It is recommended to also '
        'include other identifiers such as version number, branch name, or '
        'even the commit number if applicable.')
    level_of_theory = CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'DFT, Hartree-Fock, tight-binding, empirical model...',
        }),
        help_text=''
        'yet to come...')
    xc_functional = CharField(
        label='Exchange-correlation functional',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PBE, PW91...',
        }),
        help_text=''
        'yet to come...')
    k_point_grid = CharField(
        label='K-point grid',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3x3x3, 4x5x4 (Monkhorst-Pack)...',
        }),
        help_text=''
        'yet to come...')
    level_of_relativity = CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'non-relativistic, atomic ZORA with SOC, Koelling-Harmon...',
        }),
        help_text=''
        'Specify the level of relativity. Note that this also includes the '
        'description of spin-orbit coupling!')
    basis_set_definition = CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'JTH PAW, TM PP with semicore...',
        }),
        help_text=''
        'yet to come...')
    numerical_accuracy = CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'SCF tol. 1 meV/atom, Lebedev grids for angular integration...',
        }),
        help_text=''
        'Include all parameters here that describe the accuracy of the '
        'calculation (tolerance parameters for an SCF cycle, quality of '
        'integration grids, number of excited states included, ...).')
    computational_comment = CharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Data series

    # Exceptions
    lattice_constant_a = forms.CharField(
        label='Lattice constants',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'a'}),
        help_text=''
        'Units of lattice constants are given by "Primary unit" above.')
    lattice_constant_b = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'b'})
    )
    lattice_constant_c = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'c'})
    )
    lattice_constant_alpha = forms.CharField(
        label='Angles (deg)',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'α'})
    )
    lattice_constant_beta = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'β'})
        )
    lattice_constant_gamma = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'γ'})
    )
    placeholder_ = 'atom &lt;x&gt; &lt;y&gt; &lt;z&gt; &lt;element&gt;&#10;...'
    atomic_coordinates = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': '3',
                   'placeholder': mark_safe(placeholder_)}),
        help_text=''
        'Enter a list of atomic coordinates (optional). The format has one '
        'line per atom. Each line starts with "atom" (absolute coordinates) '
        'or "atom_frac" (fractional coordinates), followed by three numbers '
        'for the coordinate, followed by the element name. For the case of '
        'absolute coordinates ("atom"), the units are given by "Primary unit" '
        'above. Note: to resize this box, drag from the corner.')

    def __init__(self, *args, **kwargs):
        """Dynamically add fixed properties."""
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        if args:
            for key, value in args[0].items():
                if key.startswith('fixed_property_'):
                    self.fields[key] = forms.ModelChoiceField(
                        queryset=models.Property.objects.all(), initial=value)
                elif key.startswith('fixed_unit_'):
                    self.fields[key] = forms.ModelChoiceField(
                        queryset=models.Unit.objects.all(),
                        initial=value, required=False)
                elif key.startswith('fixed_value_'):
                    self.fields[key] = forms.CharField(initial=value)

    def get_fixed_properties(self):
        """Return a list of fixed properties and their current values.

        Instead of an actual list of properties, only the number that
        is in the field's name is returned. This function is relevant
        for reusing the form.

        """
        results = []
        for field in self.fields:
            if field.startswith('fixed_property_'):
                counter = field.split('fixed_property_')[1]
                results.append([counter,
                                self.fields[field].initial,
                                self.fields['fixed_unit_' + counter].initial,
                                self.fields['fixed_value_' + counter].initial])
        return results
