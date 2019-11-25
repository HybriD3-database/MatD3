// Scripts related to submitting new data
'use strict';

// Initialize axios
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFTOKEN';

// Messaging (for dynamic updates)
const create_message = (message_type, message) => {
  const flex = document.createElement('div');
  flex.classList.add('d-flex');
  const alert = document.createElement('div');
  alert.classList.add('alert', message_type);
  alert.innerHTML = message;
  flex.append(alert);
  document.getElementById('dynamic-messages').append(flex);
}
const delete_all_messages = () => {
  const messages = document.getElementById('dynamic-messages');
  while (messages.firstChild) {
    messages.firstChild.remove();
  }
}

// Helper function for building up part of the reference string
const authors_as_string = (authors) => {
  let authors_formatted = [];
  for (let author of authors) {
    authors_formatted.push(`${author.first_name[0]}. ${author.last_name}`);
  }
  return authors_formatted.join(', ');
}

// Extend any of the dropdown menus with a new entry
// (reference, material, property, ...)
function SelectEntryHandler(entry_type, label_name, post_url) {
  let card_id = 'new-' + entry_type + '-card';
  let form_id = entry_type + '-form';
  this.card = document.getElementById(card_id);
  this.form = document.getElementById(form_id);
  this.post_url = post_url;
  this.selectize_label_name = label_name;
  this.entry_type = entry_type;

  // Save new entry into the database and update selectize
  this.add_new_entry = () => {
    delete_all_messages();
    const form_data = new FormData(this.form);
    const label_name = this.selectize_label_name;
    axios
      .post(this.post_url, form_data)
      .then(response => {
        this.card.hidden = true;
        // Update all dropdowns of the current type
        for (let select_name in selectized) {
          if (select_name.includes(this.entry_type)) {
            if (this.entry_type === 'reference') {
              let article = response.data;
              let text =
                `${article.year} - ${authors_as_string(article.authors)}, ` +
                `${article.journal} ${article.vol}`;
              if (article.vol && article.pages_start) text += ',';
              text += ` ${article.pages_start} "${article.title}"`;
              form_data.set('text', text);
            }
            selectized[select_name][0].selectize.addOption({
              pk: response.data.pk, [label_name]: form_data.get(label_name),
            });
            selectized[select_name][0].selectize.refreshOptions;
            selectized[select_name][0].selectize.setValue(response.data.pk, 0);
          }
        }
        create_message(
          'alert-success',
          `New ${this.entry_type} "${form_data.get(label_name)}" ` +
          'successfully added to the database.');
        this.form.reset();
      }).catch(error => {
        create_message(
          'alert-danger',
          `Conflict: ${this.entry_type} "${form_data.get(label_name)}" ` +
          'already exists.');
        console.log(error.message);
        console.log(error.response.statusText);
      });
  }

  this.form.addEventListener('submit', event => {
    event.preventDefault();
    this.add_new_entry();
  });

  // The new entry field is shown/hidden with the '--add new--' (pk=0) field
  this.toggle_visibility = dispatcher_id => {
    $('#' + dispatcher_id).change(() => {
      if ($('#' + dispatcher_id).val() === '0') {
        this.card.hidden = false;
        window.scrollTo(0, 0);
      } else {
        this.card.hidden = true;
      }
    });
  }
}
const new_reference_handler =
  new SelectEntryHandler('reference', 'text', '/materials/references/');
const new_system_handler =
  new SelectEntryHandler('system', 'compound_name', '/materials/systems/');
const new_property_handler =
  new SelectEntryHandler('property', 'name', '/materials/properties/');
const new_unit_handler =
  new SelectEntryHandler('unit', 'label', '/materials/units/');

