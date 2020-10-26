"""Functions related to the MatD3/Qresp interface."""
import matplotlib
import os
import shutil

from . import models
from mainproject import settings

matplotlib.use('Agg')

from matplotlib import pyplot  # noqa


def create_static_files(request, dataset):
    # Create static files for Qresp
    qresp_loc = os.path.join(settings.MEDIA_ROOT,
                             f'qresp/dataset_{dataset.pk}')
    qresp_plot_title = (
        f'Generated from numerical data:\n{dataset.primary_property}')
    if dataset.primary_unit:
        qresp_plot_title += f', {dataset.primary_unit}'
    os.makedirs(qresp_loc)
    if dataset.primary_property.name == 'atomic structure':
        value_sets = []
        for subset in dataset.subsets.all():
            values_tmp = []
            for symbol, value, unit in subset.get_lattice_constants():
                values_tmp.append([symbol, value, unit])
            value_sets.append(values_tmp)
        values_transposed = []
        for i_values, values in enumerate(value_sets):
            for i_value in range(len(values)):
                symbol, value, unit = values[i_value]
                if len(value_sets) == 1:
                    values_transposed.append([symbol, value, unit])
                elif i_value == 0:
                    values_transposed.append(
                        [f'Subset {i_values+1}', symbol, value, unit])
                else:
                    values_transposed.append(['', symbol, value, unit])
        fig, ax = pyplot.subplots(
            figsize=(6, max(len(values_transposed)/4, 3)))
        ax.set_title(qresp_plot_title)
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        pyplot.table(cellText=values_transposed, loc='center')
        fig.tight_layout()
        pyplot.savefig(os.path.join(qresp_loc, 'figure.png'))
        pyplot.close()
    elif dataset.primary_property.name == 'band structure':
        bs_file_loc = os.path.join(
            settings.MEDIA_ROOT,
            f'uploads/dataset_{dataset.pk}/band_structure_full.png')
        shutil.copyfile(bs_file_loc, os.path.join(qresp_loc, 'figure.png'))
    elif dataset.primary_property.name.startswith('phase transition '):
        value_sets = []
        for subset in dataset.subsets.all():
            values_tmp = []
            pt = subset.phase_transitions.first()
            CS = models.Subset.CRYSTAL_SYSTEMS
            values_tmp.append(['Initial crystal system',
                               CS[subset.crystal_system][1]])
            if pt.crystal_system_final:
                values_tmp.append(['Final crystal system',
                                   CS[pt.crystal_system_final][1]])
            if pt.space_group_initial:
                values_tmp.append(['Initial space group',
                                   pt.space_group_initial])
            if pt.space_group_final:
                values_tmp.append(['Final space group', pt.space_group_final])
            if pt.direction:
                values_tmp.append(['Direction', pt.direction])
            if pt.hysteresis:
                values_tmp.append(['Hysteresis', pt.hysteresis])
            main_value = pt.formatted()
            if dataset.primary_unit:
                main_value += f' {dataset.primary_unit}'
            values_tmp.append(['Value', main_value])
            value_sets.append(values_tmp)
        values_transposed = []
        for i_values, values in enumerate(value_sets):
            for i_value in range(len(values)):
                label, value = values[i_value]
                if len(value_sets) == 1:
                    values_transposed.append([label, value])
                elif i_value == 0:
                    values_transposed.append(
                        [f'Subset {i_values+1}', label, value])
                else:
                    values_transposed.append(['', label, value])
        fig, ax = pyplot.subplots(
            figsize=(4, max(len(values_transposed)/4, 3)))
        ax.set_title(qresp_plot_title)
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        pyplot.table(cellText=values_transposed, loc='center')
        fig.tight_layout()
        pyplot.savefig(os.path.join(qresp_loc, 'figure.png'))
        pyplot.close()
    elif dataset.secondary_property:
        for subset in dataset.subsets.all():
            values = models.NumericalValue.objects.filter(
                datapoint__subset=subset).order_by(
                    'qualifier', 'datapoint__pk').values_list(
                        'value', flat=True)
            y_values = values[:len(values)//2]
            x_values = values[len(values)//2:len(values)]
            fixed_values = []
            for v in subset.fixed_values.all():
                fixed_values.append(
                    f'{v.physical_property} = {v.value} {v.unit}')
            sub_label = ''
            if fixed_values:
                sub_label = ', '.join(fixed_values)
            if subset.label:
                sub_label = subset.label + ' ' + sub_label
            pyplot.plot(x_values, y_values, '-o', linewidth=0.5, ms=3,
                        label=sub_label)
        pyplot.title(qresp_plot_title)
        if dataset.primary_unit:
            primary_unit_label = dataset.primary_unit.label
        else:
            primary_unit_label = ''
        pyplot.ylabel(f'{dataset.primary_property.name}, {primary_unit_label}')
        if dataset.secondary_unit:
            secondary_unit_label = dataset.secondary_unit.label
        else:
            secondary_unit_label = ''
        pyplot.xlabel(f'{dataset.secondary_property.name}, '
                      f'{secondary_unit_label}')
        pyplot.legend(loc='upper left')
        pyplot.savefig(os.path.join(qresp_loc, 'figure.png'))
        pyplot.close()
    else:
        value_sets = []
        for subset in dataset.subsets.all():
            value_sets.append(models.NumericalValue.objects.filter(
                datapoint__subset=subset).order_by(
                    'datapoint__pk').values_list('value', flat=True))
        values_transposed = []
        for i_values, values in enumerate(value_sets):
            for i_value, value in enumerate(values):
                if len(value_sets) == 1:
                    values_transposed.append([value])
                elif i_value == 0:
                    values_transposed.append([f'Subset {i_values+1}', value])
                else:
                    values_transposed.append(['', value])
        fig, ax = pyplot.subplots(
            figsize=(3, max(len(values_transposed)/4, 3)))
        ax.set_title(qresp_plot_title)
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')
        pyplot.table(cellText=values_transposed, loc='center')
        fig.tight_layout()
        pyplot.savefig(os.path.join(qresp_loc, 'figure.png'))
        pyplot.close()
