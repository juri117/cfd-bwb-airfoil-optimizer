__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

from datetime import datetime
import math
import sys
import matplotlib.pyplot as plt
from matplotlib import rc
import numpy as np
from colour import Color

from cfd.SU2 import SU2
from cfd.CFDrun import CFDrun
from airfoil.BPAirfoil import BPAirfoil
from airfoil.Airfoil import Airfoil
from constants import *
import optimization.cabinFitOptimizerV2 as cabin



FONT_SIZE = 14
font = {'family': 'sans-serif', 'size': FONT_SIZE}
fontLab = {'family': 'sans-serif', 'size': FONT_SIZE+2}

polar = np.genfromtxt(INPUT_DIR+'/'+'aoaResult.csv', delimiter=',', skip_header=1)

fig = plt.figure(1)
#rc('text', usetex=True)
rc('font', **font)

ax1 = plt.subplot(211)
plt.plot(polar[:,3], polar[:,2], 'b-', color='#437CAF')
ax1.set_xlabel(r'$c_d$', fontdict=fontLab)
ax1.set_ylabel(r'$c_l$', fontdict=fontLab)
ax1.tick_params(labelsize=FONT_SIZE, length=6, width=2)
#plt.savefig(WORKING_DIR + '/' + 'polar_cl_cd.png')
#plt.show()

ax2 = plt.subplot(212)
plt.plot(polar[:,1], polar[:,2], 'b-', color='#437CAF')
ax2.set_xlabel(r'$\alpha$', fontdict=fontLab)
ax2.set_ylabel(r'$c_l$', fontdict=fontLab)
ax2.tick_params(labelsize=FONT_SIZE, length=6, width=2)
"""
ax3 = plt.subplot(223)
plt.plot(polar[:,1], polar[:,4], 'b-')
ax3.set_xlabel(r'$\alpha$', fontdict=fontLab)
ax3.set_ylabel(r'$c_m$', fontdict=fontLab)
ax3.tick_params(labelsize=FONT_SIZE, length=6, width=2)

ax4 = plt.subplot(224)
plt.plot(polar[:,1], polar[:,5], 'b-')
ax4.set_xlabel(r'$\alpha$', fontdict=fontLab)
ax4.set_ylabel(r'$c_l/c_d$', fontdict=fontLab)
ax4.tick_params(labelsize=FONT_SIZE, length=6, width=2)
"""
plt.subplots_adjust(top=0.95, bottom=0.12, left=0.22, right=0.97, hspace=0.38,
                    wspace=0.40)

fig.set_size_inches(5, 6)

plt.savefig('dataOut/04_polarMaster.svg')
plt.savefig('dataOut/04_polarMaster.pdf')
plt.show()
