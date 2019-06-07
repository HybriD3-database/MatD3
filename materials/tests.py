# This file is covered by the BSD license. See LICENSE in the root directory.
from copy import deepcopy
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import LiveServerTestCase
from django.test import TestCase

from . import models
from accounts.tests import USERNAME
from accounts.tests import PASSWORD

User = get_user_model()
dataset_template = models.Dataset(visible=True,
                                  is_figure=False,
                                  is_experimental=True,
                                  dimensionality=3,
                                  sample_type=models.Dataset.SINGLE_CRYSTAL)


class ModelsTestCase(TestCase):
    fixtures = ['users.json',
                'properties.json',
                'units.json',
                'references.json',
                'authors.json',
                'systems.json',
                'datasets.json']

    @classmethod
    def setUpTestData(cls):
        """Start with three data sets of different property"""
        dataset = models.Dataset.objects.first()
        dataset.pk = None
        dataset.primary_property = models.Property.objects.get(
            name='dielectric constant')
        dataset.save()
        dataset.pk = None
        dataset.primary_property = models.Property.objects.get(
            name='atomic structure')
        dataset.save()

    def test_dataset_links(self):
        datasets = models.Dataset.objects.all()
        # Basic functionality
        datasets[0].linked_to.add(datasets[1])
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 2)
        self.assertEqual(datasets[0].linked_to.last().pk, datasets[1].pk)
        self.assertEqual(datasets[1].linked_to.last().pk, datasets[0].pk)
        self.assertEqual(datasets[2].linked_to.count(), 0)
        # Test if datasets[1] and datasets[2] automatically become linked
        datasets[0].linked_to.add(datasets[2])
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 6)
        self.assertEqual(datasets[2].linked_to.last().pk, datasets[1].pk)
        [self.assertEqual(ds.linked_to.count(), 2) for ds in datasets]
        # This should have no effect
        datasets[2].linked_to.add(datasets[1])
        [self.assertEqual(ds.linked_to.count(), 2) for ds in datasets]
        # Simple removal of a link
        datasets[2].linked_to.remove(datasets[1])
        self.assertEqual(datasets[2].linked_to.last().pk, datasets[0].pk)
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 4)
        # Deletion should remove all references to the given data set
        datasets[2].linked_to.add(datasets[1])
        datasets[2].delete()
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 2)

    def test_dataset_links_advanced(self):
        for _ in range(2):
            dataset = models.Dataset.objects.last()
            dataset.pk = None
            dataset.save()
        datasets = models.Dataset.objects.all()
        datasets[0].linked_to.add(datasets[1])
        datasets[4].linked_to.add(datasets[3])
        datasets[1].linked_to.add(datasets[3])
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 12)
        datasets[2].linked_to.add(datasets[3])
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 20)
        models.Dataset.objects.last().delete()
        self.assertEqual(models.Dataset.linked_to.through.objects.count(), 12)


