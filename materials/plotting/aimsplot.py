#!/usr/bin/env python
#
#  Script to plot band structure and DOS calculated with FHI-aims. Requires the control.in/geometry.in as well as the output
#  of the calculation to be in the same directory ...
#
#  The script is written for python version 2.7 and would require syntax adaptations to run with later python versions.
#
#  To achieve labelling of the special points along the band structure plot, add two arguments to the "output band"
#  command in the control.in, using the following syntax:
#
#  output band <start> <end> <npoints> <starting_point_name> <ending_point_name>
#
#  Example: to plot a band with 100 points from Gamma to half way along one of the reciprocal lattice vectors, write (in control.in)
#
#  output band 0.0 0.0 0.0 0.5 0.0 0.0 100 Gamma <End_point_name>
#

from pylab import *
from numpy.linalg import *
from numpy import dot,cross,pi
from scipy.interpolate import spline

import matplotlib.pyplot as plt
import mpld3
import os,sys

###########
# OPTIONS #
###########

print_resolution = 250          # The DPI used for printing out images
default_line_width = 1          # Change the line width of plotted bands and k-vectors, 1 is default
font_size = 12                  # Change the font size.  12 is the default.
should_spline = True            # Turn on spline interpolation for band structures NOT VERY WELL TESTED!
output_x_axis = True            # Whether to output the x-axis (e.g. the e=0 line) or not
spline_factor = 10              # If spline interpolation turned on, the sampling factor (1 is the original grid)
maxdos_output = -1              # The maximum value of the DOS axis (a.k.a. x-axis) in the DOS
                                # For zero or negative values, the script will use its default value, the maximum
                                # value for the DOS in the energy window read in
########################

print("Plotting bands for FHI-aims!")
print("============================")
print()

print("Reading lattice vectors from geometry.in ...")

matplotlib.rcParams['lines.linewidth'] = default_line_width

latvec = []

CUSTOM_YLIM = False
FERMI_OFFSET = False
energy_offset = 0.0
if len(sys.argv) >= 3:
    CUSTOM_YLIM = True
    ylim_lower = float(sys.argv[1])
    ylim_upper = float(sys.argv[2])
if len(sys.argv) >= 4:
    FERMI_OFFSET = True
    energy_offset = float(sys.argv[3])

for line in open("geometry.in"):
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

for line in open("control.in"):
    words = line.split("#")[0].split()
    nline = " ".join(words)

    if nline.startswith("spin collinear") and not PLOT_SOC:
        max_spin_channel = 2

    if nline.startswith("calculate_perturbative_soc") or nline.startswith("include_spin_orbit") or nline.startswith("include_spin_orbit_sc"):
        PLOT_SOC = True
        max_spin_channel = 1

    if nline.startswith("output band "):
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
#

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
    width, height = (5, 4)
    fig = plt.figure(figsize=(width,height))
    ax_bands = fig.add_subplot(111)
    ax_bands.grid(True, alpha=0.7)
    # ax_bands = subplot(1,1,1)
elif PLOT_DOS:
    ax_dos = subplot(1,1,1)
    ax_dos.set_title("DOS")
    PLOT_DOS_REVERSED = False

#######################

if PLOT_BANDS:
    print("Plotting %i band segments..."%len(band_segments))

    if output_x_axis:
        ax_bands.axhline(0,color=(1.,0.,0.),linestyle=":")

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
            for line in open(fname):
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
                ax_bands.plot(xvals,band_energies[:,b],color=' br'[spin])

    tickx = []
    tickl = []
    for xpos,l in labels:
        ax_bands.axvline(xpos,color='k',linestyle=":")
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
                f = open(s+"_l_proj_dos"+ss+".dat")
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
        f = open("KS_DOS_total.dat")
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
        ax_bands.set_ylim(-20,20) # just some random default -- definitely better than the full range including core bands

#######################

matplotlib.rcParams['savefig.dpi'] =  print_resolution
matplotlib.rcParams['font.size'] = font_size

print()
print("The resolution for saving figures is set to ", matplotlib.rcParams['savefig.dpi'], " dpi.")

if should_spline:
    print()
    print("Spine interpolation has been used on the band structure, with an interpolation factor of ", spline_factor)
    print("You should check this band structure against the un-interpolated version, as splining may cause some small artifacts not present in the original band structure.")

def on_q_exit(event):
    if event.key == "q": sys.exit(0)
connect('key_press_event', on_q_exit)
# show()

# save_name = "{}.html".format(filename.split(".")[0])
save_name = "band_structure_mpld3.html"
mpld3.save_html(fig, save_name)
