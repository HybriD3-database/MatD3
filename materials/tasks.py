from background_task import background
from .plotting.bs_plotting import prep_and_plot

@background(schedule=1)
def bs_plot(location):
    prep_and_plot(location)
    print("Successful band structure plot!")
