import sys
import os
import django

from mainproject.settings.base import MEDIA_ROOT, MEDIA_URL
from materials.plotting.pl_plotting import plotpl
from materials.plotting.bs_plotting import prep_and_plot

directory = os.getcwd()
sys.path.append(directory)
django.setup()

from materials.models import ExcitonEmission, BandStructure

# list out the location of all unplotted EE FILES
emissions = ExcitonEmission.objects.filter(plotted=False)

for emission in emissions:
    if emission.pl_file:
        pl_file_loc = MEDIA_ROOT + "/uploads/" + str(emission.pl_file).split("/")[1]
        plotpl(pl_file_loc)
        emission.plotted = True
        emission.save()
        print("{} plotted and saved".format(str(emission)))

band_structures = BandStructure.objects.filter(plotted=False)

for band in band_structures:
    folder_loc = band.folder_location
    if os.path.isdir(folder_loc):
        prep_and_plot(folder_loc)
        band.plotted = True
        band.save()
        print("{} plotted and saved".format(folder_loc))
