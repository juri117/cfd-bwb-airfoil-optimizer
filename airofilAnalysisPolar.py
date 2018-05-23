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
AOA = np.linspace(-4., 6., 51)
# mach nr
MACH_NR = .72

####################################


### default config for SU2 run ###
config = dict()
config['FIXED_CL_MODE'] = 'NO'

config['MACH_NUMBER'] = str(MACH_NR)
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

ouputF = open(WORKING_DIR + '/' + 'aoaResult_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv', 'w')
ouputF.write('machNr,AOA,CL,CD,CM,E,Iterations,Time(min)\n')

for a in AOA:

    projectName = 'analysis_aoa_%0.4f' % (a)
    projectDir = WORKING_DIR + '/' + projectName
    #create project dir if necessary
    if not os.path.isdir(projectDir):
        os.mkdir(projectDir)

    cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)

    cfd.load_airfoil_from_file(INPUT_DIR + '/vfw-va2.dat')
    #cfd.construct2d_generate_mesh(scale=REF_LENGTH)
    cfd.gmsh_generate_mesh(scale=REF_LENGTH)
    cfd.su2_fix_mesh()


    config['AOA'] = str(a)
    cfd.su2_solve(config)

    results = cfd.su2_parse_iteration_result()
    cfd.clean_up()

    print('totalCL: ' + str(results['CL']))
    print('totalCD: ' + str(results['CD']))
    ouputF.write(str(MACH_NR) + ','
                 + str(a) + ','
                 + str(results['CL']) + ','
                 + str(results['CD']) + ','
                 + str(results['CMz']) + ','
                 + str(results['CL/CD']) + ','
                 + str(results['Iteration']) + ','
                 + str(results['Time(min)']) + '\n')
    ouputF.flush()

print('done')