// All dropdown menus are filled asynchronously
var selectized = {};  // Must use 'var' here for Selenium
const selectize_wrapper = (name, data, initial_value, label_name) => {
  data.push({pk: 0, [label_name]: ' --add new--'});
  selectized[name] = $('#id_' + name).selectize({
    maxOptions: 500,
    valueField: 'pk',
    labelField: label_name,
    sortField: label_name,
    searchField: label_name,
    items: [initial_value],
    options: data,
  });
}
axios
  .get('/materials/references/', {
    transformResponse: [function(data) {
      // Transform each article object into a string
      let articles = JSON.parse(data);
      for (let article of articles) {
        article.text =
          `${article.year} - ${authors_as_string(article.authors)}, ` +
          `${article.journal} ${article.vol}`;
        if (article.vol && article.pages_start) article.text += ',';
        article.text += ` ${article.pages_start} "${article.title}"`;
      }
      return articles;
    }],
  })
  .then(response => {
    selectize_wrapper(
      'select_reference', response.data, initial_reference, 'text');
    let fixed_ref = document.getElementById('id_fixed_reference');
    if (fixed_ref.value) {
      selectized['select_reference'][0].selectize.setValue(fixed_ref.value);
      selectized['select_reference'][0].selectize.disable();
    }
    new_reference_handler.toggle_visibility('id_select_reference');
  });
axios.get('/materials/systems/').then(response => {
  selectize_wrapper(
    'select_system', response.data, initial_system, 'compound_name');
  new_system_handler.toggle_visibility('id_select_system');
});
axios.get('/materials/properties/').then(response => {
  selectize_wrapper(
    'primary_property', response.data, initial_primary_property, 'name');
  selectize_wrapper(
    'secondary_property', response.data, initial_secondary_property, 'name');
  document
    .getElementById('id_primary_property')
    .dispatchEvent(new Event('change'));
  document
    .getElementById('id_two_axes')
    .dispatchEvent(new Event('change'));
  new_property_handler.toggle_visibility('id_primary_property');
  new_property_handler.toggle_visibility('id_secondary_property');
});
axios.get('/materials/units/').then(response => {
  document
    .getElementById('id_primary_unit')
    .setAttribute('placeholder', '--select or add--');
  document
    .getElementById('id_secondary_unit')
    .setAttribute('placeholder', '--select or add--');
  selectize_wrapper(
    'primary_unit', response.data, initial_primary_unit, 'label');
  selectize_wrapper(
    'secondary_unit', response.data, initial_secondary_unit, 'label');
  new_unit_handler.toggle_visibility('id_primary_unit');
  new_unit_handler.toggle_visibility('id_secondary_unit');
});

// When entering data with multiple columns, set "Is figure" to true.
// Do this only once.
let is_figure_untested = true;

// Autofill the main input data textarea
const autofill_data = element => {
  let i_subset = element.id.split('import-data-file_')[1];
  const global_fill = i_subset == null;
  const form_data = new FormData();
  form_data.append('file', element.files[0]);
  if (!global_fill) {
    // Save the name of the original file for later use
    document
      .getElementById(`id_import_file_name_${i_subset}`)
      .value = element.files[0].name;
  }
  element.value = '';  // Clear the file list
  axios
    .post('/materials/autofill-input-data', form_data)
    .then(response => {
      const result =
        response.data.replace(/\n\r/g, '\n').replace(/\r/g, '\n'); // Windows
      const data = result.split(/&/);
      if (global_fill && data.length > 1) {
        const n_subsets = document.getElementById('id_number_of_subsets');
        for (let i = 1; i <= n_subsets.value; i++) {
          document.getElementById('id_subset_datapoints_' + i).value =
            data[i-1].replace(/^\n/, '');
        }
      } else {
        if (i_subset) {
          document.getElementById('id_subset_datapoints_' + i_subset).value =
            result;
        } else {
          document.getElementById('id_subset_datapoints_1').value = result;
        }
      }
      let is_figure = document.getElementById('id_is_figure');
      if (is_figure_untested && !is_figure.readOnly) {
        // If the are multiple lines and multiple columns, it is likely a
        // figure.
        let lines = data[0].split('\n', 2);
        if (lines.length > 1 && lines[0].split(' ').length > 1) {
          if (!is_figure.checked) {
            is_figure.checked = true;
            is_figure.dispatchEvent(new Event('change'));
          }
        }
        is_figure_untested = false;
      }
    })
    .catch(error => {
      if (!i_subset) i_subset = 1;
      document.getElementById('id_subset_datapoints_' + i_subset).value = error;
    });
}
document
  .getElementById('import-all-data')
  .addEventListener('change', function() {
    if ($('#id_primary_property').find(':selected').text() ===
      'atomic structure') {
      import_lattice_parameters(this);
    } else {
      autofill_data(this);
    }
  });

