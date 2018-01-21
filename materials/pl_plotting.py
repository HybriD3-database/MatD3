import matplotlib.pyplot as plt
import csv
import sys
import mpld3
from mpld3 import plugins
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

css = """
.mpld3-tooltip {
    position: relative;
    display: inline-block;
}

.mpld3-tooltip .tooltiptext {
    width: 150px;
    height: 40px;
    background-color: #ececec;
    font-size: 11px;
    text-align: center;
    padding: 5px 0;
    border-radius: 5px;
}

.mpld3-tooltip .tooltiptext::after {
    content: " ";
    position: absolute;
    top: 100%; /* At the bottom of the tooltip */
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #ececec transparent transparent transparent;
}
"""
# give parameters in inches
# filename = sys.argv[1]
width, height = (5, 4)
tooltipwidth, tooltipheight = (150, 40)
x_label, y_label = ('Wavelength/nm', 'Exciton Emission')
title = "Photoluminescence"
x = []
y = []

fig = plt.figure(figsize=(width,height))
ax = fig.add_subplot(111)
ax.grid(True, alpha=0.7)

def plotpl(filename):
    with open(filename, 'r') as csvfile:
        plots =  csv.reader(csvfile, delimiter=',')
        headers = next(plots)
        # print head
        for row in plots:
            x.append(row[0])
            y.append(row[1])
            # print row
    peak_intensity = y.index(max(y))
    exciton_peak = x[peak_intensity]
    # print "max is at", exciton_peak, "nm"
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title, size=20)
    points = ax.plot(x,y, '-', color='b', lw=2, alpha=.7)
    points = ax.plot(x,y, 'o', color='b', ms=8, alpha=.7)

    # print points[0]
    labels = []
    for i,j in zip(x,y):
        label = '<div class="tooltiptext">'
        label += '{2}: {1} <br> {3}: {0}'.format(i, j, y_label, x_label)
        label += '</div>'
        labels.append(label)

    tooltip = plugins.PointHTMLTooltip(points[0], labels, hoffset=-tooltipwidth/2, voffset=-tooltipheight, css=css)

    plugins.connect(fig, tooltip)

    save_name = "{}.html".format(filename.split(".")[0])
    mpld3.save_html(fig, save_name)
    # mpld3.fig_to_html(plt_figure)
