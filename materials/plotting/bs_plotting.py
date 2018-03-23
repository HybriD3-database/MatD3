#!/usr/bin/env python
from os import listdir, remove, rename, getcwd
from os.path import isfile, join
import os,sys

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

from pylab import *
from matplotlib import rcParams
from mpld3 import plugins
from numpy.linalg import *
from numpy import dot,cross,pi
from scipy.interpolate import spline

rcParams.update({'figure.autolayout': True})
rcParams['xtick.labelsize'] = 8
rcParams['ytick.labelsize'] = 8
rcParams['savefig.dpi'] = 500
rcParams['font.size'] = 10

path = "/".join([os.path.dirname(os.path.abspath(__file__)), "futura.ttf"])
font_prop = font_manager.FontProperties(fname=path)
# change these settings as required
LINES_ABOVE = 50
LINES_BELOW = 49
# set energies here
MIN_ENERGY = -7.5
MAX_ENERGY = 7.5

def count(input_band, num_bands):
    number = 0
    lines = 0
    with open(input_band, 'r') as fin:
        for line in fin.readlines():
            length = len(line)
            items = line.split()
            number += len(items)
            lines += 1
    return ((number-4*21)*num_bands, number/(2*lines)-2)

def get_all_energies(location):
    bandfiles = ["".join([location,"/",f]) for f in listdir(location)
                 if (f.startswith('band10') and f.endswith('.out'))]
    bandfiles.sort()
    # print(bandfiles)
    val_energies = []
    con_energies = []
    for band in bandfiles:
        val_energy, con_energy = get_energies(band)
        val_energies.append(val_energy)
        con_energies.append(con_energy)
    print("Min valence energies & max conduction energies:", max(val_energies), min(con_energies))
    return (max(val_energies), min(con_energies))

def get_energies(input_band):
    with open(input_band, 'r') as fin:
        lines = fin.readlines()
        val_energies = []
        con_energies = []
        for line in lines:
            items = line.split()
            # print(items)
            length = len(items)
            i = 4 #get the first electron state
            val_index = con_index = 0
            while(i < length-1):
                if(float(items[i]) < float(1)):
                    val_index = i-1
                    break
                i += 2
            # print(items[val_index])
            val_energies.append(float(items[val_index]))
            con_energies.append(float(items[val_index+2]))
            # print(val_energies, con_energies)
    return(max(val_energies), min(con_energies))

def get_indices(input_band, min_en, max_en):
    with open(input_band, 'r') as fin:
        line = fin.readline()
    items = line.split()
    length = len(items)
    i = 4 #get the first electron state
    low_index = min_index = hi_index = 0
    # print("Low energy:", min_en)
    # print("High energy:", max_en)
    while(i < length-1):
        if(float(items[i+1]) > float(min_en)):
            low_index = i
            break
        i += 2
    while(i < length-1):
        if(float(items[i]) < float(1)):
            min_index = i-2
            break
        i += 2
    while(i < length-1):
        if(float(items[i+1]) > float(max_en)):
            hi_index = i
            break
        i += 2
    band_gap = float(items[min_index+3]) - float(items[min_index+1])
    offset = 0 - float(items[min_index+1])
    # print ("low index, hi index = ", min_index, hi_index)
    # print ("min index, min e occ, min energy = ", min_index, items[min_index], items[min_index+1])
    # print ("val index, val e occ, val energy = ", min_index+2, items[min_index+2], items[min_index+3])
    # print ("low index, low e occ, low energy = ", low_index, items[low_index], items[low_index+1])
    # print ("hi index, hi e occ, hi energy = ", hi_index, items[hi_index], items[hi_index+1])
    # print ("band gap = ", band_gap)
    new_list = items[low_index:hi_index]
    low_energy = float(items[low_index+1]) + offset
    hi_energy = float(items[hi_index+1]) + offset
    return (low_index, hi_index, band_gap, offset, low_energy, hi_energy)

def resize_standardize(input_band, start_index, end_index, offset):
    output_file = "_tr.".join(input_band.split("."))
    fout = open(output_file, 'a')
    with open(input_band, 'r') as fin:
        lines = fin.readlines()
        for line in lines:
            length = len(line)
            items = line.split()
            i = start_index #get the first electron state
            end = end_index + 1
            fout.write(" ".join(items[0:4]) + " ")
            while(i < end):
                std_energy = float(items[i+1])+offset
                fout.write(items[i] + " ")
                fout.write(str(std_energy) + " ")
                i += 2
            fout.write("\n")
    fout.close()
    backup_name = "_bak.".join(input_band.split("."))
    rename(input_band, backup_name)
    rename(output_file, input_band)