// Create a new data subset
let counter_fixed = 0;
const add_subset = i_subset => {
  // The name and id of each input is appended by _<i_subset>
  const copy =
    document.getElementsByClassName('data-subset-template')[0].cloneNode(true);
  copy.classList.remove('d-none', 'data-subset-template');
  copy.getElementsByClassName('card-header')[0].innerHTML =
    'Subset #' + i_subset;
  for (let element of copy.querySelectorAll('input, textarea')) {
    // Set the defaults of radio buttons from the first subset
    if (i_subset > 1 && element.type === 'radio') {
      const el = document.getElementById(element.id + '_' + 1);
      element.checked = el.checked;
    }
    element.id += '_' + i_subset;
    element.name += '_' + i_subset;
  }
  for (let element of copy.getElementsByTagName('label')) {
    element.htmlFor += '_' + i_subset;
  }
  copy.getElementsByClassName('fixed-properties')[0].id =
    'fixed-properties-' + i_subset;
  const fixed_prop_btn = copy.getElementsByClassName('add-fixed-property')[0]
  fixed_prop_btn.id = 'add-fixed-property-' + i_subset;
  // Add a fixed property
  fixed_prop_btn.addEventListener('click', function() {
    add_fixed_property(i_subset, counter_fixed++);
  });
  copy
    .getElementsByClassName('import-data-file')[0]
    .addEventListener('change', function() {
      autofill_data(this);
    });
  copy
    .getElementsByClassName('import-lattice-parameters')[0]
    .addEventListener('change', function() {
      import_lattice_parameters(this);
    });
  document.getElementById('data-subset').append(copy);
}

// Create a new set of fixed property fields
const add_fixed_property =
  (subset, counter, prop_initial='', unit_initial='', value_initial='') => {
    const copy = document.getElementsByClassName('fixed-property-template')[0]
                         .cloneNode(true);
    const suffix = subset + '_' + counter;
    let el, name;
    copy.classList.remove('d-none', 'fixed-property-template');
    const edit_id_and_name = type => {
      name = 'fixed_' + type + '_' + suffix;
      el = copy.querySelector('[name="fixed_' + type + '"]');
      el.id = 'id_' + name;
      el.name = name;
    }
    edit_id_and_name('property');
    const property_name = name;
    axios.get('/materials/properties/').then(response => {
      selectize_wrapper(property_name, response.data, prop_initial, 'name');
      new_property_handler.toggle_visibility('id_' + property_name);
    });
    edit_id_and_name('unit');
    const unit_name = name;
    axios.get('/materials/units/').then(response => {
      selectize_wrapper(unit_name, response.data, unit_initial, 'label');
      new_unit_handler.toggle_visibility('id_' + unit_name);
    });
    edit_id_and_name('value');
    if (value_initial) {
      copy.querySelector('[name="fixed_value_' + suffix + '"]').value =
        value_initial;
    }
    // Remove a fixed property
    copy
      .getElementsByClassName('close-fixed-property')[0]
      .addEventListener('click', function() {
        let row = this.parentNode.parentNode.parentNode.parentNode;
        row.remove();
      });
    document.getElementById('fixed-properties-' + subset).append(copy);
  }
const number_of_subsets = document.getElementById('id_number_of_subsets');
number_of_subsets.addEventListener('change', function() {
  const data_subset = document.getElementById('data-subset');
  const n_subset_current = data_subset.children.length;
  const n_subset_requested = this.value;
  const n_to_add = n_subset_requested - n_subset_current;
  if (n_to_add > 0) {
    for (let i = 1; i <= n_to_add; i++) {
      add_subset(n_subset_current+i);
    }
  }
  if (n_to_add < 0) {
    for (let i = n_to_add; i < 0; i++) {
      data_subset.lastChild.remove();
    }
  }
  if (data_subset.hasChildNodes()) {
    data_subset.firstChild.getElementsByClassName('subset-label-class')[0]
               .disabled = n_subset_requested == 1;
  }
  document.getElementById('import-all-data').disabled = n_subset_requested == 0;
});
number_of_subsets.dispatchEvent(new Event('change'));

