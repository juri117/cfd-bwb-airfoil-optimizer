__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

from datetime import datetime

from cfd.CFDrun import CFDrun
from constants import *

MACH_NUM = 0.71
REF_LENGTH = 30. # cd, cl no effect I guess
REF_AREA = 30. # cd, cl get smaller

SCALE = 30. # cd, cl get bigger

config = dict()
#config['PHYSICAL_PROBLEM'] = 'EULER'
config['MACH_NUMBER'] = str(MACH_NUM)
config['AOA'] = str(0.0)
config['FIXED_CL_MODE'] = 'NO'
#config['TARGET_CL'] = str(.724)
config['FREESTREAM_PRESSURE'] = str(24999.8)  # for altitude 10363 m
config['FREESTREAM_TEMPERATURE'] = str(220.79)  # for altitude 10363 m
# config['GAS_CONSTANT'] = str(287.87)
config['EXT_ITER'] = str(9999)
config['OUTPUT_FORMAT'] = 'PARAVIEW'
#config['MG_DAMP_RESTRICTION'] = str(1.)
#config['MG_DAMP_PROLONGATION'] = str(1.)

config['REF_LENGTH'] = str(REF_LENGTH)
config['REF_AREA'] = str(REF_AREA)

speedOfSound = 307.828 # for altitude 10363 m
kinViscosity = 5.99537e-5 # for altitude 10363 m
REYNOLD = speedOfSound * REF_LENGTH * MACH_NUM / kinViscosity
config['REYNOLDS_NUMBER'] = str(REYNOLD)


ouputF = open(WORKING_DIR + '/' + 'convergenceResult.txt', 'w')
ouputF.write('innerMeshSize,outerMeshSize,CL,CD,CM,E,Iterations,Time(min)\n')

projectName = 'cfdTest_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
projectDir = WORKING_DIR + '/' + projectName
#create project dir if necessary
if not os.path.isdir(projectDir):
    os.mkdir(projectDir)

cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)
#cfd.load_airfoil_from_file(INPUT_DIR + '/naca641-212.csv')
cfd.load_airfoil_from_file(INPUT_DIR + '/bzTest.dat')

cfd.c2d.pointsInNormalDir = 80
cfd.c2d.pointNrAirfoilSurface = 200
#cfd.c2d.farfieldRadius = 50.
#cfd.c2d.pointsInNormalDir = 120

cfd.construct2d_generate_mesh(scale=SCALE, plot=True)

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