class SeleniumTestCase(LiveServerTestCase):
    fixtures = ['users.json',
                'properties.json',
                'units.json',
                'references.json',
                'authors.json',
                'systems.json',
                'datasets.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Firefox(service_log_path='/dev/null')
        cls.selenium.maximize_window()
        cls.selenium.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def login(self):
        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_link_text('Login').click()
        self.selenium.find_element_by_name('username').send_keys(USERNAME)
        self.selenium.find_element_by_name('password').send_keys(PASSWORD)
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

    def set_property(self, selectize_name, property_name):
        """Shortcut for setting physical properties with selectize"""
        pk = models.Property.objects.get(name=property_name).pk
        self.selenium.execute_script(
            f"selectized['{selectize_name}'][0].selectize.setValue({pk})")

    def set_unit(self, selectize_name, unit_label):
        """Shortcut for setting units with selectize"""
        pk = models.Unit.objects.get(label=unit_label).pk
        self.selenium.execute_script(
            f"selectized['{selectize_name}'][0].selectize.setValue({pk})")

    def test_properties_and_units(self):
        self.login()
        models.Dataset.objects.all().delete()
        models.Property.objects.all().delete()
        models.Unit.objects.all().delete()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        for property_ in ['band gap', 'atomic structure']:
            S.find_element_by_link_text('Define new property').click()
            S.find_element_by_name('property_name').send_keys(property_)
            property_link = reverse("materials:add_property")
            property_submit = S.find_element_by_xpath(
                f'//form[@action="{property_link}"]//button[@type="submit"]')
            property_submit.click()
        for unit in ['eV', 'Å']:
            S.find_element_by_link_text('Define new unit').click()
            S.find_element_by_name('unit_label').send_keys(unit)
            unit_link = reverse("materials:add_unit")
            unit_submit = S.find_element_by_xpath(
                f'//form[@action="{unit_link}"]//button[@type="submit"]')
            unit_submit.click()

    def test_normal_property(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        # Set system
        S.execute_script(
            f"selectized['select_system'][0].selectize.setValue(1)")
        # Set properties
        self.set_property('primary_property', 'band gap')
        self.set_unit('primary_unit', 'eV')
        S.find_element_by_id('id_is_figure').click()
        self.set_property('secondary_property', 'pressure')
        self.set_unit('secondary_unit', 'GPa')
        # General
        S.find_element_by_id('id_origin_of_data_1').click()
        S.find_element_by_id('id_sample_type_4').click()
        # Optional sections
        S.find_element_by_id('synthesis-button').click()
        S.find_element_by_id('id_starting_materials').send_keys(
            'starting material')
        S.find_element_by_id('id_product').send_keys('product')
        S.find_element_by_id('id_synthesis_description').send_keys(
            'description')
        S.find_element_by_id('id_synthesis_comment').send_keys('comment')
        S.find_element_by_id('experimental-button').click()
        S.find_element_by_id('id_experimental_method').send_keys('method')
        S.find_element_by_id('id_experimental_description').send_keys(
            'description')
        S.find_element_by_id('id_experimental_comment').send_keys(
            'exp comment')
        S.find_element_by_id('computational-button').click()
        S.find_element_by_id('id_code').send_keys('abinit')
        S.find_element_by_id('id_level_of_theory').send_keys('DFT')
        S.find_element_by_id('id_xc_functional').send_keys('PBE')
        S.find_element_by_id('id_k_point_grid').send_keys('4x4x4')
        S.find_element_by_id('id_level_of_relativity').send_keys(
            'non-relativistic')
        S.find_element_by_id('id_basis_set_definition').send_keys(
            'pseudopotentials')
        S.find_element_by_id('id_numerical_accuracy').send_keys('1 meV/atom')
        S.find_element_by_id('id_computational_comment').send_keys(
            'comp comment')
        # Data
        S.find_element_by_id('id_crystal_system_2_1').click()
        S.find_element_by_id('id_subset_datapoints_1').send_keys('''
        14.4 -3.7
        16.7(1.3) 10.4
        ''')
        submit_link = reverse("materials:submit_data")
        S.find_element_by_xpath(
            f'//form[@action="{submit_link}"]//button[@type="submit"]').click()
        # Second data set based on the first one
        last_pk = models.Dataset.objects.last().pk
        S.find_element_by_id('prefill').send_keys(last_pk)
        S.find_element_by_id('prefill-button').click()
        S.find_element_by_id('id_related_data_sets').send_keys(last_pk)
        self.set_property('primary_property', 'dielectric constant')
        S.execute_script(
            f"selectized['primary_unit'][0].selectize.clear()")
        S.find_element_by_id('id_is_figure').click()
        S.find_element_by_id('id_origin_of_data_0').click()
        S.find_element_by_id('computational-button').click()
        S.find_element_by_id('id_subset_datapoints_1').send_keys('7.8')
        S.find_element_by_xpath(
            f'//form[@action="{submit_link}"]//button[@type="submit"]').click()
        # View latest data set
        S.find_element_by_xpath(
            '//a[starts-with(@href, "/materials/dataset")]').click()
        S.find_element_by_link_text('See all related data').click()
        # View the other data set
        S.find_element_by_xpath(
            f'//button[@data-target="#synthesis-body-{last_pk}"]').click()
        S.find_element_by_xpath(
            f'//button[@data-target="#experimental-body-{last_pk}"]').click()
        S.find_element_by_xpath(
            f'//button[@data-target="#computational-body-{last_pk}"]').click()
        for test_string in ('starting material',
                            'product',
                            'description',
                            'abinit',
                            'DFT',
                            'PBE',
                            'non-relativistic',
                            '1 meV/atom'):
            S.find_element_by_xpath(
                f'//div[contains(@class, "card-body")]/'
                f'p[contains(text(), "{test_string}")]')
        for test_string in ('comment', 'exp comment', 'comp comment'):
            S.find_element_by_xpath(f'//div[contains(@class, "card-body")]/'
                                    f'p/i[contains(text(), "{test_string}")]')
        S.find_element_by_link_text('Show table').click()
        S.find_element_by_xpath(
            f'//div[contains(@class, "card-body")]/table/'
            f'tbody/tr/td[contains(text(), "16.7 (±1.3)")]')

    def test_atomic_structure(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        # Set system
        S.execute_script(
            f"selectized['select_system'][0].selectize.setValue(1)")
        # Set property
        pk = models.Property.objects.get(name='atomic structure').pk
        S.execute_script(
            f"selectized['primary_property'][0].selectize.setValue({pk})")
        # Set unit
        pk = models.Unit.objects.get(label='Å').pk
        S.execute_script(
            f"selectized['primary_unit'][0].selectize.setValue({pk})")
        # Input first atomic structure
        S.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        S.find_element_by_id('id_lattice_constant_a_1').send_keys('9.64')
        S.find_element_by_id('id_lattice_constant_b_1').send_keys('11.2(3)')
        S.find_element_by_id('id_lattice_constant_c_1').send_keys('16.4935')
        S.find_element_by_id('id_lattice_constant_alpha_1').send_keys('99.2')
        S.find_element_by_id('id_lattice_constant_beta_1').send_keys('104.6')
        S.find_element_by_id('id_lattice_constant_gamma_1').send_keys('90')
        S.find_element_by_id('id_atomic_coordinates_1').send_keys('''
        lattice_vector 5 0 0
        lattice_vector 0 5 0
        lattice_vector 0 0 5
        atom_frac 0 0 0 Al
        atom_frac 0.5 0.5 0.5 Ga
        ''')
        # Increase number of subsets to two
        S.find_element_by_id('id_number_of_subsets').send_keys(Keys.ARROW_UP)
        # Input second atomic structure
        S.find_element_by_id('id_crystal_system_6_2').click()
        S.find_element_by_id('id_lattice_constant_a_2').send_keys('8.0')
        S.find_element_by_id('id_lattice_constant_b_2').send_keys('10(1)')
        S.find_element_by_id('id_lattice_constant_c_2').send_keys('15')
        S.find_element_by_id('id_lattice_constant_alpha_2').send_keys('90')
        S.find_element_by_id('id_lattice_constant_beta_2').send_keys('95')
        S.find_element_by_id('id_lattice_constant_gamma_2').send_keys('98')
        # Create fixed properties
        S.find_element_by_id('add-fixed-property-2').click()
        S.find_element_by_id('add-fixed-property-2').click()
        # Test submit
        submit_link = reverse("materials:submit_data")
        S.find_element_by_xpath(
            f'//form[@action="{submit_link}"]//button[@type="submit"]').click()
        # Fill in fixed properties
        pk = models.Property.objects.get(name='pressure').pk
        S.execute_script(
            f"selectized['fixed_property_2_0'][0].selectize.setValue({pk})")
        pk = models.Unit.objects.get(label='Å').pk
        S.execute_script(
            f"selectized['fixed_unit_2_0'][0].selectize.setValue({pk})")
        S.find_element_by_id('id_fixed_value_2_1').send_keys('9(3)')
        pk = models.Property.objects.get(name='band gap').pk
        S.execute_script(
            f"selectized['fixed_property_2_1'][0].selectize.setValue({pk})")
        pk = models.Unit.objects.get(label='eV').pk
        S.execute_script(
            f"selectized['fixed_unit_2_1'][0].selectize.setValue({pk})")
        S.find_element_by_id('id_fixed_value_2_0').send_keys('4.5')
        # Create data set
        submit_link = reverse("materials:submit_data")
        S.find_element_by_xpath(
            f'//form[@action="{submit_link}"]//button[@type="submit"]').click()
        # View data set
        S.find_element_by_xpath(
            '//a[starts-with(@href, "/materials/dataset")]').click()
        S.find_element_by_class_name('expand-hide-button').click()
        S.find_element_by_xpath(
            '//table[contains(@class, "table-atomic-coordinates")]/'
            'tr/td[contains(text(), "lattice_vector")]')
        S.find_element_by_xpath(
            '//table[contains(@class, "table-atomic-coordinates")]/'
            'tr/td[contains(text(), "Ga")]')
        S.find_element_by_class_name('delete_button').click()
        S.switch_to_alert().accept()
        S.get(self.live_server_url + reverse('materials:add_data'))
        self.assertEqual(models.Dataset.objects.count(), 1)
