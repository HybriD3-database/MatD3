# This file is covered by the BSD license. See LICENSE in the root directory.
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
import os
import shutil

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import LiveServerTestCase
from django.test import TestCase

from . import models
from accounts.tests import USERNAME
from accounts.tests import PASSWORD

from mainproject import settings

settings.MEDIA_ROOT += '_tests'

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

    def test_verifiction(self):
        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)
        dataset = models.Dataset.objects.last()
        self.client.force_login(user1)
        verify_url = reverse('materials:verify_dataset', kwargs={
            'pk': dataset.pk, 'view_name': 'dataset',
        })
        self.client.post(verify_url)
        self.client.force_login(user2)
        self.client.post(verify_url)
        self.assertEqual(dataset.verified_by.count(), 2)
        redirect = self.client.post(verify_url)
        self.assertEqual(dataset.verified_by.count(), 1)
        response = self.client.get(redirect.url)
        self.assertContains(response, 'Verified')


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
        if settings.SELENIUM_DRIVER == 'firefox':
            cls.selenium = webdriver.Firefox(service_log_path='/dev/null')
        elif settings.SELENIUM_DRIVER in ['chrome', 'chromium']:
            cls.selenium = webdriver.Chrome(service_log_path='/dev/null')
        cls.selenium.maximize_window()
        cls.selenium.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def tearDown(self):
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

    def login(self):
        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_link_text('Login').click()
        self.selenium.find_element_by_name('username').send_keys(USERNAME)
        self.selenium.find_element_by_name('password').send_keys(PASSWORD)
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

    def selectize_set(self, selectize_name, name=None):
        """Shortcut for setting units with selectize"""
        if name:
            if 'reference' in selectize_name:
                pk = models.Reference.objects.get(year=name).pk
            elif 'system' in selectize_name:
                pk = models.System.objects.get(compound_name=name).pk
            elif 'property' in selectize_name:
                pk = models.Property.objects.get(name=name).pk
            elif 'unit' in selectize_name:
                pk = models.Unit.objects.get(label=name).pk
        else:
            pk = 0
        self.selenium.find_element_by_id(f'id_{selectize_name}-selectized')
        self.selenium.execute_script(
            f"selectized['{selectize_name}'][0].selectize.setValue({pk})")

    def test_properties_and_units(self):
        self.login()
        models.Dataset.objects.all().delete()
        models.Property.objects.all().delete()
        models.Unit.objects.all().delete()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        # Wait for all dropdowns to finish loading
        S.find_element_by_id('id_secondary_unit-selectized')
        # New property via primary property
        self.selectize_set('primary_property')
        S.find_element_by_id('id_name').send_keys('band gap')
        S.find_element_by_xpath(
            '//div[@id="new-property-card"]//button[@type="submit"]').click()
        # New unit via secondary unit
        S.find_element_by_id('id_two_axes').click()
        self.selectize_set('secondary_unit')
        S.find_element_by_id('id_label').send_keys('eV')
        S.find_element_by_xpath(
            '//div[@id="new-unit-card"]//button[@type="submit"]').click()
        # New property via first fixed property
        S.find_element_by_id('add-fixed-property-1').click()
        self.selectize_set('fixed_property_1_0')
        S.find_element_by_id('id_name').send_keys('atomic structure')
        S.find_element_by_xpath(
            '//div[@id="new-property-card"]//button[@type="submit"]').click()
        # New unit via fixed unit of subset 2
        S.find_element_by_id('id_number_of_subsets').send_keys(Keys.ARROW_UP)
        S.find_element_by_id('add-fixed-property-2').click()
        self.selectize_set('fixed_unit_2_1')
        S.find_element_by_id('id_label').send_keys('Å')
        S.find_element_by_xpath(
            '//div[@id="new-unit-card"]//button[@type="submit"]').click()

    def test_publication_material(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        # Wait for all dropdowns to finish loading
        S.find_element_by_id('id_secondary_unit-selectized')
        # New reference
        self.selectize_set('select_reference')
        S.find_element_by_id('first-name-1').send_keys('first 1')
        S.find_element_by_id('last-name-1').send_keys('last 1')
        S.find_element_by_xpath(
            '//div[@id="institution-1"]//input').send_keys('institution 1')
        S.find_element_by_id('add-more-authors-btn').click()
        S.find_element_by_id('first-name-2').send_keys('First 2')
        S.find_element_by_id('last-name-2').send_keys('last 2')
        S.find_element_by_xpath(
            '//div[@id="institution-2"]//input').send_keys('institution 2')
        S.find_element_by_id('id_title').send_keys('article title')
        S.find_element_by_id('id_journal').send_keys('journal name')
        S.find_element_by_id('id_vol').send_keys('1')
        S.find_element_by_id('id_pages_start').send_keys('1')
        S.find_element_by_id('id_pages_end').send_keys('2')
        S.find_element_by_id('id_year').send_keys('2000')
        S.find_element_by_id('id_doi_isbn').send_keys('doi')
        S.find_element_by_xpath(
            '//div[@id="new-reference-card"]//button[@type="submit"]').click()
        S.find_element_by_xpath('//div[@id="dynamic-messages"]//div')
        self.assertEqual(models.Reference.objects.count(), 2)
        # New system
        self.selectize_set('select_system')
        S.find_element_by_id('id_compound_name').send_keys('new compound')
        S.find_element_by_id('id_formula').send_keys('H2O')
        S.find_element_by_id('id_organic').send_keys('H')
        S.find_element_by_id('id_inorganic').send_keys('O')
        S.find_element_by_id('id_group').send_keys('OH2')
        S.find_element_by_id('id_description').send_keys('description')
        S.find_element_by_xpath(
            '//div[@id="new-system-card"]//button[@type="submit"]').click()
        S.find_element_by_xpath('//div[@id="dynamic-messages"]'
                                '//div[contains(text(), "compound")]')
        self.assertEqual(models.System.objects.count(), 2)

    def test_normal_property(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        S.find_element_by_id('id_secondary_unit-selectized')
        # Set reference
        self.selectize_set('select_reference', '2000')
        # Set properties
        self.selectize_set('primary_property', 'band gap')
        self.selectize_set('primary_unit', 'eV')
        S.find_element_by_id('id_is_figure').click()
        self.selectize_set('secondary_property', 'pressure')
        self.selectize_set('secondary_unit', 'GPa')
        # Set system
        S.execute_script(
            f"selectized['select_system'][0].selectize.setValue(1)")
        # General
        S.find_element_by_id('id_origin_of_data_1').click()
        S.find_element_by_id('id_sample_type_4').click()
        S.find_element_by_id('id_space_group').send_keys('F222')
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
        self.assertEqual(
            models.Dataset.objects.last().space_group, 'F222')
        # Second data set based on the first one
        last_pk = models.Dataset.objects.last().pk
        S.find_element_by_id('prefill').send_keys(last_pk)
        S.find_element_by_id('prefill-button').click()
        S.find_element_by_id('id_related_data_sets').send_keys(last_pk)
        self.selectize_set('primary_property', 'dielectric constant')
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
        sleep(0.2)
        S.find_element_by_xpath(
            f'//button[@data-target="#experimental-body-{last_pk}"]').click()
        sleep(0.2)
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
        # Test presence of all fields in computational details
        comp = models.ComputationalDetails.objects.first()
        self.assertEqual(comp.code, 'abinit')
        self.assertEqual(comp.level_of_theory, 'DFT')
        self.assertEqual(comp.xc_functional, 'PBE')
        self.assertEqual(comp.k_point_grid, '4x4x4')
        self.assertEqual(comp.level_of_relativity, 'non-relativistic')
        self.assertEqual(comp.basis_set_definition, 'pseudopotentials')
        self.assertEqual(comp.numerical_accuracy, '1 meV/atom')

    def test_atomic_structure(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        S.find_element_by_id('id_secondary_unit-selectized')
        # Set reference
        self.selectize_set('select_reference', '2000')
        # Set property and unit
        self.selectize_set('primary_property', 'atomic structure')
        self.selectize_set('primary_unit', 'Å')
        # Set system
        S.execute_script(
            f"selectized['select_system'][0].selectize.setValue(1)")
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
        self.selectize_set('fixed_property_2_0', 'pressure')
        self.selectize_set('fixed_unit_2_0', 'Å')
        S.find_element_by_id('id_fixed_value_2_1').send_keys('9(3)')
        self.selectize_set('fixed_property_2_1', 'band gap')
        self.selectize_set('fixed_unit_2_1', 'eV')
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
        S.find_element_by_class_name('delete-button').click()
        S.switch_to_alert().accept()
        S.get(self.live_server_url + reverse('materials:add_data'))
        self.assertEqual(models.Dataset.objects.count(), 1)

    def test_phase_transition(self):
        self.login()
        S = self.selenium
        S.get(self.live_server_url + reverse('materials:add_data'))
        S.find_element_by_id('id_secondary_unit-selectized')
        # Set reference
        self.selectize_set('select_reference', '2000')
        # Set property and unit
        self.selectize_set('primary_property', 'phase transition temperature')
        self.selectize_set('primary_unit', 'K')
        # Set system
        S.execute_script(
            f"selectized['select_system'][0].selectize.setValue(1)")
        # Input data
        S.find_element_by_id(
            'id_phase_transition_space_group_initial_1').send_keys('C1')
        S.find_element_by_id(
            'id_phase_transition_space_group_final_1').send_keys('C2')
        S.find_element_by_id(
            'id_phase_transition_direction_1').send_keys('increasing')
        S.find_element_by_id(
            'id_phase_transition_hysteresis_1').send_keys('none')
        S.find_element_by_id(
            'id_phase_transition_value_1').send_keys('300...301')
        # Create data set
        submit_link = reverse("materials:submit_data")
        S.find_element_by_xpath(
            f'//form[@action="{submit_link}"]//button[@type="submit"]').click()
        # Test if the temperature range was correctly captured
        pt_instance = models.PhaseTransition.objects.last()
        self.assertEqual(pt_instance.value, 300)
        self.assertEqual(pt_instance.upper_bound, 301)
