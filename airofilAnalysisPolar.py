__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

from datetime import datetime
import math

from cfd.SU2 import SU2
from cfd.CFDrun import CFDrun
from constants import *

import matplotlib.pyplot as plt
import numpy as np


####################################
### setup

# mach range
AOA = np.linspace(-2., 6., 9)
# mach nr
MACH_NUMBER = 0.85  # mach number cruise
# compensate sweep deg
SWEEP_LEADING_EDGE = 45

####################################

MACH_SWEEP_COMPENSATED = MACH_NUMBER * math.sqrt(math.cos(SWEEP_LEADING_EDGE * math.pi / 180))
print('sweep compensated mach number: ' + str(MACH_SWEEP_COMPENSATED))

MACH_NR = MACH_SWEEP_COMPENSATED
REF_LENGTH = 30.  # cd, cl no effect I guess
REF_AREA = REF_LENGTH  # cd, cl get smaller
SCALE = REF_LENGTH  # cd, cl get bigger

### default config for SU2 run ###
config = dict()

speedOfSound = 307.828 # for altitude 10363 m
kinViscosity = 5.99537e-5 # for altitude 10363 m
REYNOLD = speedOfSound * REF_LENGTH * MACH_NR / kinViscosity
print('Reynolds-Number: ' + str(REYNOLD))
config['REF_LENGTH'] = str(REF_LENGTH)
config['REF_AREA'] = str(REF_AREA)
config['REYNOLDS_NUMBER'] = str(REYNOLD)

config['FIXED_CL_MODE'] = 'NO'
#config['TARGET_CL'] = 0.15

config['MACH_NUMBER'] = str(MACH_NR)
config['FREESTREAM_PRESSURE'] = str(24999.8) #for altitude 10363 m
config['FREESTREAM_TEMPERATURE'] = str(220.79) #for altitude 10363 m
#config['GAS_CONSTANT'] = str(287.87)
#config['REF_LENGTH'] = str(1.0)
#config['REF_AREA'] = str(1.0)
config['EXT_ITER'] = str(5000)
config['OUTPUT_FORMAT'] = 'PARAVIEW'

config['MGLEVEL'] = str(3)
config['MGCYCLE'] = 'V_CYCLE'
config['MG_DAMP_RESTRICTION'] = str(.55)
config['MG_DAMP_PROLONGATION'] = str(.55)

#config['CFL_ADAPT'] = 'YES'
#config['CFL_ADAPT_PARAM'] = '( 1.5, 0.5, 1.0, 50.0 )'

config['TIME_DISCRE_FLOW'] = 'EULER_IMPLICIT'
config['CONV_NUM_METHOD_FLOW'] = 'JST'
config['RELAXATION_FACTOR_FLOW'] = str(1.)
config['RELAXATION_FACTOR_TURB'] = str(1.)




##################################
### naca Test ca, cd over mach ###

su2 = SU2(SU2_BIN_PATH, used_cores=SU2_USED_CORES, mpi_exec=OS_MPI_COMMAND)

outputF = open(WORKING_DIR + '/' + 'aoaResult_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv', 'w')
outputF.write('machNr,AOA,CL,CD,CM,E,Iterations,Time(min)\n')

for a in AOA:

    projectName = 'analysis_aoa_%0.4f' % (a)
    projectDir = WORKING_DIR + '/' + projectName
    #create project dir if necessary
    if not os.path.isdir(projectDir):
        os.mkdir(projectDir)

    cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)

    cfd.load_airfoil_from_file(INPUT_DIR + '/vfw-va2.dat')
    #cfd.load_airfoil_from_file(INPUT_DIR + '/vfw-va2.dat')
    cfd.c2d.pointsInNormalDir = 80
    cfd.c2d.pointNrAirfoilSurface = 200
    cfd.c2d.reynoldsNum = REYNOLD
    cfd.construct2d_generate_mesh(scale=SCALE, plot=False)
    #cfd.construct2d_generate_mesh(scale=REF_LENGTH)
    #cfd.gmsh_generate_mesh(scale=REF_LENGTH)
    cfd.su2_fix_mesh()


    config['AOA'] = str(a)
    cfd.su2_solve(config)

    results = cfd.su2_parse_iteration_result()
    cfd.clean_up()

    print('totalCL: ' + str(results['CL']))
    print('totalCD: ' + str(results['CD']))
    outputF.write(str(MACH_NR) + ','
                  + str(a) + ','
                  + str(results['CL']) + ','
                  + str(results['CD']) + ','
                  + str(results['CMz']) + ','
                  + str(results['CL/CD']) + ','
                  + str(results['Iteration']) + ','
                  + str(results['Time(min)']) + '\n')
    outputF.flush()

outputF.close()
print('done')