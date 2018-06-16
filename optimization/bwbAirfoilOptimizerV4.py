__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import os
import sys
import math

from meshing.Gmsh import Gmsh
from airfoil.Airfoil import Airfoil
from cfd.SU2 import SU2
from airfoil.BPAirfoil import BPAirfoil
from cfd.CFDrun import CFDrun
from constants import *

sys.path.insert(0, './OpenMDAO')
sys.path.insert(0, './pyDOE2')

from openmdao.api import Problem, ScipyOptimizeDriver, IndepVarComp, ExplicitComponent, SqliteRecorder
from datetime import datetime

from openmdao.core.problem import Problem
from openmdao.core.indepvarcomp import IndepVarComp

import optimization.cabinFitOptimizerV2 as cabinFit

LOG_FILE_PATH = WORKING_DIR + '/om_iterations_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv'

PROJECT_NAME_PREFIX = 'iter'

MACH_NUMBER = 0.85  # mach number cruise
# compensate sweep deg
SWEEP_LEADING_EDGE = 45

MACH_SWEEP_COMPENSATED = MACH_NUMBER * math.sqrt(math.cos(SWEEP_LEADING_EDGE * math.pi / 180))
print('sweep compensated mach number: ' + str(MACH_SWEEP_COMPENSATED))

MACH_NR = MACH_SWEEP_COMPENSATED
REF_LENGTH = 39.9462  # cd, cl no effect I guess
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
config['MG_DAMP_RESTRICTION'] = str(.45)
config['MG_DAMP_PROLONGATION'] = str(.45)

#config['CFL_ADAPT'] = 'YES'
#config['CFL_ADAPT_PARAM'] = '( 1.5, 0.5, 1.0, 50.0 )'

config['TIME_DISCRE_FLOW'] = 'EULER_IMPLICIT'
config['CONV_NUM_METHOD_FLOW'] = 'JST'
config['RELAXATION_FACTOR_FLOW'] = str(1.)
config['RELAXATION_FACTOR_TURB'] = str(1.)

cabinLength = 0.55
cabinHeigth = 0.14

