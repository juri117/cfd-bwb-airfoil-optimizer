__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

from datetime import datetime

from cfd.SU2 import SU2
from cfd.CFDrun import CFDrun
from constants import *

import matplotlib.pyplot as plt
import numpy as np

####################################
### setup

# mach range
MACH_NR = np.linspace(0.6, 0.8, 11)
# target C_L
C_LIFT = .724

####################################


### default config for SU2 run ###
config = dict()
config['AOA'] = str(2.31)
config['TARGET_CL'] = str(C_LIFT)
config['FREESTREAM_PRESSURE'] = str(24999.8) #for altitude 10363 m
config['FREESTREAM_TEMPERATURE'] = str(220.79) #for altitude 10363 m
#config['GAS_CONSTANT'] = str(287.87)
#config['REF_LENGTH'] = str(1.0)
#config['REF_AREA'] = str(1.0)
config['EXT_ITER'] = str(9999)
config['OUTPUT_FORMAT'] = 'PARAVIEW'

REF_LENGTH = 1.
REF_AREA = 1.
REYNOLD = 6e6
config['REF_LENGTH'] = str(REF_LENGTH)
config['REF_AREA'] = str(REF_AREA)
config['REYNOLDS_NUMBER'] = str(REYNOLD)
config['REYNOLDS_LENGTH'] = str(1.)




##################################
### naca Test ca, cd over mach ###

su2 = SU2(SU2_BIN_PATH, used_cores=SU2_USED_CORES, mpi_exec=OS_MPI_COMMAND)

ouputF = open(WORKING_DIR + '/' + 'machResult_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv', 'w')
ouputF.write('machNr,AOA,CL,CD,CM,E,Iterations,Time(min)\n')

for mach in MACH_NR:
    projectName = 'analysis_mach_%0.3f' % (mach)
    projectDir = WORKING_DIR + '/' + projectName
    #create project dir if necessary
    if not os.path.isdir(projectDir):
        os.mkdir(projectDir)

    cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)

    cfd.load_airfoil_from_file(INPUT_DIR + '/vfw-va2.dat')
    #cfd.construct2d_generate_mesh(scale=REF_LENGTH)
    cfd.gmsh_generate_mesh(scale=REF_LENGTH)
    cfd.su2_fix_mesh()

    config['MACH_NUMBER'] = str(mach / 100.)
    cfd.su2_solve(config)

    totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()

    print('totalCL: ' + str(totalCL))
    print('totalCD: ' + str(totalCD))
    results = cfd.su2_parse_iteration_result()
    # totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()
    totalCL = results['CL']
    totalCD = results['CD']
    totalCM = results['CMz']
    totalE = results['CL/CD']
    ouputF.write(str(mach / 100.) + ','
                 + str(results['AOA']) + ','
                 + str(totalCL) + ','
                 + str(totalCD) + ','
                 + str(totalCM) + ','
                 + str(totalE) + ','
                 + str(results['Iteration']) + ','
                 + str(results['Time(min)']) + '\n')
    ouputF.flush()

print('done')