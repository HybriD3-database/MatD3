# This file is covered by the BSD license. See LICENSE in the root directory.
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def tooltip(value):
    value = escape(value)
    return mark_safe('<i class="fa fa-question-circle tooltip-container">'
                     '<span class="tooltiptext">' + value + '</span></i>')


@register.inclusion_tag('materials/input_field.html')
def input_field(field, inline=False):
    return {'field': field, 'inline': inline}

@register.filter()
def get_element_dict_value(element_dict, key):
    #return '6'
    return element_dict.get(key, '')

@register.filter()
def sort_stoichiometry_elements(elements, element_dict):
    # Use .get() safely and ensure that if element is missing, it defaults to 0
    return sorted(elements, key=lambda x: element_dict.get(x.element, 0))  # Default to 0 if element is missing