// Collapsable sections of the input
const toggle_section_visibility = (button, hidden_field_id) => {
  const hidden_field = document.getElementById(hidden_field_id);
  $(button).click(function() {
    if (hidden_field.value === 'True') {
      hidden_field.value = 'False';
      $(this).attr('aria-expanded', true);
      $(this).css({'background': '#dce9ff'});
      $(this).html($(this).html().split('remove)')[0] + 'add)');
    } else {
      hidden_field.value = 'True';
      $(this).attr('aria-expanded', false);
      $(this).css({'background': '#f3ebff'});
      $(this).html($(this).html().split('add)')[0] + 'remove)');
    }
  });
  $(button).attr('aria-expanded', hidden_field.value === 'True');
  if (hidden_field.value === 'True') {
    hidden_field.value = 'False';
    $(button).click();
  }
}
toggle_section_visibility(
  '#synthesis-button', 'id_with_synthesis_details');
toggle_section_visibility(
  '#experimental-button', 'id_with_experimental_details');
toggle_section_visibility(
  '#computational-button', 'id_with_computational_details');

// Helper function for setting the value and freezing/unfreezing a checkbox
const set_checkbox = (id, value, freeze) => {
  const element = document.getElementById(id);
  element.checked = value;
  if (freeze) {
    element.readOnly = true;
    element.onclick = function(event) { event.preventDefault(); };
  } else {
    element.readOnly = false;
    element.onclick = null;
  }
  element.dispatchEvent(new Event('change'));
}
const two_axes = document.getElementById('id_two_axes');
two_axes.addEventListener('change', function() {
  if (this.checked) {
    $('#id_secondary_property').parent().show();
    $('#id_secondary_unit').parent().show();
    document.getElementById('id_secondary_property_label').parentNode.hidden =
      false;
    $('label[for="id_primary_property-selectized"]').html('Primary property (y-axis)');
    for (let element of document.getElementsByClassName('subset-datapoints')) {
      element.placeholder = 'x1 y1\nx2 y2\n...';
    }
  } else {
    $('#id_secondary_property').parent().hide();
    $('#id_secondary_unit').parent().hide();
    document.getElementById('id_secondary_property_label').parentNode.hidden =
      true;
    $('label[for="id_primary_property-selectized"]').html('Primary property');
    for (let element of document.getElementsByClassName('subset-datapoints')) {
      element.placeholder = 'value_1 value_2 ...';
    }
  }
});

// If figure then "Two axes" must be enabled
const is_figure = document.getElementById('id_is_figure');
is_figure.addEventListener('change', function() {
  set_checkbox('id_two_axes', this.checked, this.checked);
});
is_figure.dispatchEvent(new Event('change'));

// Prefill most of the form from an other data set
const prefill_button = document.getElementById('prefill-button');
prefill_button.addEventListener('click', event => {
  event.preventDefault();
  const prefill_input = document.getElementById('prefill');
  axios
    .get('/materials/prefilled-form/' + prefill_input.value)
    .then(response => {
      const values = response.data['values'];
      for (const key in values) {
        const el = document.getElementById('id_' + key);
        if (el) {
          if (el.type === 'select-one') {
            selectized[key][0].selectize.setValue(values[key]);
          } else if (el.type === 'checkbox') {
            el.checked = values[key];
          } else {
            el.value = values[key];
          }
        } else { // radio buttons
          document.querySelector('.form-check-input[name="' + key +
                                 '"][value="' + values[key] + '"]')
                  .checked = true;
        }
      }
      const expandables = ['synthesis', 'experimental', 'computational'];
      for (let section of expandables) {
        const button = '#' + section + '-button';
        const hidden_field = document.getElementById('id_with_' + section + '_details');
        // Django renders the value of hidden_field as a string of 'True'
        // or 'False', which is different from the aria-expanded value of
        // 'true' or 'false' as set by Bootstrap, which leads to the messy conditional.
        const cond = ($(button).attr('aria-expanded') === 'false' &&
                      hidden_field.value === 'True') ||
                     ($(button).attr('aria-expanded') === 'true' &&
                      hidden_field.value === 'False');
        if (cond) {
          if (hidden_field.value === 'True') {
            hidden_field.value = 'False';
          } else {
            hidden_field.value = 'True';
          }
          $(button).click();
        }
      }
      document.getElementById('id_primary_property').dispatchEvent(new Event('change'));
      document.getElementById('id_two_axes').dispatchEvent(new Event('change'));
      document.getElementById('id_is_figure').dispatchEvent(new Event('change'));
      prefill_input.value = '';
    }).
     catch(error => {
       create_message('alert-danger',
                      'Data set #' + prefill_input.value + ' does not exist');
       console.log(error.message);
       console.log(error.response.statusText);
     });
});

