===================
Database structure
===================

The web interface for the database is written in the Django web framework and the database itself is of SQL type. That is, any structured database should in principle be fine for hosting (mySQL, SQLite), but we recommend using mySQL/MariaDB. This section provides an overview of the Django models used for the website. The presentation focuses on how the models are defined in the Python source code and not the actual SQL tables. For example, even though fields such as the primary key are not listed in the following, it is understood that these are automatically created for the SQL tables.

Most models inherit from a base model which records information of how each entry is created/updated. Since actual polymorphism is not supported in relational databases, Django explicitly copies these fields to any child models.

.. admonition:: Base

  **created**
    date the entry was created
  **updated**
    date the entry was last modified
  **created by**
    user that created the entry
  **updated by**
    user that updated the entry

All properties are stored in a table that contains the name of the property.

.. admonition:: Property(Base)

  **name**
    displayed name of the property

All units are stored in a table that contains the label field.

.. admonition:: Unit(Base)

  **label**
    "nm", "cm\ :sup:`2` V\ :sup:`-1` s\ :sup:`-1`", ...

A solid system is defined by the following properties.

.. admonition:: System

  **compound name**
    displayed name of the material
  **formula**
    chemical formula for the compound
  **group**
    alternate names
  **organic**
    organic component
  **inorganic**
    inorganic component
  **last_update**
    date the system was last modified
  **description**
    description of the compound

Authors and references are stored in the following tables.

.. admonition:: Author

  **first_name**
    first name
  **last_name**
    last name
  **institution**
    institution, does not have to be the full address
  **reference**
    a ManyToMany field that maps authors to references.

.. admonition:: Reference

  **title**
    title of the paper
  **journal**
    journal name
  **vol**
    volume
  **pages_start**
    starting page number
  **pages_end**
    end page number
  **year**
    year of publication
  **doi_isbn**
    DOI/ISBN if applicable

All experimental and theoretical results are contained in data sets. A data set typically refers to a single value, table, or figure found in a reference. The quantity of primary interest is called the "primary property". For example, given some data where the band gap depends on temperature, the band gap and temperature would be the "primary" and "secondary" properties, respectively (think of these as y- and x-values in a plot).

.. admonition:: Dataset(Base)

  **caption**
    description of the data set
  **system**
    foreign key for System
  **primary_property**
    foreign key for Property
  **primary_unit**
    foreign key for Unit
  **primary_property_label**
    custom label for the y-axis (typically left empty and the property name is used instead)
  **secondary_property**
    foreign key for Property
  **secondary_unit**
    foreign key for Unit
  **secondary_property_label**
    custom label for the x-axis (typically left empty and the property name is used instead)
  **reference**
    foreign key for Reference
  **visible**
    whether the data is visible on the website
  **is_figure**
    whether the data should be plotted
  **plotted**
    whether data is plotted by default
  **experimental**
    whether the data is of experimental origin (theoretical if false)
  **dimensionality**
    dimensionality of the inorganic component as understood in the HOIP literature (not the dimensionality of the crystal)
  **sample_type**
    single crystal, powder, \ldots
  **extraction_method**
    short explanation for how the data was obtained
  **representative**
    in case of multiple entries of the same property for a given material, whether this data set should be shown on the material's main page.
  **linked_to**
    a ManyToManyField, used if the numerical values of this data set are somehow directly linked to another data set
  **verified_by**
    list of users that have verified the correctness of the data set

A data set consists of one or more data subsets. One is always present but there could be several if it is possible to logically group the data somehow. For instance, different curves in a figure would correspond to separate data subsets.

.. admonition:: Subset(Base)

  **dataset**
    foreign key for Dataset
  **label**
    short description of this subset
  **crystal_system**
    one of the seven crystal systems

A data subset consists of one or more data points. When describing a single value such as the band gap of a material with no additional dependencies, the whole data set would consist of one subset with only one data point with one numerical value.

.. admonition:: Datapoint(Base)

  **subset**
    foreign key for Subset

Finally, the actual data is stored in the **NumericalValue** table.

.. admonition:: NumericalValue(Base)

  **datapoint**
    foreign key for Datapoint
  **qualifier**
    "primary", "secondary"
  **value_type**
    "accurate", "approximate", "lower/upper bound"
  **value**
    floating point number
  **counter**
    counts the number of values attached to a given data point

Any errors (uncertainties) associated with a numerical value are stored in a separate table. In the code, the errors are then retrieved from the database by querying for numerical values with the \verb+select_related('error')+ function and checking if a value has an associated error (\verb+if hasattr(value, 'error')+).

