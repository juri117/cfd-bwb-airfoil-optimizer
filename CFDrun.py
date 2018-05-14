__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import os
import sys

from Gmsh import Gmsh
from Airfoil import Airfoil
from SU2 import SU2
from BPAirfoil import BPAirfoil
from Construct2d import Construct2d
from meshTools.p3d2su2_OGrid import p2_to_su2_ogrid

GMSH_EXE_PATH = 'gmsh/gmsh.exe'
#SU2_BIN_PATH = 'D:/prog/portable/Luftfahrt/su2-windows-latest/ExecParallel/bin/'
SU2_BIN_PATH = 'su2-windows-latest/ExecParallel/bin/'
OS_MPI_COMMAND = 'mpiexec'
CONSTRUCT2D_EXE_PATH = 'meshTools/construct2d.exe'
SU2_USED_CORES = 4
WORKING_DIR = 'dataOut/'
INPUT_DIR = 'dataIn/'


class CFDrun:

    def __init__(self, project_name, used_cores=SU2_USED_CORES):
        # create project dir if necessary
        self.projectDir = WORKING_DIR + '/' + project_name
        # create project dir if necessary
        if not os.path.isdir(self.projectDir):
            os.mkdir(self.projectDir)
        self.su2 = SU2(SU2_BIN_PATH, used_cores=used_cores, mpi_exec=OS_MPI_COMMAND)
        self.foilCoord = None
        self.gmsh = Gmsh(GMSH_EXE_PATH)
        self.c2d = Construct2d(CONSTRUCT2D_EXE_PATH)

    def load_airfoil_from_file(self, file_name):
        self.airfoil = Airfoil(file_name)
        self.foilCoord = self.airfoil.get_sorted_point_list()

    #def load_airfoil_bp(self):
    #    bp = BPAirfoil()
    #    self.foilCoord = bp.generate_airfoil(500, show_plot=False)

    def set_airfoul_coords(self, buttom, top):
        #self.foilCoord = coords
        self.airfoil = Airfoil(None)
        self.airfoil.set_coordinates(top, buttom)
        self.foilCoord = self.airfoil.get_sorted_point_list()

    def gmsh_generate_mesh(self):
        print('start meshing with gmsh...')
        self.gmsh.generate_geo_file(self.foilCoord, 'airfoilMesh.geo', 1000, working_dir=self.projectDir)
        self.gmsh.run_2d_geo_file('airfoilMesh.geo', 'airfoilMesh.su2', working_dir=self.projectDir)

    def construct2d_generate_mesh(self):
        print('start meshing with construct2d...')
        self.airfoil.write_to_dat('airfoil.dat', working_dir=self.projectDir)

        self.c2d.run_mesh_generatoin('airfoil.dat', working_dir=self.projectDir)
        p2_to_su2_ogrid(self.projectDir + '/' + 'airfoil.p3d')
        os.rename(self.projectDir + '/' + 'airfoil.su2', self.projectDir + '/' + 'airfoilMesh.su2')

    def su2_fix_mesh(self):
        print('start mesh-fixing...')
        self.su2.fix_mesh('airfoilMesh.su2', 'airfoilMeshFixed.su2', working_dir=self.projectDir)

    def su2_solve(self, config):
        print('start solving...')
        self.su2.run_cfd('airfoilMeshFixed.su2', config, working_dir=self.projectDir)

    def su2_parse_results(self):
        print('parse results...')
        totalCL, totalCD, totalCM, totalE = self.su2.parse_force_breakdown('forces_breakdown.dat', working_dir=self.projectDir)
        return totalCL, totalCD, totalCM, totalE

    def su2_parse_iteration_result(self):
        print('parsing cfd iteration results')
        return self.su2.parse_result_from_history('history.vtk', working_dir=self.projectDir)

    def clean_up(self):
        print('clean up...')
        if os.path.isfile(self.projectDir + '/airfoilMesh.su2'):
            os.remove(self.projectDir + '/airfoilMesh.su2')
        if os.path.isfile(self.projectDir + '/airfoilMeshFixed.su2'):
            os.remove(self.projectDir + '/airfoilMeshFixed.su2')
        if os.path.isfile(self.projectDir + '/cfdMpiRun.bat'):
            os.remove(self.projectDir + '/cfdMpiRun.bat')
        if os.path.isfile(self.projectDir + '/restart_flow.dat'):
            os.remove(self.projectDir + '/restart_flow.dat')
        if os.path.isfile(self.projectDir + '/original_grid.dat'):
            os.remove(self.projectDir + '/original_grid.dat')
        if os.path.isfile(self.projectDir + '/meshFix.cfg'):
            os.remove(self.projectDir + '/meshFix.cfg')