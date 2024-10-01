# This file is covered by the BSD license. See LICENSE in the root directory.
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

from . import models

from django.db.models.signals import post_save
from .models import System, System_Stoichiometry, Stoichiometry_Elements
import re


def parse_formula(formula):
    tokens = re.findall(r"([A-Z][a-z]?|\(|\)|\d+)", formula)
    stack = [{}]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "(":
            stack.append({})
            i += 1
        elif token == ")":
            top = stack.pop()
            i += 1
            # Check if there is a multiplier
            if i < len(tokens) and tokens[i].isdigit():
                multiplier = int(tokens[i])
                i += 1
            else:
                multiplier = 1
            for element, count in top.items():
                stack[-1][element] = stack[-1].get(element, 0) + count * multiplier
        elif re.match(r"[A-Z][a-z]?$", token):
            element = token
            i += 1
            if i < len(tokens) and tokens[i].isdigit():
                count = int(tokens[i])
                i += 1
            else:
                count = 1
            stack[-1][element] = stack[-1].get(element, 0) + count
        else:
            i += 1
    return stack[0]


@receiver(post_save, sender=System)
def create_stoichiometry_entries(sender, instance, created, **kwargs):
    if created:
        formula = instance.formula
        # Updated regex pattern to match decimals
        element_pattern = r"([A-Z][a-z]*)(\d*(?:\.\d+)?)"
        elements = re.findall(element_pattern, formula)
        stoichiometry_str = ",".join([f"{el}:{count or 1}" for el, count in elements])
        stoichiometry = System_Stoichiometry.objects.create(
            system=instance, stoichiometry=stoichiometry_str
        )
        for el, count in elements:
            Stoichiometry_Elements.objects.create(
                system_stoichiometry=stoichiometry,
                element=el,
                string_value=str(count or "1"),
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
