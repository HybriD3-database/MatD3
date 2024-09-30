# This file is covered by the BSD license. See LICENSE in the root directory.
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

from . import models

from django.db.models.signals import post_save
from .models import System, System_Stoichiometry, Stoichiometry_Elements
import re


@receiver(post_save, sender=System)
def create_stoichiometry_entries(sender, instance, created, **kwargs):
    if created:
        # Example: assuming the system's formula is provided in the form 'C6H12O6'
        formula = (
            instance.formula
        )  # Use the system's formula field for stoichiometry parsing

        # Regular expression to extract elements and their counts (e.g., C6, H12, O6 from 'C6H12O6')
        element_pattern = r"([A-Z][a-z]*)(\d*)"
        elements = re.findall(element_pattern, formula)

        # Create the stoichiometry string in the format "C:6,H:12,O:6"
        stoichiometry_str = ",".join([f"{el}:{count or 1}" for el, count in elements])

        # Create System_Stoichiometry entry
        stoichiometry = System_Stoichiometry.objects.create(
            system=instance, stoichiometry=stoichiometry_str
        )

        # Create Stoichiometry_Elements entries
        for el, count in elements:
            Stoichiometry_Elements.objects.create(
                system_stoichiometry=stoichiometry,
                element=el,
                string_value=count or "1",
                float_value=float(count) if count else 1.0,
            )


@receiver(m2m_changed, sender=models.Dataset.linked_to.through)
def interconnect_all_links(sender, **kwargs):
    """Make linking of data sets transitive.

    If A is linked to B and B is linked to C then A and C should also
    be linked.

    """
    if kwargs["action"] == "post_add" and kwargs["pk_set"]:
        target_pk = list(kwargs["pk_set"])[0]
        direct_datasets = kwargs["instance"].linked_to.all()
        indirect_datasets = models.Dataset.objects.filter(linked_to__pk=target_pk)
        all_datasets = list(set(direct_datasets | indirect_datasets))
        for i in range(len(all_datasets)):
            dataset_i = all_datasets[i]
            for j in range(i + 1, len(all_datasets)):
                dataset_j = all_datasets[j]
                if dataset_j not in dataset_i.linked_to.all():
                    dataset_i.linked_to.add(dataset_j)
