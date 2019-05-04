"""Helper functions for this project."""
import functools
import io
import operator
import matplotlib
import numpy
import re

from django.db.models import Q
from django.core.files.uploadedfile import SimpleUploadedFile

from . import models


def atomic_coordinates_as_json(pk):
    """Get atomic coordinates from the atomic structure list.

    The first six entries of the "atomic structure" property are the
    lattice constants and angles. These need to be skipped when
    fetching for the lattice vectors and atomic coordinates.

    """
    series = models.Dataseries.objects.get(pk=pk)
    vectors = models.NumericalValue.objects.filter(
        datapoint__dataseries=series).filter(
           datapoint__symbols__isnull=True).order_by(
               'datapoint_id', 'counter')
    data = {'vectors':
            [[x.formatted('.10g') for x in vectors[:3]],
             [x.formatted('.10g') for x in vectors[3:6]],
             [x.formatted('.10g') for x in vectors[6:9]]]}
    # Here counter=1 filters out the first six entries
    symbols = models.Symbol.objects.filter(
        datapoint__dataseries=series).filter(counter=1).order_by(
            'datapoint_id').values_list('value', flat=True)
    coords = models.NumericalValue.objects.filter(
        datapoint__dataseries=series).filter(
            datapoint__symbols__counter=1).select_related('error').order_by(
                'counter', 'datapoint_id')
    tmp = models.Symbol.objects.filter(
        datapoint__dataseries=series).annotate(
            num=models.models.Count('datapoint__symbols')).filter(
                num=2).first()
    if tmp:
        data['coord-type'] = tmp.value
    data['coordinates'] = []
    N = int(len(coords)/3)
    for symbol, coord_x, coord_y, coord_z in zip(
            symbols, coords[:N], coords[N:2*N], coords[2*N:3*N]):
        data['coordinates'].append((symbol,
                                    coord_x.formatted('.9g'),
                                    coord_y.formatted('.9g'),
                                    coord_z.formatted('.9g')))
    return data


