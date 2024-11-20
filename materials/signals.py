# This file is covered by the BSD license. See LICENSE in the root directory.
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

from . import models

from django.db.models.signals import post_save
from .models import System, System_Stoichiometry, Stoichiometry_Elements
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import re
from .utils import parse_formula


@receiver(post_save, sender=System)
def create_stoichiometry_entries(sender, instance, created, **kwargs):
    if created:
        formula = instance.formula
        try:
            element_counts = parse_formula(formula)
        except Exception as e:
            # Handle parsing errors if necessary
            return

        # Create stoichiometry string with formatted counts
        stoichiometry_list = []
        for el, count in element_counts.items():
            if count == count.to_integral():
                count_str = str(count.to_integral())
            else:
                count_str = str(
                    count.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
                )
            stoichiometry_list.append(f"{el}:{count_str}")
        stoichiometry_str = ",".join(stoichiometry_list)

        stoichiometry = System_Stoichiometry.objects.create(
            system=instance, stoichiometry=stoichiometry_str
        )
        for el, count in element_counts.items():
            if count == count.to_integral():
                count_str = str(count.to_integral())
            else:
                count_str = str(
                    count.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
                )
            Stoichiometry_Elements.objects.create(
                system_stoichiometry=stoichiometry,
                element=el,
                string_value=count_str,
                float_value=float(count),
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
