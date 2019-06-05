# This file is covered by the BSD license. See LICENSE in the root directory.
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
        fields = ('first_name', 'last_name', 'institution', 'reference')
        exclude = ('reference',)

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


class AddReference(forms.ModelForm):
    all_fields = ('title', 'journal', 'vol', 'pages_start', 'pages_end',
                  'year', 'doi_isbn')

    class Meta:
        model = models.Reference
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


class AutoCharField(forms.CharField):
    """Like regular CharField but max_length is automatically determined."""
    def __init__(self, model=None, field=None, *args, **kwargs):
        if model:
            max_length = model._meta.get_field(field).max_length
        else:
            max_length = None
        super().__init__(required=False, max_length=max_length,
                         *args, **kwargs)


class AddPropertyForm(forms.Form):
    property_name = AutoCharField(
        model=models.Property, field='name',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Name of the physical property.')


class AddUnitForm(forms.Form):
    unit_label = AutoCharField(
        model=models.Unit, field='label',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Label of the unit.')


class AddDataForm(forms.Form):
    """Main form for submitting data."""

    # General
    related_data_sets = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'List of data set IDs directly related (linked) to this data (space '
        'separated). Two or more data sets can be linked if they are results '
        'of the same experiment or calculation but describe different '
        'physical properties (e.g., "band structure" and "band gap" or '
        '"absorption coefficient" and "absorption peak position"). Find the '
        'related data set IDs as "Data set ID" at the bottom of the data sets.'
    )
    select_reference = forms.ModelChoiceField(
        queryset=models.Reference.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Select the reference that is associated with the inserted data. If '
        'the data is unpublished or no reference is applicable, leave empty.')
    select_system = forms.ModelChoiceField(
        queryset=models.System.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=''
        'Select the system that is associated with the inserted data.')
    label = AutoCharField(
        model=models.Dataset, field='label',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Main description of the data. This can include an explanation of the '
        'significance of the results.')
    extraction_method = AutoCharField(
        label='Data extraction protocol',
        model=models.Dataset, field='extraction_method',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'How was the current data obtained? For example, manually extracted '
        'from a publication, from author, from another database, ...')
    primary_property = forms.ModelChoiceField(
        queryset=models.Property.objects.all(),
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
    primary_property_label = AutoCharField(
        model=models.Dataset, field='primary_property_label',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave empty if not required'
        }),
        help_text=''
        'If present, this label is used on the y-axis of a figure. Default is '
        'to use the same name as the physical property.')
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
    secondary_property_label = AutoCharField(
        model=models.Dataset, field='secondary_property_label',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave empty if not required'
        }),
        help_text=''
        'If present, this label is used on the x-axis of a figure. Default is '
        'to use the same name as the physical property.')
    is_figure = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        help_text=''
        'Choose whether the data is more suitably presented as a figure or as '
        'a table. Especially for a large amount of data points, a figure '
        'might make more sense. This setting can be easily toggled later.')
    two_axes = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=False,
        required=False,
        help_text=''
        'Select this if your data has independent (x) and dependent (y) '
        'variables.')
    visible_to_public = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=True,
        required=False,
        help_text=''
        'Choose whether the data should be initially visible on the website. '
        'If not, only you can view the data. This setting can be easily '
        'toggled later.')
    origin_of_data = forms.ChoiceField(
        initial='is_experimental',
        choices=(
            ('is_experimental', 'experimental'),
            ('is_theoretical', 'theoretical'),
        ),
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

    # Synthesis
    with_synthesis_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
    starting_materials = AutoCharField(
        model=models.SynthesisMethod, field='starting_materials',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Specify the starting materials.')
    product = AutoCharField(
        model=models.SynthesisMethod, field='product',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Specify the final product of synthesis.')
    synthesis_description = AutoCharField(
        label='Description',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        help_text='Describe the steps of the synthesis process.')
    synthesis_comment = AutoCharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Experimental
    with_experimental_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
    experimental_method = AutoCharField(
        label='Method',
        model=models.ExperimentalDetails, field='method',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Short name of the method used, e.g., "X-ray diffraction".')
    experimental_description = AutoCharField(
        label='Description',
        model=models.ExperimentalDetails, field='description',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        help_text='Describe all experimental steps here.')
    experimental_comment = AutoCharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Computational
    with_computational_details = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput())
    code = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Abinit, Quantum espresso...',
        }),
        help_text=''
        'Name of the code(s) used for calculations. It is recommended to also '
        'include other identifiers such as version number, branch name, or '
        'even the commit number if applicable.')
    level_of_theory = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'DFT, Hartree-Fock, tight-binding, empirical model...',
        }),
        help_text=''
        'Level of theory summarizes the collection of physical approximations '
        'used in the calculation. It gives an overall picture of the physics '
        'involved. Finer details of the level of theory such as the level of '
        'relativity should be filled separately.')
    xc_functional = AutoCharField(
        label='Exchange-correlation functional',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PBE, PW91...',
        }),
        help_text=''
        'Level of approximation used to treat the electron-electron '
        'interaction.')
    k_point_grid = AutoCharField(
        label='K-point grid',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3x3x3, 4x5x4 (Monkhorst-Pack)...',
        }),
        help_text=''
        'Details of the k-point mesh.')
    level_of_relativity = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'non-relativistic, atomic ZORA with SOC, Koelling-Harmon...',
        }),
        help_text=''
        'Specify the level of relativity. Note that this also includes the '
        'description of spin-orbit coupling!')
    basis_set_definition = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'JTH PAW, TM PP with semicore...',
        }),
        help_text=''
        'Details of the basis set or of the algorithms directly related to '
        'the basis set. For example, in case of a plane wave calculation, '
        'also include details of the pseudopotential here if applicable.')
    numerical_accuracy = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'SCF tol. 1 meV/atom, Lebedev grids for angular integration...',
        }),
        help_text=''
        'Include all parameters here that describe the accuracy of the '
        'calculation (tolerance parameters for an SCF cycle, quality of '
        'integration grids, number of excited states included, ...).')
    external_repositories = AutoCharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':
            'http://dx.doi.org/00.00000/NOMAD/2000.01.30-5 ...',
        }),
        help_text=''
        'Provide link(s) to external repositories such as NOMAD, which host '
        'additional data related to the data entered here.')
    computational_comment = AutoCharField(
        label='Comments',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=''
        'Additional information not revelant or suitable for the description '
        'part.')

    # Data subset
    number_of_subsets = forms.CharField(
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control mx-sm-3',
                                        'min': '1',
                                        'style': 'width:8em'}),
        help_text=''
        'Enter the number of data subgroups. For each subgroup, one or more '
        'properties or some other aspect of the experiment/calculation are '
        'typically fixed (see the help text for "Add fixed property"). In '
        'case of a figure, each curve is typically considered a separate data '
        'subset.')
    crystal_system = forms.ChoiceField(
        required=False,
        initial=models.Subset.CRYSTAL_SYSTEMS[0],
        choices=(models.Subset.CRYSTAL_SYSTEMS),
        widget=forms.RadioSelect(),
        help_text='Select the crystal system.')
    subset_label = AutoCharField(
        label='Label',
        model=models.Subset, field='label',
        widget=forms.TextInput(
            attrs={'class': 'form-control subset-label-class'}),
        help_text=''
        'Short description of the data subset (optional). In a figure, this '
        'information is typically shown in the legend. Not applicable with '
        'only one data subset set.')
    subset_datapoints = forms.CharField(
        required=False,
        label='Data points',
        widget=forms.Textarea(
            attrs={'class': 'form-control subset-datapoints', 'rows': '4',
                   'placeholder': 'value_1 value_2 ...'}),
        help_text=''
        'Insert data points here. These may be a single value, a series of '
        'values, or a series of value pairs. The latter applies when there '
        'are both primary and secondary properties, in which case the first '
        'column has values of the secondary property (x-values) and the '
        'second column corresponds to the primary property (y-values). Note: '
        'to resize this box, drag from the corner.')
    # Exceptions
    lattice_constant_a = forms.CharField(
        label='Lattice constants',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'a'}),
        help_text=''
        'Units of lattice constants are given by "Primary unit" above. When '
        'importing from file, two formats are allowed. In the first format, '
        'include "a", "b", "c", "alpha", "beta", and "gamma" followed by '
        'their respective values. This can be either on one line or on '
        'separate lines (e.g., "a val1 b val2 ..."). For the second format, '
        'see the help text of "Atomic coordinates" below.')
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
    placeholder_ = (
        'lattice_vector &lt;x&gt; &lt;y&gt; &lt;z&gt;&#10;...&#10;'
        'atom &lt;x&gt; &lt;y&gt; &lt;z&gt; &lt;element&gt;&#10;...')
    atomic_coordinates = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'rows': '3',
                   'placeholder': mark_safe(placeholder_)}),
        help_text=''
        'Enter a list of lattice vectors and atomic coordinates (optional). '
        'Each of the three lattice vectors starts with the word '
        '"lattice_vector" followed by three coordinates. Each line for the '
        'atomic coordinates starts with "atom" (absolute coordinates) or '
        '"atom_frac" (fractional coordinates), followed by three numbers for '
        'the coordinate, followed by the element name. For the case of '
        'absolute coordinates ("atom"), the units are given by "Primary unit" '
        'above. Note: to resize this box, drag from the corner.')

    # Uploads
    uploaded_files = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        help_text=''
        'Upload files containing anything that is relevant to the current '
        'data (input files to a calculation, image of the sample, ...). '
        'Multiple files can be selected here.')

    def __init__(self, *args, **kwargs):
        """Dynamically add subsets and fixed properties."""
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        if args:
            for key, value in args[0].items():
                if key.startswith('subset_datapoints_'):
                    self.fields[key] = forms.CharField(
                        required=False, widget=forms.Textarea, initial=value)
                elif key.startswith('subset_label_'):
                    self.fields[key] = forms.CharField(required=False,
                                                       initial=value)
                elif key.startswith('crystal_system_'):
                    self.fields[key] = forms.ChoiceField(
                        required=False,
                        initial=value,
                        choices=(models.Subset.CRYSTAL_SYSTEMS),
                        widget=forms.RadioSelect())
                elif key.startswith('fixed_property_'):
                    self.fields[key] = forms.ModelChoiceField(
                        queryset=models.Property.objects.all(), initial=value)
                elif key.startswith('fixed_unit_'):
                    self.fields[key] = forms.ModelChoiceField(
                        queryset=models.Unit.objects.all(),
                        initial=value, required=False)
                elif key.startswith('fixed_value_'):
                    self.fields[key] = forms.CharField(initial=value)
                elif key.startswith('lattice_constant_'):
                    self.fields[key] = forms.CharField(required=False,
                                                       initial=value)
                elif key.startswith('atomic_coordinates_'):
                    self.fields[key] = forms.CharField(
                        required=False, widget=forms.Textarea, initial=value)

    def clean(self):
        """Set secondary property conditionally required."""
        data = self.cleaned_data
        if data.get('two_axes') and not data.get('secondary_property'):
            self.add_error('secondary_property', 'This field is required.')
        if not all(map(lambda x: x.isdigit(),
                       data.get('related_data_sets').split())):
            self.add_error('related_data_sets',
                           'This must be a list of space separated integers.')

    def get_subset(self):
        """Return a list of initial values for data subset."""
        results = []
        for field in self.fields:
            if field.startswith('subset_datapoints_'):
                counter = field.split('subset_datapoints_')[1]
                crystal_system = self.fields[
                    'crystal_system_' + counter].initial
                if 'subset_label_' + counter in self.fields:
                    label = self.fields['subset_label_' + counter].initial
                else:
                    label = ''
                datapoints = self.fields[field].initial
                results.append([counter, crystal_system, label, datapoints])
        return results

    def get_fixed_properties(self):
        """Return a list of fixed properties and their current values."""
        results = []
        for field in self.fields:
            if field.startswith('fixed_property_'):
                suffix = field.split('fixed_property_')[1]
                subset, counter = suffix.split('_')
                results.append([subset, counter,
                                self.fields[field].initial,
                                self.fields['fixed_unit_' + suffix].initial,
                                self.fields['fixed_value_' + suffix].initial])
        return results

    def get_lattice_parameters(self):
        results = []
        for field in self.fields:
            if field.startswith('lattice_constant_a_'):
                subset = field.split('lattice_constant_a_')[1]
                results.append([
                    subset,
                    self.fields['lattice_constant_a_' + subset].initial,
                    self.fields['lattice_constant_b_' + subset].initial,
                    self.fields['lattice_constant_c_' + subset].initial,
                    self.fields['lattice_constant_alpha_' + subset].initial,
                    self.fields['lattice_constant_beta_' + subset].initial,
                    self.fields['lattice_constant_gamma_' + subset].initial,
                    self.fields['atomic_coordinates_' + subset].initial,
                ])
        return results
