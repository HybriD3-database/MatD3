from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase

from . import models

User = get_user_model()
dataset_template = models.Dataset(visible=True,
                                  is_figure=False,
                                  is_experimental=True,
                                  dimensionality=3,
                                  sample_type=models.Dataset.SINGLE_CRYSTAL,
                                  crystal_system=models.Dataset.TRICLINIC)
system_template = models.System(compound_name='MAPbI3',
                                formula='(CH3NH3)PbI3',
                                group='MAPI',
                                organic='CH3NH3',
                                inorganic='PbI3')


class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create()
        system = deepcopy(system_template)
        system.save()
        dataset = deepcopy(dataset_template)
        dataset.created_by = cls.user
        dataset.updated_by = cls.user
        dataset.system = system
        dataset.primary_property = models.Property.objects.create(
            created_by=cls.user, name='band gap')
        dataset.save()
        dataset.pk = None
        dataset.primary_property = models.Property.objects.create(
            created_by=cls.user, name='absorption coefficient')
        dataset.save()
        dataset.pk = None
        dataset.primary_property = models.Property.objects.create(
            created_by=cls.user, name='atomic structure')
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