class AirfoilCFD(ExplicitComponent):

    def setup(self):
        ######################
        ### needed Objects ###
        self.bzFoil = BPAirfoil()
        self.air = Airfoil(None)


        #####################
        ### openMDAO init ###
        ### INPUTS

        self.add_input('r_le', val=-0.05, desc='nose radius')
        self.add_input('beta_te', val=0.1, desc='thickness angle trailing edge')
        self.add_input('x_t', val=0.3, desc='dickenruecklage')

        self.add_input('gamma_le', val=0.5, desc='camber angle leading edge')
        self.add_input('x_c', val=0.5, desc='woelbungsruecklage')
        self.add_input('y_c', val=0.1, desc='max camber')
        self.add_input('alpha_te', val=-0.1, desc='camber angle trailing edge')
        #self.add_input('z_te', val=0., desc='camber trailing edge')

        # bezier parameters
        self.add_input('b_8', val=0.05, desc='')
        self.add_input('b_15', val=0.75, desc='')
        self.add_input('b_0', val=0.1, desc='')
        self.add_input('b_2', val=0.25, desc='')
        self.add_input('b_17', val=0.9, desc='')

        ### OUTPUTS
        self.add_output('c_d', val=.2)
        self.add_output('c_l', val=.2)
        self.add_output('c_m', val=.2)
        self.add_output('y_t', val=0.1, desc='max thickness')

        self.add_output('cabin_height', val=cabinHeigth)
        self.add_output('angle', val=0.)
        self.add_output('offsetFront', val=.1)

        self.declare_partials('*', '*', method='fd')
        self.executionCounter = 0

    """
    def fit_cabin(self, xFront, angle):
        top, buttom = self.bzFoil.get_cooridnates_top_buttom(500)
        if self.bzFoil.valid == False:
            return False
        xBack = xFront + cabinLength  # inputs['length']
        self.air.set_coordinates(top, buttom)
        self.air.rotate(angle)
        yMinButtom = max(self.air.get_buttom_y(xFront), self.air.get_buttom_y(xBack))
        yMaxTop = min(self.air.get_top_y(xFront), self.air.get_top_y(xBack))
        height = yMaxTop - yMinButtom
        return height
        #outputs['cabin_height'] = height
    """

    def compute(self, inputs, outputs):
        error = False
        self.bzFoil.r_le = inputs['r_le']
        self.bzFoil.beta_te = inputs['beta_te']
        self.bzFoil.dz_te = 0.
        self.bzFoil.x_t = inputs['x_t']

        self.bzFoil.gamma_le = inputs['gamma_le']
        self.bzFoil.x_c = inputs['x_c']
        self.bzFoil.y_c = inputs['y_c']
        self.bzFoil.alpha_te = inputs['alpha_te']
        self.bzFoil.z_te = 0.

        self.bzFoil.b_8 = inputs['b_8']
        self.bzFoil.b_15 = inputs['b_15']
        self.bzFoil.b_0 = inputs['b_0']
        self.bzFoil.b_2 = inputs['b_2']
        self.bzFoil.b_17 = inputs['b_17']

        projectName = PROJECT_NAME_PREFIX + '_%09d' % self.executionCounter
        cfd = CFDrun(projectName)

        airFoilCoords = self.bzFoil.generate_airfoil(500,
                                                     show_plot=False,
                                                     save_plot_path=WORKING_DIR+'/'+projectName+'/airfoil.png',
                                                     param_dump_file=WORKING_DIR+'/'+projectName+'/airfoil.txt')

        # check if bz is valid
        if self.bzFoil.valid:
            ### use cabin fit optimization to find y_t
            cabinFit.cabinHeigth = cabinHeigth
            cabinFit.cabinLength = cabinLength
            cabinFit.bzFoil = self.bzFoil
            y_t, height, angle, offsetFront = cabinFit.run_cabin_opti(show_plot=False)
            self.bzFoil.y_t = y_t

            outputs['cabin_height'] = height
            outputs['y_t'] = y_t
            outputs['angle'] = angle
            outputs['offsetFront'] = offsetFront
            print('new cabin_height= ' + str(outputs['cabin_height']))


        if not self.bzFoil.valid:
            #raise AnalysisError('AirfoilCFD: invalid BPAirfoil')
            print('ERROR: AirfoilCFD, invalid BPAirfoil')
            self.bzFoil.save_parameters_to_file(
                WORKING_DIR + '/bz_error_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.txt')
            error = True
        else:

            self.bzFoil.plot_airfoil_with_cabin(outputs['offsetFront'],
                                                cabinLength,
                                                outputs['cabin_height'],
                                                outputs['angle'],
                                                show_plot=False,
                                                save_plot_path=WORKING_DIR + '/' + projectName + '/airfoil_cabin.png')

            ### now we do cfd
            top, buttom = self.bzFoil.get_cooridnates_top_buttom(500)
            cfd.set_airfoul_coords(top, buttom)

            cfd.c2d.pointsInNormalDir = 80
            cfd.c2d.pointNrAirfoilSurface = 200
            cfd.c2d.reynoldsNum = REYNOLD
            cfd.construct2d_generate_mesh(scale=SCALE, plot=False)
            cfd.su2_fix_mesh()
            cfd.su2_solve(config)
            results = cfd.su2_parse_iteration_result()
            cfd.clean_up()

            if float(results['CD']) <= 0. or float(results['CD']) > 100.:
                #raise AnalysisError('AirfoilCFD: c_d is out of range (cfd failed)')
                print('ERROR: AirfoilCFD, c_d is out of range (cfd failed)')
                error = True

            outputs['c_d'] = results['CD']
            outputs['c_l'] = results['CL']
            outputs['c_m'] = results['CMz']
            print('c_l= ' + str(outputs['c_l']))
            print('c_d= ' + str(outputs['c_d']))
            print('c_m= ' + str(outputs['c_m']))
            print('c_l/c_d= ' + str(results['CL/CD']))
            print('cfdIterations= ' + str(results['Iteration']))
            write_to_log(str(self.executionCounter) + ','
                         + datetime.now().strftime('%H:%M:%S') + ','
                         + str(outputs['c_l']) + ','
                         + str(outputs['c_d']) + ','
                         + str(outputs['c_m']) + ','
                         + str(results['CL/CD']) + ','
                         + str(results['Iteration']) + ','
                         + str(outputs['cabin_height']) + ','
                         + str(outputs['offsetFront']) + ','
                         + str(outputs['angle']) + ','
                         + str(inputs['r_le']) + ','
                         + str(inputs['beta_te']) + ','
                         + str(inputs['x_t']) + ','
                         + str(outputs['y_t']) + ','
                         + str(inputs['gamma_le']) + ','
                         + str(inputs['x_c']) + ','
                         + str(inputs['y_c']) + ','
                         + str(inputs['alpha_te']) + ','
                         + str(self.bzFoil.z_te) + ','#+ str(inputs['z_te']) + ','
                         + str(inputs['b_8']) + ','
                         + str(inputs['b_15']) + ','
                         + str(inputs['b_0']) + ','
                         + str(inputs['b_17']) + ','
                         + str(inputs['b_2']))

        #workaround since raising an error seems to crash the optimization
        if error:
            outputs['c_d'] = 999.
            outputs['c_l'] = 0.
            outputs['c_m'] = 0.
        self.executionCounter += 1


