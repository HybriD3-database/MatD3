from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from materials import models

register = template.Library()


@register.filter()
def tooltip(value):
    value = escape(value)
    return mark_safe('<i class="fa fa-question-circle tooltip-container">'
                     '<span class="tooltiptext">' + value + '</span></i>')


@register.filter()
def datapoint(datapoint):
    primary_value = None
    secondary_value = None
    primary_error = None
    secondary_error = None
    for value in datapoint.numericalvalue_set.all():
        if value.value_type == models.NumericalValue.ACCURATE:
            value_str = str(value.value)
        elif value.value_type == models.NumericalValue.UPPER_BOUND:
            value_str = '<' + str(value.value)
        elif value.value_type == models.NumericalValue.LOWER_BOUND:
            value_str = '>' + str(value.value)
        elif value.value_type == models.NumericalValue.APPROXIMATE:
            value_str = '≈' + str(value.value)
        if value.qualifier == models.NumericalValue.PRIMARY:
            if value.value_type == models.NumericalValue.ERROR:
                primary_error = str(value.value)
            else:
                primary_value = value_str
        else:
            if value.value_type == models.NumericalValue.ERROR:
                secondary_error = str(value.value)
            else:
                secondary_value = value_str
    if primary_error:
        primary_value = primary_value + '±' + primary_error
    if secondary_error:
        secondary_value = secondary_value + '±' + secondary_error
    return primary_value, secondary_value