def plot_band_structure(k_labels, files, dataset):
    """Generate two images of the band structure.

    k_labels: string(n,2)
       List of k-point pairs. Example: [['X', 'L'], ['L', 'B'], ...]
    files:
        List of file names containing the band energies.

    """
    from matplotlib import pyplot
    matplotlib.use('Agg')
    ENERGY_FULL_MIN = -8
    ENERGY_FULL_MAX = 8
    ENERGY_SMALL_MIN = -2
    ENERGY_SMALL_MAX = 5
    HELPER_LINE_WIDTH = 0.2
    # Compress k_labels into a 1-dim list. If the endpoint of a pairs
    # differs from the beginning of the next pair, use both labels
    # with a "|" in between.
    k_labels_reduced = (len(k_labels)+1)*['']
    k_labels_reduced[0] = k_labels[0][0]
    for ik in range(len(k_labels)):
        if ik < len(k_labels)-1 and k_labels[ik][1] != k_labels[ik+1][0]:
            k_labels_reduced[ik+1] = f'{k_labels[ik][1]}|{k_labels[ik+1][0]}'
        else:
            k_labels_reduced[ik+1] = k_labels[ik][1]
    # Use the gamma symbol where appropriate
    for ik in range(len(k_labels_reduced)):
        k_labels_reduced[ik] = re.sub('[Gg](?:amma)?', 'Γ',
                                      k_labels_reduced[ik])
    # A segment location is where a k-point should be displayed
    segment_locations = numpy.empty(len(files)+1, dtype=int)
    segment_locations[0] = 0
    # Read in all data points (energies) next
    data_raw = []
    n_kpoints = []
    fermi_energy = -1e10
    for i_segment, file_ in enumerate(files):
        lines = file_.readlines()
        n_kpoints.append(len(lines))
        # If the first k-point is the same as the last k-point of
        # the previous segment, it needs to be skipped.
        skip_first = i_segment > 0 and '|' not in k_labels_reduced[i_segment]
        if skip_first:
            n_kpoints[-1] -= 1
            i_skip = 1
        else:
            i_skip = 0
        segment_locations[i_segment+1] = sum(n_kpoints)-1
        # Determine the number of bands from the first line of the
        # first file. This is assumed to be constant througout.
        if i_segment == 0:
            words = lines[0].split()
            n_bands = int(len(words[5:])/2)
            min_index = int(1e10)
            max_index = 0
        data_raw.append(numpy.empty([n_kpoints[-1], n_bands]))
        for i_kpoint in range(n_kpoints[-1]):
            words = lines[i_kpoint+i_skip].split()
            for i_band in range(n_bands):
                band_energy = float(words[5+2*i_band])
                occupation = float(words[4+2*i_band])
                data_raw[-1][i_kpoint, i_band] = band_energy
                if occupation > 1e-10:
                    fermi_energy = max(fermi_energy, band_energy)
    for i_segment in range(len(data_raw)):
        data_raw[i_segment] -= fermi_energy
        for i_kpoint in range(n_kpoints[i_segment]):
            min_index = min(min_index, numpy.searchsorted(
                data_raw[i_segment][i_kpoint, :], ENERGY_FULL_MIN))
            max_index = max(max_index, numpy.searchsorted(
                data_raw[i_segment][i_kpoint, :], ENERGY_FULL_MAX))
        file_.close()
    # Reduce the full data because we are only interested in a small
    # energy window.
    n_bands_reduced = max_index - min_index
    data = numpy.empty([n_bands_reduced, sum(n_kpoints)])
    k_start = 0
    for i_segment in range(len(data_raw)):
        n_kpoints = data_raw[i_segment].shape[0]
        for i_kpoint in range(n_kpoints):
            data[:, k_start+i_kpoint] = (
                data_raw[i_segment][i_kpoint, min_index:max_index])
        k_start += n_kpoints
    # Transfer the data into the plot
    x_ticks = range(data.shape[1])
    ax = pyplot.axes()
    for i_band in range(data.shape[0]):
        ax.plot(x_ticks, data[i_band, :], color='blue', lw=1.0)
    # Set x-axis labels
    ax.xaxis.set_ticks_position('none')
    x_labels = len(x_ticks)*['']
    for i, loc in enumerate(segment_locations):
        x_labels[loc] = k_labels_reduced[i]
    pyplot.xticks(x_ticks, x_labels)
    ax.set_xlim(left=0, right=len(x_ticks))
    # Set y-axis label
    pyplot.ylabel('Energy, eV')
    # Draw some vertical and horizontal helper lines
    for segment_i in segment_locations:
        ax.axvline(x=segment_i, color='black', linestyle='--',
                   lw=HELPER_LINE_WIDTH)
    ax.axhline(y=0, color='black', linestyle='--', lw=HELPER_LINE_WIDTH)
    # Save to file
    ax.set_ylim(bottom=ENERGY_FULL_MIN, top=ENERGY_FULL_MAX)

    def save_plot(name):
        in_memory_object = io.BytesIO()
        pyplot.savefig(in_memory_object, format='png', bbox_inches='tight')
        f = SimpleUploadedFile(name, in_memory_object.getvalue())
        dataset.files.create(created_by=dataset.created_by, dataset_file=f)
        in_memory_object.close()

    save_plot('band_structure_full.png')
    ax.set_ylim(bottom=ENERGY_SMALL_MIN, top=ENERGY_SMALL_MAX)
    save_plot('band_structure_small.png')
    pyplot.close()


def makeCorrections(form):
    # alter user input if necessary
    try:
        temp = form.temperature
        if temp.endswith('K') or temp.endswith('C'):
            temp = temp[:-1].strip()
            form.temperature = temp
        return form
    except Exception:  # just in case
        return form


def getAuthorSearchResult(search_text):
    keyWords = search_text.split()
    results = models.System.objects.\
        filter(functools.reduce(operator.or_, (
            Q(synthesismethodold__reference__author__last_name__icontains=x)
            for x in keyWords)) | functools.reduce(operator.or_, (Q(
                    excitonemission__reference__author__last_name__icontains=x
            ) for x in keyWords)) | functools.reduce(operator.or_, (Q(
                bandstructure__reference__author__last_name__icontains=x
            ) for x in keyWords))).distinct()
    return results


def search_result(search_term, search_text):
    if search_term == 'formula':
        return models.System.objects.filter(
            Q(formula__icontains=search_text) |
            Q(group__icontains=search_text) |
            Q(compound_name__icontains=search_text)).order_by('formula')
    elif search_term == 'organic':
        return models.System.objects.filter(
            organic__icontains=search_text).order_by('organic')
    elif search_term == 'inorganic':
        return models.System.objects.filter(
            inorganic__icontains=search_text).order_by('inorganic')
    elif search_term == 'author':
        return getAuthorSearchResult(search_text)
    else:
        raise KeyError('Invalid search term.')