// Adding and removing authors on the new reference form
document
  .getElementById('add-more-authors-btn')
  .addEventListener('click', () => {
    const latest_first_name =
      document.getElementById('first-names').lastElementChild;
    const latest_last_name =
      document.getElementById('last-names').lastElementChild;
    const latest_institution =
      document.getElementById('institutions').lastElementChild;
    const first_name_copy = latest_first_name.cloneNode(true);
    const last_name_copy = latest_last_name.cloneNode(true);
    const institution_copy = latest_institution.cloneNode(true);
    first_name_copy.hidden = false;
    last_name_copy.hidden = false;
    institution_copy.hidden = false;
    const institution_input = institution_copy.getElementsByTagName('input')[0];
    let input_counter;
    if (latest_first_name.hasAttribute('name')) {
      input_counter =
        Number(latest_first_name.name.split('first-name-')[1]) + 1;
    } else {
      input_counter = 1;
    }
    first_name_copy.name = `first-name-${input_counter}`;
    last_name_copy.name = `last-name-${input_counter}`;
    institution_input.name = `institution-${input_counter}`;
    first_name_copy.id = `first-name-${input_counter}`;
    last_name_copy.id = `last-name-${input_counter}`;
    institution_copy.id = `institution-${input_counter}`;
    first_name_copy.value = '';
    last_name_copy.value = '';
    institution_input.value = '';
    institution_copy
      .getElementsByTagName('button')[0]
      .addEventListener('click', () => {
        first_name_copy.remove();
        last_name_copy.remove();
        institution_copy.remove();
      });
    document.getElementById('first-names').append(first_name_copy);
    document.getElementById('last-names').append(last_name_copy);
    document.getElementById('institutions').append(institution_copy);
  });
document
  .getElementById('add-more-authors-btn')
  .dispatchEvent(new Event('click'));

// Hide special property fields under subsets and show only normal input
function reset_subset_fields() {
  for (let input_type of ['atomic-structure-input', 'phase-transition-input']) {
    for (let element of document.getElementsByClassName(input_type)) {
      element.hidden = true;
    }
  }
  for (let element of document.getElementsByClassName('normal-input')) {
    element.hidden = false;
  }
  if (document.getElementById('id_is_figure').readOnly) {
    set_checkbox('id_is_figure', false, false);
    set_checkbox('id_two_axes', false, false);
  }
  let elements =
    document.querySelectorAll('input[name^="lattice_constant_"]',
                              'input[name="phase_transition_value"]');
  for (let element of elements) {
    element.required = false;
  }
  elements = document.querySelectorAll('textarea[name^="subset_datapoints_"]');
  for (let element of elements) {
    element.required = true;
  }
  for (let label of document.querySelectorAll('.card-subset legend')) {
    label.innerHTML =
      label.innerHTML.replace(/Initial crystal system/, 'Crystal system');
  }
}