def plotbs(location, lower, upper, band_gap):
    print_resolution = 500          # The DPI used for printing out images
    default_line_width = 0.5        # Change the line width of plotted bands and k-vectors, 1 is default
    font_size = 10                 # Change the font size.  12 is the default.
    should_spline = True            # Turn on spline interpolation for band structures NOT VERY WELL TESTED!
    output_x_axis = True            # Whether to output the x-axis (e.g. the e=0 line) or not
    spline_factor = 10              # If spline interpolation turned on, the sampling factor (1 is the original grid)
    maxdos_output = -1              # The maximum value of the DOS axis (a.k.a. x-axis) in the DOS
                                    # For zero or negative values, the script will use its default value, the maximum
                                    # value for the DOS in the energy window read in
    ########################

    # new settings added by xd24
    ylim_lower, ylim_upper = (lower, upper)
    width, height = (5, 4)
    tooltipwidth, tooltipheight = (150, 40)
    x_label, y_label = ('Lattice Positions', 'Energy/eV')
    title = "Band Structure"

    print("Plotting bands for FHI-aims!")
    print("============================")
    print()

    print("Reading lattice vectors from geometry.in ...")

    matplotlib.rcParams['lines.linewidth'] = default_line_width

    latvec = []

    CUSTOM_YLIM = False
    FERMI_OFFSET = False
    energy_offset = 0.0

    folder_loc = location
    # if len(sys.argv) >= 2:
    #     folder_loc = sys.argv[1]

    print("folder_loc: ", folder_loc)
    folder_name = folder_loc.split("/")[-1]
    print("folder_name: ", folder_name)
    def get_path(filename):
        # print("filename: ", filename)
        return os.path.join(folder_loc, filename)

    for line in open(get_path("geometry.in")):
        line = line.split("#")[0]
        words = line.split()
        if len(words) == 0:
            continue
        if words[0] == "lattice_vector":
            if len(words) != 4:
                raise Exception("geometry.in: Syntax error in line '"+line+"'")
            latvec += [ array(list(map(float,words[1:4]))) ]

    if len(latvec) != 3:
        raise Exception("geometry.in: Must contain exactly 3 lattice vectors")

    latvec = asarray(latvec)

    print("Lattice vectors:")
    for i in range(3):
        print(latvec[i,:])
    print()

    #HERE:  Calculate reciprocal lattice vectors
    rlatvec = []
    volume = (np.dot(latvec[0,:],np.cross(latvec[1,:],latvec[2,:])))
    rlatvec.append(array(2*pi*cross(latvec[1,:],latvec[2,:])/volume))
    rlatvec.append(array(2*pi*cross(latvec[2,:],latvec[0,:])/volume))
    rlatvec.append(array(2*pi*cross(latvec[0,:],latvec[1,:])/volume))
    rlatvec = asarray(rlatvec)

    #rlatvec = inv(latvec) Old way to calculate lattice vectors
    print("Reciprocal lattice vectors:")
    for i in range(3):
        print(rlatvec[i,:])
    print()

    ########################

    print("Reading information from control.in ...")

    PLOT_BANDS = False
    PLOT_DOS = False
    PLOT_DOS_SPECIES = False
    PLOT_DOS_ATOM = False
    PLOT_SOC = False # This is needed because there will only be one "spin" channel output,
                     # but collinear spin may (or may not) be turned on, so the "spin
                     # collinear" setting needs to be overridden

    species = []

    max_spin_channel = 1
    band_segments = []
    band_totlength = 0.0 # total length of all band segments

    for line in open(get_path("control.in")):
        words = line.split("#")[0].split()
        nline = " ".join(words)

        if nline.startswith("spin collinear") and not PLOT_SOC:
            max_spin_channel = 2

        if nline.startswith("calculate_perturbative_soc") or nline.startswith("include_spin_orbit") or nline.startswith("include_spin_orbit_sc"):
            PLOT_SOC = True
            max_spin_channel = 1

        if nline.startswith("output band"):
            if len(words) < 9 or len(words) > 11:
                raise Exception("control.in: Syntax error in line '"+line+"'")
            PLOT_BANDS = True
            start = array(list(map(float,words[2:5])))
            end = array(list(map(float,words[5:8])))
            # HERE:  Here is where we calculate path lengths
            length = norm(dot(rlatvec,end) - dot(rlatvec,start))
            band_totlength += length
            npoint = int(words[8])
            startname = ""
            endname = ""
            if len(words)>9:
                startname = words[9]
            if len(words)>10:
                endname = words[10]
            band_segments += [ (start,end,length,npoint,startname,endname) ]

        if nline.startswith("output dos"):
            PLOT_DOS = True

        if nline.startswith("output species_proj_dos"):
            PLOT_DOS = True
            PLOT_DOS_SPECIES = True

        if nline.startswith("output atom_proj_dos"):
            PLOT_DOS = True
            PLOT_DOS_ATOM = True

        if nline.startswith("species"):
            if len(words) != 2:
                raise Exception("control.in: Syntax error in line '"+line+"'")
            species += [ words[1] ]
    # Added by Xiaochen Du

    #######################
    if PLOT_SOC:
        max_spin_channel = 1

    if PLOT_BANDS and PLOT_DOS:
        ax_bands = axes([0.1,0.1,0.6,0.8])
        ax_dos = axes([0.72,0.1,0.18,0.8],sharey=ax_bands)
        ax_dos.set_title("DOS")
        setp(ax_dos.get_yticklabels(),visible=False)
        ax_bands.set_ylabel("E [eV]")
        PLOT_DOS_REVERSED = True
    elif PLOT_BANDS:
        fig = plt.figure(figsize=(width,height))
        fig.patch.set_facecolor('none')
        fig.patch.set_alpha(0.0)
        ax_bands = fig.add_subplot(111)
        ax_bands.patch.set_facecolor('white')
        ax_bands.set_xlabel(x_label, fontproperties=font_prop)
        ax_bands.set_ylabel(y_label, fontproperties=font_prop)
        ax_bands.set_title(title, fontproperties=font_prop, size=15)
        ax_bands.grid(linestyle=":")
        # ax_bands = subplot(1,1,1)
    elif PLOT_DOS:
        ax_dos = subplot(1,1,1)
        ax_dos.set_title("DOS")
        PLOT_DOS_REVERSED = False

    #######################

    if PLOT_BANDS:
        print("Plotting %i band segments..."%len(band_segments))

        # if output_x_axis:
        #     ax_bands.axhline(0,color=(1.,0.,0.),linestyle=":")

        prev_end = band_segments[0][0]
        distance = band_totlength/30.0 # distance between line segments that do not coincide

        iband = 0
        xpos = 0.0
        labels = [ (0.0,band_segments[0][4]) ]

        for start,end,length,npoint,startname,endname in band_segments:
            iband += 1

            if any(start != prev_end):
                xpos += distance
                labels += [ (xpos,startname) ]

            xvals = xpos+linspace(0,length,npoint)
            xpos = xvals[-1]

            labels += [ (xpos,endname) ]

            prev_end = end
            prev_endname = endname

            for spin in range(1,max_spin_channel+1):
                fname = "band%i%03i.out"%(spin,iband)
                idx = []
                kvec = []
                band_energies = []
                band_occupations = []
                for line in open(get_path(fname)):
                    words = line.split()
                    idx += [ int(words[0]) ]
                    kvec += [ list(map(float,words[1:4])) ]
                    band_occupations += [ list(map(float,words[4::2])) ]
                    band_energies += [ list(map(float,words[5::2])) ]
                    # Apply energy offset if specified to all band energies just read in
                    band_energies[-1] = [x - energy_offset for x in band_energies[-1]]
                assert(npoint) == len(idx)
                band_energies = asarray(band_energies)
                # Now perform spline interpolation on band structure if requested
                if should_spline == True:
                    xvals_smooth = np.linspace(xvals.min(),xvals.max(),spline_factor*len(xvals) ) # Interpolated x axis for spline smoothing
                    new_band_energies = []
                    for b in range(band_energies.shape[1]): # Spline every band, one by one
                        new_band_energies.append(spline(xvals, band_energies[:,b], xvals_smooth))
                    band_energies = asarray(new_band_energies).transpose() # recombine the bands back into the original data format
                    xvals = xvals_smooth # and use the interpolated x axis
                for b in range(band_energies.shape[1]):
                    points = ax_bands.plot(xvals,band_energies[:,b],color=' br'[spin])

        tickx = []
        tickl = []
        for xpos,l in labels:
            # ax_bands.axvline(xpos,color='k',linestyle=":")
            tickx += [ xpos ]
            if len(l)>1:
                l = "$\\"+l+"$"
            tickl += [ l ]
        for x, l in zip(tickx, tickl):
            print("| %8.3f %s" % (x, repr(l)))

        ax_bands.set_xlim(labels[0][0],labels[-1][0])
        ax_bands.set_xticks(tickx)
        ax_bands.set_xticklabels(tickl)

    #######################

    if PLOT_DOS:
        def smoothdos(dos):
            dos = asarray(dos)
            # JW: Smoothing is actually done within FHI-aims...
            return dos
            for s in range(40):  # possible gaussian smoothing
                dos_old = dos
                dos = 0.5*dos_old
                dos[1:,...] += 0.25*dos_old[:-1,...]
                dos[0,...] += 0.25*dos_old[0,...]
                dos[:-1,...] += 0.25*dos_old[1:,...]
                dos[-1,...] += 0.25*dos_old[-1,...]
            return dos

        print("Plotting DOS")

    #    if PLOT_DOS_ATOM:
    #    elif PLOT_DOS_SPECIES:
        if PLOT_DOS_SPECIES:
            spinstrs = [ "" ]
            if max_spin_channel == 2:
                spinstrs = [ "_spin_up","_spin_down" ]

            energy = []
            tdos = []
            ldos = []
            maxdos = 0.0

            for s in species:
                val_s = []
                for ss in spinstrs:
                    f = open(get_path(s+"_l_proj_dos"+ss+".dat"))
                    f.readline()
                    mu = float(f.readline().split()[-2])
                    f.readline()
                    val_ss = []
                    for line in f:
                        val_ss += [ list(map(float,line.split())) ]
                    val_s += [ val_ss ]
                val_s = asarray(val_s).transpose(1,0,2)
                # Here val_s is a NumPy data structures, so to apply offset
                # we don't need to use list comprehension
                energy += [ val_s[:,:,0] - energy_offset ]
                tdos += [ smoothdos(val_s[:,:,1]) ]
                ldos += [ smoothdos(val_s[:,:,2:]) ]
                maxdos = max(maxdos,tdos[-1].max())
            for e in energy:
                for i in range(e.shape[1]):
                    assert all(e[:,i] == energy[0][:,0])
            energy = energy[0][:,0]

        else:
            f = open(get_path("KS_DOS_total.dat"))
            f.readline()
            mu = float(f.readline().split()[-2])
            f.readline()
            energy = []
            dos = []
            if max_spin_channel == 1:
                for line in f:
                    e,d = line.split()
                    energy += [ float(e) ]
                    energy[-1] = energy[-1] - energy_offset
                    dos += [ (2*float(d),) ]
            else:
                for line in f:
                    e,d1,d2 = line.split()
                    energy += [ float(e) ]
                    # Apply energy offset if specified to all DOS energies just read in
                    energy[-1] = energy[-1] - energy_offset
                    dos += [ (float(d1),float(d2)) ]
            energy = asarray(energy)
            dos = smoothdos(dos)
            maxdos = dos.max()

        spinsgn = [ 1. ]
        if max_spin_channel == 2:
            spinsgn = [ 1.,-1. ]

        if PLOT_DOS_REVERSED:
            ax_dos.axhline(0,color='k',ls='--')
            ax_dos.axvline(0,color=(0.5,0.5,0.5))

            if PLOT_DOS_SPECIES:
                for sp in range(len(species)):
                    for ispin in range(max_spin_channel):
                        ax_dos.plot(tdos[sp][:,ispin]*spinsgn[ispin],energy,linestyle='-',label='%s %s'%(species[sp],['up','down'][ispin]))
                        for l in range(ldos[sp].shape[2]):
                            ax_dos.plot(ldos[sp][:,ispin,l]*spinsgn[ispin],energy,linestyle='--',label='%s (l=%i) %s'%(species[sp],l,['up','down'][ispin]))
            else:
                for ispin in range(max_spin_channel):
                    ax_dos.plot(dos[:,ispin]*spinsgn[ispin],energy,color='br'[ispin])

            if maxdos_output > 0:
                # If the user has specified a maximum DOS value, use it
                ax_dos.set_xlim(array([min(spinsgn[-1],0.0)-0.05,1.00])*maxdos_output)
            else:
                # Otherwise use the maximum DOS value read in
                ax_dos.set_xlim(array([min(spinsgn[-1],0.0)-0.05,1.05])*maxdos)
            if CUSTOM_YLIM:
                ax_dos.set_ylim(ylim_lower,ylim_upper)
            else:
                ax_dos.set_ylim(energy[0],energy[-1])
        else:
            ax_dos.axvline(0,color='k',ls='--')
            ax_dos.axhline(0,color=(0.5,0.5,0.5))

            if PLOT_DOS_SPECIES:
                for sp in range(len(species)):
                    for ispin in range(max_spin_channel):
                        ax_dos.plot(energy,tdos[sp][:,ispin]*spinsgn[ispin],color='br'[ispin],linestyle='-',label='%s %s'%(species[sp],['up','down'][ispin]))
                        for l in range(ldos[sp].shape[2]):
                            ax_dos.plot(energy,ldos[sp][:,ispin,l]*spinsgn[ispin],color='br'[ispin],linestyle='--',label='%s (l=%i) %s'%(species[sp],l,['up','down'][ispin]))
            else:
                for ispin in range(max_spin_channel):
                    ax_dos.plot(energy,dos[:,ispin]*spinsgn[ispin],color='br'[ispin])

            ax_dos.set_xlim(energy[0],energy[-1])
            if CUSTOM_YLIM:
                ax_dos.set_ylim(ylim_lower,ylim_upper)
            else:
                if maxdos_output > 0:
                    # If the user has specified a maximum DOS value, use that instead
                    ax_dos.set_ylim(array([min(spinsgn[-1],0.0)-0.05,1.00])*maxdos_output)
                else:
                    # Otherwise use the maximum DOS value read in
                    ax_dos.set_ylim(array([min(spinsgn[-1],0.0)-0.05,1.05])*maxdos)
            ax_dos.set_xlabel(r"$\varepsilon - \mu$ (eV)")
        if PLOT_DOS_SPECIES:
            ax_dos.legend()
    else:
        if CUSTOM_YLIM:
            ax_bands.set_ylim(ylim_lower,ylim_upper)
        else:
            ax_bands.set_ylim(ylim_lower,ylim_upper) # just some random default -- definitely better than the full range including core bands

    #######################

    print()
    print("The resolution for saving figures is set to ", matplotlib.rcParams['savefig.dpi'], " dpi.")

    if should_spline:
        print()
        print("Spine interpolation has been used on the band structure, with an interpolation factor of ", spline_factor)
        print("You should check this band structure against the un-interpolated version, as splining may cause some small artifacts not present in the original band structure.")

    def on_q_exit(event):
        if event.key == "q": sys.exit(0)
    connect('key_press_event', on_q_exit)

    save_name = "{}_{}.png".format(get_path(folder_name), "full")
    plt.savefig(save_name, facecolor=fig.get_facecolor(), edgecolor='none')
    ax_bands.set_ylim([-1.5,band_gap+1.5])
    save_name = "{}_{}.png".format(get_path(folder_name), "min")
    plt.savefig(save_name, facecolor=fig.get_facecolor(), edgecolor='none')