.. admonition:: Error(Base)

  **numerical_value**
    foreign key for NumericalValue
  **value**
    floating point number

Similarly to errors, when dealing with ranges, the upper bounds are stored in a separate table. The **value** field is then understood to contain the lower bound of the range

.. admonition:: UpperBound(Base)

  **numerical_value**
    foreign key for NumericalValue
  **value**
    floating point number

A separate table is used for values that are fixed across a data subset. For instance, if the curves of band gap vs dopant density are measured for different temperatures, then "band gap", "dopant density", and "temperature" would be "primary", "secondary", and "fixed", respectively. Unlike regular numerical values, the fixed values are far lesser in number. Thus, we can attach the errors directly to the values without a performance penalty.

.. admonition:: NumericalValueFixed(Base)

  **dataset**
    foreign key for Dataset
  **subset**
    foreign key for Subset
  **physical_property**
    foreign key for Property
  **unit**
    foreign key for Unit
  **value**
    floating point number
  **type**
    "accurate", "approximate", "lower/upper bound", "error"
  **error**
    floating point number (optional)
  **upper_bound**
    floating point number (optional); if present, then **value** is understood to be the lower bound for the range

If the dependence of the primary property is on something that cannot be stored as a floating point number, it is stored in the **Symbol** table. Example: the user enters band gap values a function of phase. The phases are then stored as strings in the following table.

.. admonition:: Symbol(Base)

  **datapoint**
    foreign key for Datapoint
  **value**
    a string
  **counter**
    counts the number of symbols attached to a given data point

In case of an experimental study, the details of the synthesis method and the experiment can be stored in the following tables.

.. admonition:: SynthesisMethod(Base)

  **dataset**
    foreign key for Datapoint
  **starting_materials**
    starting materials of synthesis
  **product**
    product of synthesis
  **description**
    detailed description of the synthesis process

.. admonition:: ExperimentalDetails(Base)

  **dataset**
    foreign key for Datapoint
  **method**
    name of the experimental method
  **description**
    detailed description of the experiment

Similarly, in case of a theoretical study, the computational details are recorded in a separate table.

.. admonition:: ComputationalDetails(Base)

  **dataset**
    foreign key for Datapoint
  **code**
    computer code used for calculations
  **level_of_theory**
    level of theory used in the calculation
  **xc_functional**
    exchange-correlation functional
  **k_point_grid**
    details about the K-point grid
  **level_of_relativity**
    level of relatively (this includes the description of spin-orbit coupling)
  **basis_set_definition**
    anything related to the basis set used (this includes pseudopotential details, if applicable)
  **numerical_accuracy**
    information about parameters that control the accuracy of the calculation

Each entry of synthesis method, experimental details, or computational details may have a comment, which is stored in a separate table.

.. admonition:: Comment(Base)

  **synthesis_method**
    foreign key for SynthesisMethod
  **experimental_details**
    foreign key for ExperimentalDetails
  **computational_details**
    foreign key for ComputationalDetails
  **text**
    comment body

Besides storing all numerical data in a structured database, the data is also stored in the form of files. This way the original user uploaded data is stored without modifications, e.g., preserving any comments that the input file may contain.

.. admonition:: InputDataFile(Base)

  **dataset**
    foreign key for Dataset
  **dataset_file**
    a file upload field

Any additional files, if present, are stored in **DatasetFile** (input/output files for a calculation, image of the sample, \ldots).

.. admonition:: AdditionalFile(Base)

  **dataset**
    foreign key for Dataset
  **dataset_file**
    a file upload field

Phase transition properties, such as the phase transition pressure, required special treatment and are stored in **PhaseTransition**.

.. admonition:: PhaseTransition(Base)

  **subset**
    foreign key for Subset
  **crystal_system_final**
    final crystal system; **crystal_system** of the subset is then understood to be the initial crystal system
  **space_group_initial**
    initial space group
  **space_group_final**
    final space group
  **direction**
    direction of the phase transition
  **hysteresis**
    details about the hysteresis of the phase transition
  **value**
    floating point number
  **value_type**
    "accurate", "approximate", "lower/upper bound"
  **counter**
    number of values attached to a given subset
  **error**
    uncertainty of the value
  **upper_bound**
    upper bound of the value

All user information is stored in the **UserProfile** table.

.. admonition:: UserProfile

  **user**
    the default Django user model
  **description**
    description of the user (e.g., undergraduate)
  **institution**
    name of the institution
  **website**
    website of the user