// Atomic structure specific
$('#id_primary_property').change(function() {
  if ($('#id_primary_property').find(':selected').text() ===
    'atomic structure') {
    reset_subset_fields();
    for (let el of document.getElementsByClassName('atomic-structure-input')) {
      el.hidden = false;
    }
    for (let element of document.getElementsByClassName('normal-input')) {
      element.hidden = true;
    }
    set_checkbox('id_is_figure', false, true);
    set_checkbox('id_two_axes', false, true);
    // Make these fields required only if 'atomic structure' is the selected
    // property
    for (let element of
      document.querySelectorAll('input[name^="lattice_constant_"]')) {
      element.required = true;
    }
    for (let element of
      document.querySelectorAll('textarea[name^="subset_datapoints_"]')) {
      element.required = false;
    }
  }
});
const import_lattice_parameters = element => {
  let i_subset = element.id.split('import-lattice-parameters_')[1];
  const form_data = new FormData();
  form_data.append('file', element.files[0]);
  const is_cif_format = element.files[0].name.match(/\.cif$/) !== null;
  if (i_subset) {
    // Save the name of the original file for later use
    document
      .getElementById(`id_import_file_name_${i_subset}`)
      .value = element.files[0].name;
  }
  element.value = '';  // Clear the file list
  axios
    .post('/materials/autofill-input-data', form_data)
    .then(response => {
      let data = response.data;
      let a, b, c, alpha, beta, gamma;
      const process_batch = (input_data, dest_suffix) => {
        const lines = input_data.split('\n');
        let aims_format = false;
        if (!is_cif_format) {
          for (let line of lines) {
            if (line.match(/^ *lattice_vector/)) {
              aims_format = true;
              break;
            }
          }
        }
        const i_subset_loc = i_subset ? i_subset : '1';
        const geometry_format =
          document.getElementById(`id_geometry_format_${i_subset_loc}`);
        if (aims_format) {
          // Generate the atomic structure (lattice constants and angles)
          // from lattice vectors
          geometry_format.value = 'aims';
          let lattice_vectors = [];
          const regex =
            /^ *lattice_vector\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\b/;
          let match_;
          for (let line of lines) {
            match_ = line.match(regex);
            if (match_) {
              lattice_vectors.push([match_[1], match_[2], match_[3]]);
            }
            if (lattice_vectors.length == 3) break;
          }
          const norm = vector =>
            Math.sqrt(Math.pow(vector[0],2) +
                      Math.pow(vector[1],2) +
                      Math.pow(vector[2],2));
          const get_angle = (v1, v2, norm1, norm2) =>
            Math.acos((v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2])/norm1/norm2)*360/2/Math.PI;
          if (lattice_vectors.length < 3) {
            throw 'Unable to find three lattice vectors';
          }
          a = norm(lattice_vectors[0]);
          b = norm(lattice_vectors[1]);
          c = norm(lattice_vectors[2]);
          alpha = get_angle(lattice_vectors[1], lattice_vectors[2], b, c);
          beta = get_angle(lattice_vectors[0], lattice_vectors[2], a, c);
          gamma = get_angle(lattice_vectors[0], lattice_vectors[1], a, b);
        } else if (is_cif_format) {
          geometry_format.value = 'cif';
          let match_;
          let matches = {};
          for (let line of lines) {
            match_ = line.match(
              /^_cell_(?:length|angle)_([a-c]|alpha|beta|gamma) +(.*)/);
            if (match_) matches[match_[1]] = match_[2];
            if ('gamma' in matches && 'beta' in matches && 'alpha' in matches &&
                'c' in matches && 'b' in matches && 'a' in matches) break;
          }
          a = matches['a'];
          b = matches['b'];
          c = matches['c'];
          alpha = matches['alpha'];
          beta = matches['beta'];
          gamma = matches['gamma'];
        } else {
          // Read the atomic structure directly from an input file
          const nr_reg =
            /\b([a-z]+)\s+(-?(?:\d+(?:\.\d+)?|\.\d+)(?:\(\d+(?:\.\d+)?\)|\b))/g;
          let matches = [];
          while (matches = nr_reg.exec(input_data)) {
            switch(matches[1]) {
              case 'a':     a     = matches[2]; break;
              case 'b':     b     = matches[2]; break;
              case 'c':     c     = matches[2]; break;
              case 'alpha': alpha = matches[2]; break;
              case 'beta':  beta  = matches[2]; break;
              case 'gamma': gamma = matches[2]; break;
            }
          }
          if (a && b && c && alpha && beta && gamma) {
            input_data = '';
          } else {
            a = b = c = alpha = beta = gamma = '';
          }
        }
        const set_value = (part_id, value) => {
          document.getElementById(part_id + dest_suffix).value = value;
        }
        set_value('id_lattice_constant_a_', a);
        set_value('id_lattice_constant_b_', b);
        set_value('id_lattice_constant_c_', c);
        set_value('id_lattice_constant_alpha_', alpha);
        set_value('id_lattice_constant_beta_', beta);
        set_value('id_lattice_constant_gamma_', gamma);
        set_value('id_atomic_coordinates_', input_data);
      }
      try {
        if (i_subset) {
          process_batch(data, i_subset);
        } else {
          data = data.replace(/\n\r/g, '\n').replace(/\r/g, '\n'); // Windows
          const subsets = data.split('&');
          for (let i = 0; i < subsets.length; i++) {
            if (subsets[i]) {
              process_batch(subsets[i].replace(/^\n/, ''), i+1);
            }
          }
        }
      } catch(error) {
        document.getElementById('id_atomic_coordinates_' + i_subset).value = error;
      }
    }).
     catch(error => {
       if (!i_subset) i_subset = 1;
       document
         .getElementById('id_atomic_coordinates_' + i_subset).innerHTML = error;
     });
}