def write_to_log(outStr):
    outStr = outStr.replace('[', '')
    outStr = outStr.replace(']', '')
    outputF = open(LOG_FILE_PATH, 'a') #'a' so we append the file
    outputF.write(outStr + '\n')
    outputF.close()


def runOpenMdao():

    prob = Problem()

    #first guesses here
    indeps = prob.model.add_subsystem('indeps', IndepVarComp(), promotes=['*'])

    # load defaults from BPAirfoil
    bp = BPAirfoil()
    # read last optimization result if available (has to be copied here manually)
    if os.path.isfile(INPUT_DIR+'/'+'airfoil.txt'):
        bp.read_parameters_from_file(INPUT_DIR+'/'+'airfoil.txt')
    indeps.add_output('r_le', bp.r_le)
    indeps.add_output('beta_te', bp.beta_te)
    indeps.add_output('x_t', bp.x_t)

    indeps.add_output('gamma_le', bp.gamma_le)
    indeps.add_output('x_c', bp.x_c)
    indeps.add_output('y_c', bp.y_c)
    indeps.add_output('alpha_te', bp.alpha_te)
    #indeps.add_output('z_te', bp.z_te)

    indeps.add_output('b_8', bp.b_8)
    indeps.add_output('b_15', bp.b_15)
    indeps.add_output('b_0', bp.b_0)
    indeps.add_output('b_2', bp.b_2)
    indeps.add_output('b_17', bp.b_17)

    prob.model.add_subsystem('airfoil_cfd', AirfoilCFD())

    prob.model.connect('r_le', 'airfoil_cfd.r_le')
    prob.model.connect('beta_te', 'airfoil_cfd.beta_te')
    prob.model.connect('x_t', 'airfoil_cfd.x_t')

    prob.model.connect('gamma_le', 'airfoil_cfd.gamma_le')
    prob.model.connect('x_c', 'airfoil_cfd.x_c')
    prob.model.connect('y_c', 'airfoil_cfd.y_c')
    prob.model.connect('alpha_te', 'airfoil_cfd.alpha_te')
    #prob.model.connect('z_te', 'airfoil_cfd.z_te')

    prob.model.connect('b_8', 'airfoil_cfd.b_8')
    prob.model.connect('b_15', 'airfoil_cfd.b_15')
    prob.model.connect('b_0', 'airfoil_cfd.b_0')
    prob.model.connect('b_2', 'airfoil_cfd.b_2')
    prob.model.connect('b_17', 'airfoil_cfd.b_17')

    # setup the optimization
    prob.driver = ScipyOptimizeDriver()
    #'Nelder-Mead', 'Powell', 'CG', 'BFGS', 'Newton-CG', 'L-BFGS-B', 'TNC', 'COBYLA', 'SLSQP']
    prob.driver.options['optimizer'] = 'COBYLA'
    prob.driver.options['tol'] = 1e-6
    prob.driver.options['maxiter'] = 100000

    # setup recorder
    recorder = SqliteRecorder(WORKING_DIR + '/openMdaoLog.sql')
    prob.driver.add_recorder(recorder)
    prob.driver.recording_options['record_desvars'] = True
    prob.driver.recording_options['record_responses'] = True
    prob.driver.recording_options['record_objectives'] = True
    prob.driver.recording_options['record_constraints'] = True

    #limits and constraints
    lowerPro = 0.9
    upperPro = 1.1
    prob.model.add_design_var('r_le', lower=-0.1, upper=-0.015)
    prob.model.add_design_var('beta_te', lower=0, upper=0.3)
    #prob.model.add_design_var('dz_te', lower=0., upper=0.)
    prob.model.add_design_var('x_t', lower=0.25, upper=0.4)
    #prob.model.add_design_var('y_t')#, lower=0.075, upper=0.09)

    prob.model.add_design_var('gamma_le', lower=0.05, upper=0.4)
    prob.model.add_design_var('x_c', lower=0.2, upper=0.5)
    prob.model.add_design_var('y_c', lower=0., upper=0.04)
    prob.model.add_design_var('alpha_te', lower=-0.5, upper=0)
    #prob.model.add_design_var('z_te')#, lower=0., upper=0.)

    prob.model.add_design_var('b_8', lower=0.0000001, upper=0.06)
    prob.model.add_design_var('b_15', lower=0.2, upper=1.)
    prob.model.add_design_var('b_0', lower=0., upper=0.3)
    prob.model.add_design_var('b_2', lower=-.1, upper=0.7)
    prob.model.add_design_var('b_17', lower=0.7, upper=1.)

    prob.model.add_objective('airfoil_cfd.c_d', scaler=1)

    prob.model.add_constraint('airfoil_cfd.cabin_height', lower=cabinHeigth * 0.99, upper=cabinHeigth*1.05)
    prob.model.add_constraint('airfoil_cfd.c_l', lower=0.145, upper=.155)
    prob.model.add_constraint('airfoil_cfd.c_m', lower=-0.05, upper=99.)

    write_to_log('iterations,time,c_l,c_d,c_m,CL/CD,cfdIterations,cabin_height,offsetFront,angle,r_le,beta_te,x_t,y_t,gamma_le,x_c,y_c,alpha_te,z_te,b_8,b_15,b_0,b_17,b_2]))')

    prob.setup()
    prob.set_solver_print(level=0)
    prob.model.approx_totals()
    prob.run_driver()

    print('done')
    print('cabin frontOffset: ' + str(prob['airfoil_cfd.offsetFront']))
    print('cabin angle: ' + str(-1. * prob['airfoil_cfd.angle']) + ' deg')

    print('c_l= ' + str(prob['airfoil_cfd.c_l']))
    print('c_d= ' + str(prob['airfoil_cfd.c_d']))
    print('c_m= ' + str(prob['airfoil_cfd.c_m']))

    print('execution counts airfoil cfd: ' + str(prob.model.airfoil_cfd.executionCounter))



if __name__ == '__main__':
    cabinLength = 0.55
    cabinHeigth = 0.13
    runOpenMdao()