def prep_and_plot(location):
    # location = sys.argv[1]
    print("File location is:", location)
    vbe, cbe = get_all_energies(location)
    offset = -vbe

    offset_max = MAX_ENERGY - offset
    offset_min = MIN_ENERGY - offset

    # truncate files
    bandfiles = ["".join([location,"/",f]) for f in listdir(location)
                 if (f.startswith('band10') and f.endswith('.out'))]
    bandfiles.sort()
    # print(bandfiles)
    print()
    print("Total number of points & lines:", count(bandfiles[0], len(bandfiles)))

    low_index, hi_index, band_gap, offset, low_energy, hi_energy = get_indices(bandfiles[0], offset_min, offset_max)

    for f in bandfiles:
        resize_standardize(f, low_index, hi_index, offset)

    # plot BS
    plotbs(location, MIN_ENERGY, MAX_ENERGY, band_gap)

    # remove BS plotting files
    bandfiles = ["".join([location,"/",f]) for f in listdir(location)
                 if (f.startswith('band10') and f.endswith('.out'))]
    bakfiles = [f for f in bandfiles
                 if f.endswith('_bak.out')]
    truncfiles = [f for f in bandfiles
                 if (f not in bakfiles)]
    bandfiles.sort()
    bakfiles.sort()
    truncfiles.sort()
    # print(bandfiles)
    # print(bakfiles)
    # print(truncfiles)
    # print()
    for f in truncfiles:
        remove(f)
    short_names = [f.split("/")[-1] for f in bakfiles]
    new_names = [".".join([f.split("_")[0],"out"]) for f in short_names]
    # print(short_names)
    # print(new_names)
    i = 0
    while (i<len(bakfiles)):
        rename(bakfiles[i], "/".join([location, new_names[i]]))
        i += 1
    print()