// Band structure specific
let band_structure_selected = false;
$('#id_primary_property').change(function() {
  const primary_unit = $(this).parent().next();
  if ($(this).find(':selected').text() === 'band structure') {
    reset_subset_fields();
    primary_unit.hide();
    number_of_subsets.readOnly = true;
    number_of_subsets.value = 1;
    number_of_subsets.dispatchEvent(new Event('change'));
    band_structure_selected = true;
    set_checkbox('id_is_figure', false, true);
    set_checkbox('id_two_axes', false, true);
    for (let el of document.getElementsByClassName('subset-datapoints')) {
      el.placeholder = '# K-point path\nX L\nL Gamma\n...';
    }
  } else if (band_structure_selected) {
    primary_unit.show();
    number_of_subsets.readOnly = false;
    band_structure_selected = false;
    set_checkbox('id_is_figure', false, false);
    set_checkbox('id_two_axes', false, false);
  }
});

// Attempt to autofill the k-path textarea from control.in if present
const uploaded_files = document.getElementById('id_uploaded_files')
uploaded_files.addEventListener('change', function() {
  const prop = document.getElementById('id_primary_property');
  if (prop.options[prop.selectedIndex].text === 'band structure' &&
      !document.getElementById('id_subset_datapoints_1').value) {
    let control_file = null;
    for (let file of this.files) {
      if (file.name === 'control.in') {
        control_file = file;
        break;
      }
    }
    if (control_file) {
      const form_data = new FormData();
      form_data.append('file', control_file);
      axios
        .post('/materials/extract-k-from-control-in', form_data)
        .then(response => {
          const result =
            response.data.replace(/\n\r/g, '\n').replace(/\r/g, '\n'); // Windows
          document.getElementById('id_subset_datapoints_1').value = result;
        });
    }
  }
});

// Phase transition specific
$('#id_primary_property').change(function() {
  if ($('#id_primary_property').find(':selected').text()
                               .startsWith('phase transition ')) {
    reset_subset_fields();
    for (let el of document.getElementsByClassName('phase-transition-input')) {
      el.hidden = false;
    }
    for (let element of document.getElementsByClassName('normal-input')) {
      element.hidden = true;
    }
    set_checkbox('id_is_figure', false, true);
    set_checkbox('id_two_axes', false, true);
    for (let label of document.querySelectorAll('.card-subset legend')) {
      label.innerHTML =
        label.innerHTML.replace(/^\s*Crystal system/, 'Initial crystal system');
    }
    for (let element of document.querySelectorAll(
      'input[name="phase_transition_crystal_system_final"]',
      'input[name="phase_transition_value"]')) {
      element.required = true;
    }
    for (let element of
      document.querySelectorAll('textarea[name^="subset_datapoints_"]')) {
      element.required = false;
    }
  }
});
$('#id_primary_property').change(function() {
  const selected = $('#id_primary_property').find(':selected').text();
  if (selected !== 'band structure' &&
      selected !== 'atomic structure' &&
      !selected.startsWith('phase transition ')) {
    reset_subset_fields();
  }
});
