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
#import fcntl
import numpy as np
import time
import threading
import Queue
import select
import sys
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

class Construct2d:

    def __init__(self, construct2d_path):
        self.errorFlag = False
        self.construct2dPath = construct2d_path

        self.pointNrAirfoilSurface = 250
        self.farfieldRadius = 15.0
        self.useCGrid = True
        self.pointsInNormalDir = 101

    def wait_for_keyword(self, que, word):
        while (True):
            try:
                line = que.get_nowait()  # or q.get(timeout=.1)
            except Empty:
                #print('no output yet')
                time.sleep(0.01)
            else:  # got line
                print(line)
                if word in line:
                    return True

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def write_to_console_and_enter(self, p, str):
        p.stdin.write(str + '\n')
        p.stdin.flush()

    def run_mesh_generatoin(self, input_dat_file_name, working_dir='dataOut/'):
        #out_r, out_w = pty.openpty()


        #p = subprocess.Popen([self.construct2dPath], cwd=working_dir,
        #                            stdout=pipe_w,
        #                            stderr=pipe_w, shell = False)
        #                            #stdin=subprocess.PIPE)

        ON_POSIX = 'posix' in sys.builtin_module_names



        p = subprocess.Popen([self.construct2dPath], cwd=working_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX)
        q = Queue()
        t = Thread(target=self.enqueue_output, args=(p.stdout, q))
        t.daemon = True  # thread dies with the program
        t.start()

        time.sleep(1.)
        self.wait_for_keyword(q, 'QUIT')
        self.write_to_console_and_enter(p, input_dat_file_name)
        self.wait_for_keyword(q, 'QUIT')

        """
        #enter airfoil surface options
        self.write_to_console_and_enter(p, 'SOPT')
        self.wait_for_keyword(q, 'QUIT')
        #points on surface
        self.write_to_console_and_enter(p, 'NSRF')
        self.wait_for_keyword(q, 'Current')
        self.write_to_console_and_enter(p, str(self.pointNrAirfoilSurface))
        self.wait_for_keyword(q, 'QUIT')
        #farfield radius
        self.write_to_console_and_enter(p, 'RADI')
        self.wait_for_keyword(q, 'Current')
        self.write_to_console_and_enter(p, str(self.farfieldRadius))
        self.wait_for_keyword(q, 'QUIT')
        #go back
        self.write_to_console_and_enter(p, 'QUIT')
        self.wait_for_keyword(q, 'QUIT')

        #enter volume grid options
        self.write_to_console_and_enter(p, 'VOPT')
        self.wait_for_keyword(q, 'QUIT')
        #select mesh type
        self.write_to_console_and_enter(p, 'TOPO')
        self.wait_for_keyword(q, 'Sharp')
        if self.useCGrid:
            self.write_to_console_and_enter(p, 'CGRD')
        else:
            self.write_to_console_and_enter(p, 'OGRD')
        self.wait_for_keyword(q, 'QUIT')
        #set num of points in normal direction
        self.write_to_console_and_enter(p, 'JMAX')
        self.wait_for_keyword(q, 'Current')
        self.write_to_console_and_enter(p, str(self.pointsInNormalDir))
        self.wait_for_keyword(q, 'QUIT')
        # go back
        self.write_to_console_and_enter(p, 'QUIT')
        self.wait_for_keyword(q, 'QUIT')
        """

        #start meshing
        self.write_to_console_and_enter(p, 'GRID')
        self.wait_for_keyword(q, 'QUIT')
        self.write_to_console_and_enter(p, 'SMTH')
        self.wait_for_keyword(q, 'QUIT')
        #quit
        self.write_to_console_and_enter(p, 'QUIT')


        out, err = p.communicate()
        if err == None:
            print('run meshTools successful!')
        else:
            print('ERROR: meshTools returned the error: ' + str(err))


        # ... do other things here

        # read line without blocking

                # ... do something with line


        #out = proc.stdout
        #out, err = p.communicate(input_dat_file_name)
        #print(out)
        #p.stdin.write(input_dat_file_name)
        #out, err = p.communicate('GRID')
        #out = p.stdout.read()
        #print(out)
        #out, err = p.communicate('SMTH')
        #print(out)
        #out, err = p.communicate('QUIT')
        #print(out)

        print('done')


if __name__ == '__main__':
    c2d = Construct2d('meshTools/construct2d.exe')
    c2d.pointNrAirfoilSurface = 200
    c2d.farfieldRadius = 10
    c2d.run_mesh_generatoin('naca641-212.dat', working_dir='dataOut/meshTest/')