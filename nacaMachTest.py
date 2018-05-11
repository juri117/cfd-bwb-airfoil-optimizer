__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import os
import sys
import math

from Gmsh import Gmsh
from Airfoil import Airfoil
from SU2 import SU2
from BPAirfoil import BPAirfoil
from CFDrun import CFDrun

from openmdao.core.explicitcomponent import ExplicitComponent
from openmdao.api import Problem, ScipyOptimizeDriver, IndepVarComp, ExplicitComponent
import matplotlib.pyplot as plt

from openmdao.core.problem import Problem
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.analysis_error import AnalysisError

GMSH_EXE_PATH = 'gmsh/gmsh.exe'
#SU2_BIN_PATH = 'D:/prog/portable/Luftfahrt/su2-windows-latest/ExecParallel/bin/'
SU2_BIN_PATH = 'su2-windows-latest/ExecParallel/bin/'
OS_MPI_COMMAND = 'mpiexec'
SU2_USED_CORES = 4
WORKING_DIR = 'dataOut/'
INPUT_DIR = 'dataIn/'

# create working dir if necessary
if not os.path.isdir(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# check if gmsh exe exists
if not os.path.isfile(GMSH_EXE_PATH):
    print('gmsh executable could not be found in: ' + GMSH_EXE_PATH)
    sys.exit(0)

MACH_NUMBER = 0.78 #mach number cruise


#create working dir if necessary
if not os.path.isdir(WORKING_DIR):
    os.mkdir(WORKING_DIR)

#check if gmsh exe exists
if not os.path.isfile(GMSH_EXE_PATH):
    print('gmsh executable could not be found in: ' + GMSH_EXE_PATH)
    sys.exit(0)


### default config for SU2 run ###
config = dict()
config['PHYSICAL_PROBLEM'] = 'EULER'
config['AOA'] = str(0.0)
#config['FREESTREAM_PRESSURE'] = str(101325.0)
#config['FREESTREAM_TEMPERATURE'] = str(273.15)
#config['GAS_CONSTANT'] = str(287.87)
#config['REF_LENGTH'] = str(1.0)
#config['REF_AREA'] = str(1.0)
config['MARKER_EULER'] = '( airfoil )'
config['MARKER_FAR'] = '( farfield )'
config['EXT_ITER'] = str(500)
config['OUTPUT_FORMAT'] = 'PARAVIEW'




##################################
### naca Test ca, cd over mach ###

su2 = SU2(SU2_BIN_PATH, used_cores=SU2_USED_CORES, mpi_exec=OS_MPI_COMMAND)

machNr = range(60, 91, 1)

for mach in machNr:

    projectName = 'nacaMach' + '%03d' % mach
    projectDir = WORKING_DIR + '/' + projectName
    #create project dir if necessary
    if not os.path.isdir(projectDir):
        os.mkdir(projectDir)

    cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)

    cfd.load_airfoil_from_file(INPUT_DIR + '/naca641-212.csv')
    cfd.generate_mesh()
    cfd.su2_fix_mesh()

    config['MACH_NUMBER'] = str(mach / 100.)
    cfd.su2_solve(config)

    totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()

    print('totalCL: ' + str(totalCL))
    print('totalCD: ' + str(totalCD))

tCL = []
tCD = []
plt.close()
plt.clf()
for mach in machNr:
    projectDir = WORKING_DIR + '/' 'nacaMach' + '%03d' % mach
    totalCL, totalCD, totalCM, totalE = su2.parse_force_breakdown('forces_breakdown.dat', working_dir=projectDir)
    tCL.append(totalCL)
    tCD.append(totalCD)

plt.plot(machNr, tCD, '-r')
plt.plot(machNr, tCL, '-b')
plt.show()

