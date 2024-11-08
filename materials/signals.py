# This file is covered by the BSD license. See LICENSE in the root directory.
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

from . import models

from django.db.models.signals import post_save
from .models import System, System_Stoichiometry, Stoichiometry_Elements
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import re


def parse_formula(formula):
    # Updated regex to include decimal numbers and fractions inside brackets
    token_pattern = r"([A-Z][a-z]?|\d+(\.\d+)?|\([\d\.]+(\/[\d\.]+)?\)|\{[\d\.]+(\/[\d\.]+)?\}|\[[\d\.]+(\/[\d\.]+)?\]|[\(\)\[\]\{\}])"
    tokens = re.findall(token_pattern, formula)
    # Flatten the tokens list
    tokens = [token[0] for token in tokens]
    if not tokens:
        return {}
    stack = [{}]
    bracket_stack = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in "([{":
            stack.append({})
            bracket_stack.append(token)
            i += 1
        elif token in ")]}":
            if not bracket_stack:
                raise ValueError("Unmatched closing bracket in formula")
            opening = bracket_stack.pop()
            expected_closing = {"(": ")", "[": "]", "{": "}"}[opening]
            if token != expected_closing:
                raise ValueError("Mismatched brackets in formula")
            top = stack.pop()
            i += 1
            multiplier = Decimal("1")
            if i < len(tokens) and (
                re.match(r"^\d+(\.\d+)?$", tokens[i])
                or re.match(r"^[\(\[\{][\d\.]+(\/[\d\.]+)?[\)\]\}]$", tokens[i])
            ):
                if re.match(r"^[\(\[\{][\d\.]+\/[\d\.]+[\)\]\}]$", tokens[i]):
                    # Handle fractions inside brackets
                    fraction = tokens[i][1:-1].split("/")
                    numerator = Decimal(fraction[0])
                    denominator = Decimal(fraction[1])
                    multiplier = numerator / denominator
                elif re.match(r"^[\(\[\{][\d\.]+[\)\]\}]$", tokens[i]):
                    # Handle decimal numbers inside brackets
                    multiplier = Decimal(tokens[i][1:-1])
                else:
                    # Handle plain numbers
                    multiplier = Decimal(tokens[i])
                i += 1
            for element, count in top.items():
                stack[-1][element] = (
                    stack[-1].get(element, Decimal("0")) + count * multiplier
                )
        elif re.match(r"^[A-Z][a-z]?$", token):
            element = token
            i += 1
            count = Decimal("1")
            if i < len(tokens) and (
                re.match(r"^\d+(\.\d+)?$", tokens[i])
                or re.match(r"^[\(\[\{][\d\.]+(\/[\d\.]+)?[\)\]\}]$", tokens[i])
            ):
                if re.match(r"^[\(\[\{][\d\.]+\/[\d\.]+[\)\]\}]$", tokens[i]):
                    # Handle fractions inside brackets
                    fraction = tokens[i][1:-1].split("/")
                    numerator = Decimal(fraction[0])
                    denominator = Decimal(fraction[1])
                    count = numerator / denominator
                elif re.match(r"^[\(\[\{][\d\.]+[\)\]\}]$", tokens[i]):
                    # Handle decimal numbers inside brackets
                    count = Decimal(tokens[i][1:-1])
                else:
                    # Handle plain numbers
                    count = Decimal(tokens[i])
                i += 1
            stack[-1][element] = stack[-1].get(element, Decimal("0")) + count
        else:
            i += 1
    if bracket_stack:
        raise ValueError("Unmatched opening bracket in formula")
    return stack[0]


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
