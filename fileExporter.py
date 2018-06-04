__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

from datetime import datetime
import math
import sys
import matplotlib.pyplot as plt
import numpy as np

from cfd.SU2 import SU2
from cfd.CFDrun import CFDrun
from airfoil.BPAirfoil import BPAirfoil
from airfoil.Airfoil import Airfoil
from constants import *



####################################
### setup



####################################


#cfd = CFDrun('export', used_cores=SU2_USED_CORES)
#cfd.load_airfoil_from_file(INPUT_DIR + '/vfw-va2.dat')

# load defaults from BPAirfoil
bp = BPAirfoil()
# read last optimization result if available (has to be copied here manually)
if os.path.isfile(INPUT_DIR+'/'+'airfoil.txt'):
    bp.read_parameters_from_file(INPUT_DIR+'/'+'airfoil.txt')
else:
    print('error, no default airfoil.txt')
    sys.exit(1)

##################################
### naca Test ca, cd over mach ###

print('export data to m-file')
filePath = WORKING_DIR + '/' + 'dataAirfoilOptimizer.m'
outputF = open(filePath, 'w')


outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('% this file was generatet by the cfdBwbAirfoilOptimizer-project\n')
outputF.write('% on: '+datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+'\n')
outputF.write('% repo: https://github.com/juri117/cfdBwbAirfoilOptimizer\n')
outputF.write('% author: Juri Bieler\n')
outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('% airfoil coordinates 2D (1000 points)\n')
outputF.write('aircraft.centerbody.airfoilCoords = ...\n')
bzCoords = bp.generate_airfoil(250, show_plot=False)
outputF.write('\t[{:.7f} {:.7f};\n'.format(bzCoords[0][0], bzCoords[0][1]))
for i in range(1, len(bzCoords)):
    outputF.write('\t{:.7f} {:.7f};\n'.format(bzCoords[i][0], bzCoords[i][1]))
outputF.write('\t{:.7f} {:.7f};];\n'.format(bzCoords[0][0], bzCoords[0][1]))
outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('\n')

outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('% relatvie coordinates of intersection points between airfoil points\n')
outputF.write('% between airfoil and tube\n')
outputF.write('%\n')
outputF.write('% (px_ol, py_ol) ________________________ (px_or, py_or)\n')
outputF.write('%               |                        |\n')
outputF.write('%               |                        |\n')
outputF.write('% (px_ul, py_ul)|________________________|(px_ur, py_ur)\n')
outputF.write('%\n')
outputF.write('%               <------------------------>\n')
outputF.write('%                            1\n')

angle = 0.
offsetFront = 0.11
length = 0.55
air = Airfoil(INPUT_DIR+'/'+'airfoil.dat')
air.rotate(angle)
#air.rotate(angle)
px_ul = offsetFront
px_ur = offsetFront + length
py_ul = max(air.get_buttom_y(px_ul), air.get_buttom_y(px_ur))
py_ur = py_ul
px_ol = px_ul
px_or = px_ur
py_ol = min(air.get_top_y(px_ol), air.get_top_y(px_or))
py_or = py_ol
print('geometrical calculated height = ' + str(py_ol - py_ul))
(px_ol, py_ol) = air.rotatePoint((0, 0), (px_ol, py_ol), -angle)
(px_ul, py_ul) = air.rotatePoint((0, 0), (px_ul, py_ul), -angle)

