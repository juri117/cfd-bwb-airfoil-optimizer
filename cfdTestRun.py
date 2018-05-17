__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import os
import sys
import math
import numpy as np
from datetime import datetime

from Gmsh import Gmsh
from Airfoil import Airfoil
from SU2 import SU2
from BPAirfoil import BPAirfoil
from CFDrun import CFDrun
from constants import *

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


MACH_NUM = 0.71
REF_LENGTH = 36. # cd, cl no effect I guess
REF_AREA = 36. # cd, cl get smaller

SCALE = 36. # cd, cl get bigger


config = dict()
config['PHYSICAL_PROBLEM'] = 'EULER'
config['MACH_NUMBER'] = str(MACH_NUM)
config['AOA'] = str(2.)
config['FREESTREAM_PRESSURE'] = str(24999.8)  # for altitude 10363 m
config['FREESTREAM_TEMPERATURE'] = str(220.79)  # for altitude 10363 m
# config['GAS_CONSTANT'] = str(287.87)
# config['REF_LENGTH'] = str(1.0)
# config['REF_AREA'] = str(1.0)
config['MARKER_EULER'] = '( airfoil )'
config['MARKER_FAR'] = '( farfield )'
config['EXT_ITER'] = str(1000)
config['OUTPUT_FORMAT'] = 'PARAVIEW'
config['MG_DAMP_RESTRICTION'] = str(1.)
config['MG_DAMP_PROLONGATION'] = str(1.)

config['REF_LENGTH'] = str(REF_LENGTH)
config['REF_AREA'] = str(REF_AREA)



#for construct 2d
normalMeshDivider = [100] #range(60, 500, 10)
secondParam = [250]


cdList = np.zeros((len(normalMeshDivider),len(secondParam)))
clList = np.zeros((len(normalMeshDivider),len(secondParam)))
cmList = np.zeros((len(normalMeshDivider),len(secondParam)))
eList = np.zeros((len(normalMeshDivider),len(secondParam)))

ouputF = open(WORKING_DIR + '/' + 'convergenceResult.txt', 'w')
ouputF.write('innerMeshSize,outerMeshSize,CL,CD,CM,E,Iterations,Time(min)\n')

projectName = 'cfdTest_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
projectDir = WORKING_DIR + '/' + projectName
#create project dir if necessary
if not os.path.isdir(projectDir):
    os.mkdir(projectDir)

cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)
cfd.load_airfoil_from_file(INPUT_DIR + '/naca641-212.csv')

#cfd.c2d.pointsInNormalDir = 100
#cfd.c2d.pointNrAirfoilSurface = 250

cfd.construct2d_generate_mesh(scale=SCALE, savePlot=False)
cfd.su2_fix_mesh()
cfd.su2_solve(config)
results = cfd.su2_parse_iteration_result()
totalCL = results['CL']
totalCD = results['CD']
totalCM = results['CMz']
totalE = results['CL/CD']

print('totalCL: ' + str(totalCL))
print('totalCD: ' + str(totalCD))

print('done')
