import sys
import os
import django

from mainproject.settings.base import MEDIA_ROOT, MEDIA_URL
from materials.plotting.pl_plotting import plotpl
from materials.plotting.bs_plotting import prep_and_plot

directory = os.getcwd()
sys.path.append(directory)
os.environ['DJANGO_SETTINGS_MODULE'] = 'mainproject.settings.dev'
django.setup()

from materials.models import ExcitonEmission, BandStructure

# list out the location of all unplotted EE FILES
emissions = ExcitonEmission.objects.filter(plotted=False)
entries = [str(e.pl_file).split("/")[1] for e in emissions]

count = 0
while count < len(emissions):
    pl_file_loc = MEDIA_ROOT + "/uploads/" + entries[count]
    plotpl(pl_file_loc)
    emissions[count].plotted = True
    emissions[count].save()
    print("{} plotted and saved".format(emissions[count]))
    count += 1

band_structures = BandStructure.objects.filter(plotted=False)
entries = [str(bs.folder_location) for bs in band_structures]

count = 0
while count < len(band_structures):
    prep_and_plot(entries[0])
    band_structures[count].plotted = True
    band_structures[count].save()
    print("{} plotted and saved".format(band_structures[count]))
    count += 1