#py_ur = air.get_buttom_y(px_ur)
#px_or = px_ur
#py_or = py_ur + height
(px_or, py_or) = air.rotatePoint((0, 0), (px_or, py_or), -angle)
(px_ur, py_ur) = air.rotatePoint((0, 0), (px_ur, py_ur), -angle)
air.rotate(0.)
ax = air.plotAirfoil(showPlot=False)
ax.plot([px_ol, px_ul, px_ur, px_or, px_ol], [py_ol, py_ul, py_ur, py_or, py_ol], 'rx-')
plt.show()
outputF.write('aircraft.centerbody.px_ol\t= {:.7f};\n'.format(px_ol))
outputF.write('aircraft.centerbody.py_ol\t= {:.7f};\n'.format(py_ol))
outputF.write('aircraft.centerbody.px_or\t= {:.7f};\n'.format(px_or))
outputF.write('aircraft.centerbody.py_or\t= {:.7f};\n'.format(py_or))
outputF.write('aircraft.centerbody.px_ul\t= {:.7f};\n'.format(px_ul))
outputF.write('aircraft.centerbody.py_ul\t= {:.7f};\n'.format(py_ul))
outputF.write('aircraft.centerbody.px_ur\t= {:.7f};\n'.format(px_ur))
outputF.write('aircraft.centerbody.py_ur\t= {:.7f};\n'.format(py_ur))
outputF.write('\n')
outputF.write('aircraft.centerbody.tx_ol\t= {:.7f};\n'.format(px_ol))
outputF.write('aircraft.centerbody.ty_ol\t= {:.7f};\n'.format(py_ol))
outputF.write('aircraft.centerbody.tx_or\t= {:.7f};\n'.format(px_or))
outputF.write('aircraft.centerbody.ty_or\t= {:.7f};\n'.format(py_or))
outputF.write('aircraft.centerbody.tx_ul\t= {:.7f};\n'.format(px_ul))
outputF.write('aircraft.centerbody.ty_ul\t= {:.7f};\n'.format(py_ul))
outputF.write('aircraft.centerbody.tx_ur\t= {:.7f};\n'.format(px_ur))
outputF.write('aircraft.centerbody.ty_ur\t= {:.7f};\n'.format(py_ur))
outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('\n')

outputF.write('%-------------------------------------------------------------------------%\n')
outputF.write('% Col1: Angle of Attack, Col2: Lift Coefficent , Col3: Drag Coefficent,\n')
outputF.write('% Col4: Moment Coefficent\n')
outputF.write('aircraft.centerbody.airfoilAeroData2D = ...\n')

polar = np.genfromtxt(INPUT_DIR+'/'+'aoaResult.csv', delimiter=',', skip_header=1)
plt.plot(polar[:,3], polar[:,2], 'b-')
plt.suptitle('polar')
plt.xlabel('cd')
plt.ylabel('ca')
plt.savefig(WORKING_DIR + '/' + 'polar_cl_cd.png')
plt.show()

plt.plot(polar[:,1], polar[:,2], 'b-')
plt.suptitle('aoa-polar')
plt.xlabel('aoa in deg')
plt.ylabel('ca')
plt.savefig(WORKING_DIR + '/' + 'polar_cl_aoa.png')
plt.show()

outputF.write('\t[{:.7f} {:.7f} {:.7f} {:.7f};\n'.format(polar[0][1], polar[0][2], polar[0][3], polar[0][4]))
for i in range(1, len(polar)-1):
    outputF.write('\t{:.7f} {:.7f} {:.7f} {:.7f};\n'.format(polar[i][1], polar[i][2], polar[i][3], polar[i][4]))
outputF.write('\t{:.7f} {:.7f} {:.7f} {:.7f};];\n'.format(polar[-1][1], polar[-1][2], polar[-1][3], polar[-1][4]))

outputF.write('%-------------------------------------------------------------------------%\n')
outputF.close()
print('file exportet to: ' + filePath)

print('export geometry to txt-file')
top, but = bp.get_cooridnates_top_buttom(250, show_plot=False)
bzCoords = np.concatenate((top[::-1], but[::-1][1:]), axis=0)
filePath = WORKING_DIR + '/' + 'centerAirfoil.txt'
outputF = open(filePath, 'w')
for i in range(0, len(bzCoords)):
    outputF.write('{:.7f}\t{:.7f}\n'.format(bzCoords[i][0], bzCoords[i][1]))
if not(bzCoords[-1][0] == bzCoords[0][0] and bzCoords[-1][1] == bzCoords[0][1]):
    outputF.write('{:.7f}\t{:.7f}\n'.format(bzCoords[0][0], bzCoords[0][1]))
outputF.close()
print('file exportet to: ' + filePath)