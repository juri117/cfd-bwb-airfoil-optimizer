
import os
import sys

GMSH_EXE_PATH = 'bin/gmsh/gmsh.exe'
#SU2_BIN_PATH = 'D:/prog/portable/Luftfahrt/su2-windows-latest/ExecParallel/bin/'
SU2_BIN_PATH = 'bin/su2-windows-latest/ExecParallel/bin/'
OS_MPI_COMMAND = 'mpiexec'
CONSTRUCT2D_EXE_PATH = 'bin/construct2d/construct2d.exe'
SU2_USED_CORES = 20
WORKING_DIR = 'dataOut/'
INPUT_DIR = 'dataIn/'



### some checks here...

# create working dir if necessary
if not os.path.isdir(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# check if gmsh exe exists
GMSH_EXE_PATH = os.path.abspath(GMSH_EXE_PATH)
if not os.path.isfile(GMSH_EXE_PATH):
    print('WARNING: gmsh executable could not be found in: ' + GMSH_EXE_PATH)

# check if construct2d exe exists
CONSTRUCT2D_EXE_PATH = os.path.abspath(CONSTRUCT2D_EXE_PATH)
if not os.path.isfile(CONSTRUCT2D_EXE_PATH):
    print('WARNING: construct2d executable could not be found in: ' + CONSTRUCT2D_EXE_PATH)