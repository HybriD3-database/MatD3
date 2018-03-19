import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import csv
import sys
import mpld3
import numpy as np
from mpld3 import plugins
from matplotlib import rcParams
from scipy.interpolate import interp1d
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
def plotpl(filename):
    # give parameters in inches
    # filename = sys.argv[1]
    width, height = (5, 4)
    tooltipwidth, tooltipheight = (150, 40)
    x_label, y_label = ('Wavelength/nm', 'Intensity/arb. units')
    title = "Photoluminescence"
    x = []
    y = []

    fig = plt.figure(figsize=(width,height))
    ax = fig.add_subplot(111)
    ax.grid(True, alpha=0.7)
    with open(filename, 'r') as csvfile:
        plots =  csv.reader(csvfile, delimiter=',')
        headers = next(plots)
        # print head
        for row in plots:
            x.append(float(row[0]))
            y.append(float(row[1]))
            # print row


    minX, maxX = (min(x), max(x))
    # normalize y to 0 & 1
    # [(yVal-minY)/(maxY-minY) for yVal in y]
    y = np.array(y)
    maxY = y.max()

    peak_index = np.argmax(y)
    print("Peak index is: ", peak_index)


    # scale 1
    # minY = y[peak_index:].min()
    # print("minY is: ", minY)
    #
    # y = (y-minY)/(maxY-minY)

    # scale 2
    # minY = y.min()
    # rightY = y[peak_index:].min()
    # print("minY is: ", minY)
    #
    # scaleFactorY = (rightY-minY)/(maxY-minY) + 1
    # # set maxY-rightY = 1
    # # set
    # y = (y-minY)*scaleFactorY/(maxY-minY)

    # scale 3
    minY = y.min()
    print("minY is: ", minY)

    y = np.around((y-minY)/(maxY-minY), decimals=3)

    min_index = np.argmin(y)
    print(min_index)
    # reassign normalized max and min
    maxY, minY = (1.0, 0.0)
    # peak_intensity = y.index(maxY)
    # exciton_peak = x[peak_intensity]
    # print "max is at", exciton_peak, "nm"
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title, size=20)

    deltaX = maxX/10
    deltaY = maxY/10
    minXlim = int((minX-deltaX)/50)*50
    maxXlim = int((maxX+deltaX)/50+1)*50
    ax.set_xticks(np.linspace(int((minX-deltaX)/50)*50, int((maxX+deltaX)/50+1)*50, 11))
    ax.set_yticks(np.linspace(int((minY)*100)/float(100), 1, 11))
    ax.set_xlim(minXlim, maxXlim)
    ax.set_ylim(float(minY-deltaY),float(maxY+deltaY))

    # start cubic spline
    # f = interp1d(x, y, kind='cubic')
    # x_new = np.linspace(minX, maxX, num=800, endpoint=True)
    points = ax.plot(x,y, '-', color='b', lw=2, alpha=.7)
    # points = ax.plot(x_new, f(x_new), '-', color='b', lw=2, alpha=.7)
    points = ax.plot(x,y, 'o', color='b', ms=7, alpha=.7)

    # add two horizontal lines touching min and max
    # print(x[peak_index])
    # print(maxXlim)
    # print(x[min_index])
    # Xlim = maxXlim - minXlim
    # ax.axhline(y=1, xmin=(x[peak_index]-minXlim)/Xlim, ls='--', color='r')
    # ax.axhline(y=0, xmin=(x[min_index]-minXlim)/Xlim, ls='--', color='r')

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
    # filename = "{}.png".format(filename.split(".")[0])
    # plt.savefig(filename, dpi = 300, bbox_inches='tight')
    mpld3.save_html(fig, save_name)
    plt.close()
    # mpld3.fig_to_html(plt_figure)
