__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

# ==============================================================================
# description     :offers API to gmsh, which is used to generate a mesh from a cad geometry
# date            :2018-01-11
# notes           :
# python_version  :3.6
# ==============================================================================

import subprocess
import os
import numpy as np

class Gmsh:

    def __init__(self, gmsh_path):
        self.errorFlag = False
        self.gmshPath = gmsh_path

        self.innerMeshSize = 0.005
        self.outerMeshSize = 0.5
        self.recombinMesh = False

    #runns gmsh.exe from command line with to create a mesh file
    def run_2d_geo_file(self, input_file_name, output_file_name, working_dir='dataOut/', min_mesh_size=1e-10, max_mesh_size=1e22):
        # -2 : mesh 2D
        # -format str: select format here inp (abaqus mesh)
        # -o str: output file name
        # -order int: 1,...,5
        # -clmin float: min mesh size
        # -clmax float: max mesh size
        format = output_file_name.split('.')[-1]
        p = subprocess.Popen([self.gmshPath,
                              input_file_name,
                              '-2',
                              '-format', format,
                              '-clmin', str(min_mesh_size),
                              '-clmax', str(max_mesh_size),
                              '-o', output_file_name],
                             cwd=working_dir, stdout=subprocess.PIPE)
        out, err = p.communicate()
        print(out.decode('UTF-8'))
        if err is not None:
            print('gmsh process failed')
            self.errorFlag = True
        if not os.path.isfile(working_dir + '/' + output_file_name):
            print('error gmash did not create the file as expected')
            self.errorFlag = True
        return

    def generate_geo_file(self, airfoil_points, output_file_name, startIndex, working_dir='dataOut/'):
        ## Read in data using this bit
        #fin = open(filename, 'r')
        #i = 0
        #x = [];
        #y = [];
        #z = [];

        #lines = fin.readlines()

        #for line in lines:
        #    # comments indicated by #
        #    if line[0] != '#' or line[0] != '':
        #        i = i + 1
        #        data = line.split()
        #        x.append(float(data[0]))
        #        y.append(float(data[1]))

        #        newZ = 0
        #        if len(data) > 2:
        #            newZ = float(data[2])
        #        z.append(newZ)

        #        n_lines = int(i)

        # Write data out with this;

        n_lines = len(airfoil_points)
        x = airfoil_points[:,0]
        y = airfoil_points[:,1]
        z = np.zeros(n_lines)

        fout = open(working_dir + '/' + output_file_name, 'w')

        # Format
        # Point(1) = {0, 0, 0, lc};
        fout.write("airfoil_lc = %f;\n" % (self.innerMeshSize))
        j = startIndex
        for i in range(n_lines):
            outputline = "Point(%i) = { %8.8f, %8.8f, %8.8f, airfoil_lc};\n " \
                         % (j, x[i], y[i], z[i])
            j = j + 1
            fout.write(outputline)

        # gmsh bspline format
        # Write out splinefit line
        fout.write("Spline(%i) = {%i:%i, %i};\n" \
                   % (startIndex, startIndex, startIndex + n_lines - 1, startIndex))

        # generate circular farfield
        fout.write("radius = %i;\n" % (10))
        fout.write("farfield_lc = %f;\n" % (self.outerMeshSize))
        fout.write("Point(11) = {0, 0, 0, farfield_lc};\n")
        fout.write("Point(12) = {0, -radius, 0, farfield_lc};\n")
        fout.write("Point(13) = {-radius, 0, 0, farfield_lc};\n")
        fout.write("Point(14) = {0, radius, 0, farfield_lc};\n")
        fout.write("Point(15) = {4 * radius, radius, 0, farfield_lc};\n")
        fout.write("Point(16) = {4 * radius, -radius, 0, farfield_lc};\n")
        fout.write("Circle(21) = {12, 11, 13};\n")
        fout.write("Circle(22) = {13, 11, 14};\n")
        fout.write("Line(25) = {14, 15};\n")
        fout.write("Line(26) = {15, 16};\n")
        fout.write("Line(27) = {16, 12};\n")
        fout.write("Line Loop(1) = {21, 22, 25, 26, 27};\n")

        fout.write("Line Loop(2) = {1000};\n")
        fout.write("Plane Surface(2000) = {1, 2};\n")
        fout.write("Physical Line(\"airfoil\") = {1000};\n")
        fout.write("Physical Line(\"farfield\") = {21, 22, 25, 26, 27};\n")
        #fout.write("Transfinite Line{1000} = 500;\n")
        #fout.write("Transfinite Line{3001} = 500;\n")
        #fout.write("Transfinite Surface{2000} = {1, 2};\n")
        fout.write("Physical Surface(2000) = {2000};\n")
        if self.recombinMesh:
            fout.write("Recombine Surface{2000};\n")

        fout.close()

if __name__ == '__main__':
    g = Gmsh('gmsh/gmsh.exe')
