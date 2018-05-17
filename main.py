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
from constants import *

from openmdao.core.explicitcomponent import ExplicitComponent
from openmdao.api import Problem, ScipyOptimizeDriver, IndepVarComp, ExplicitComponent, SqliteRecorder
import matplotlib.pyplot as plt
from datetime import datetime

from openmdao.core.problem import Problem
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.analysis_error import AnalysisError

# create working dir if necessary
if not os.path.isdir(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# check if gmsh exe exists
if not os.path.isfile(GMSH_EXE_PATH):
    print('gmsh executable could not be found in: ' + GMSH_EXE_PATH)
    sys.exit(0)

#create working dir if necessary
if not os.path.isdir(WORKING_DIR):
    os.mkdir(WORKING_DIR)

#check if gmsh exe exists
if not os.path.isfile(GMSH_EXE_PATH):
    print('gmsh executable could not be found in: ' + GMSH_EXE_PATH)
    sys.exit(0)

LOG_FILE_PATH = WORKING_DIR + '/om_iterations_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.csv'

MACH_NUMBER = 0.78 #mach number cruise
#compensate sweep deg
SWEEP_LEADING_EDGE = 45

MACH_SWEEP_COMPENSATED = MACH_NUMBER * math.sin(SWEEP_LEADING_EDGE * math.pi / 180)
print('sweep compensated mach number: ' + str(MACH_SWEEP_COMPENSATED))

MACH_NUM = 0.71
REF_LENGTH = 36. # cd, cl no effect I guess
REF_AREA = 36. # cd, cl get smaller

SCALE = 36. # cd, cl get bigger

### default config for SU2 run ###
config = dict()
config['PHYSICAL_PROBLEM'] = 'EULER'
config['MACH_NUMBER'] = str(MACH_SWEEP_COMPENSATED)
config['AOA'] = str(2.0)
config['FREESTREAM_PRESSURE'] = str(24999.8) #for altitude 10363 m
config['FREESTREAM_TEMPERATURE'] = str(220.79) #for altitude 10363 m
#config['GAS_CONSTANT'] = str(287.87)
#config['REF_LENGTH'] = str(1.0)
#config['REF_AREA'] = str(1.0)
config['MARKER_EULER'] = '( airfoil )'
config['MARKER_FAR'] = '( farfield )'
config['EXT_ITER'] = str(5000)
config['OUTPUT_FORMAT'] = 'PARAVIEW'
config['MG_DAMP_RESTRICTION'] = str(1.)
config['MG_DAMP_PROLONGATION'] = str(1.)

config['REF_LENGTH'] = str(REF_LENGTH)
config['REF_AREA'] = str(REF_AREA)

cabinLength = 0.55
cabinHeigth = 0.13

class AirfoilCFD(ExplicitComponent):

    def setup(self):
        ######################
        ### needed Objects ###
        self.bzFoil = BPAirfoil()


        #####################
        ### openMDAO init ###
        ### INPUTS

        self.add_input('r_le', val=-0.05, desc='nose radius')
        self.add_input('beta_te', val=0.1, desc='thickness angle trailing edge')
        #self.add_input('dz_te', val=0., desc='thickness trailing edge')
        self.add_input('x_t', val=0.3, desc='dickenruecklage')
        self.add_input('y_t', val=0.1, desc='max thickness')

        self.add_input('gamma_le', val=0.5, desc='camber angle leading edge')
        self.add_input('x_c', val=0.5, desc='woelbungsruecklage')
        self.add_input('y_c', val=0.1, desc='max camber')
        self.add_input('alpha_te', val=-0.1, desc='camber angle trailing edge')
        self.add_input('z_te', val=0., desc='camber trailing edge')

        # bezier parameters
        self.add_input('b_8', val=0.05, desc='')
        self.add_input('b_15', val=0.75, desc='')
        self.add_input('b_0', val=0.1, desc='')
        self.add_input('b_2', val=0.25, desc='')
        self.add_input('b_17', val=0.9, desc='')

        # just for plotin
        self.add_input('offsetFront', val=0.1, desc='...')
        self.add_input('angle', val=.0, desc='...')

        ### OUTPUTS
        self.add_output('c_d', val=.2)
        self.add_output('c_l', val=.2)
        self.add_output('c_m', val=.2)

        self.declare_partials('*', '*', method='fd')
        self.executionCounter = 0

    def compute(self, inputs, outputs):
        self.bzFoil.r_le = inputs['r_le']
        self.bzFoil.beta_te = inputs['beta_te']
        #self.bzFoil.dz_te = inputs['dz_te']
        self.bzFoil.x_t = inputs['x_t']
        self.bzFoil.y_t = inputs['y_t']

        self.bzFoil.gamma_le = inputs['gamma_le']
        self.bzFoil.x_c = inputs['x_c']
        self.bzFoil.y_c = inputs['y_c']
        self.bzFoil.alpha_te = inputs['alpha_te']
        self.bzFoil.z_te = inputs['z_te']

        self.bzFoil.b_8 = inputs['b_8']
        self.bzFoil.b_15 = inputs['b_15']
        self.bzFoil.b_0 = inputs['b_0']
        self.bzFoil.b_2 = inputs['b_2']
        self.bzFoil.b_17 = inputs['b_17']

        projectName = 'iter_%09d' % self.executionCounter
        cfd = CFDrun(projectName)

        airFoilCoords = self.bzFoil.generate_airfoil(500,
                                                     show_plot=False,
                                                     save_plot_path=WORKING_DIR+'/'+projectName+'/airfoil.png',
                                                     param_dump_file=WORKING_DIR+'/'+projectName+'/airfoil.txt')
        self.bzFoil.plot_airfoil_with_cabin(inputs['offsetFront'],
                                            cabinLength,
                                            cabinHeigth,
                                            inputs['angle'],
                                            show_plot=False,
                                            save_plot_path=WORKING_DIR+'/'+projectName+'/airfoil_cabin.png')
        if not self.bzFoil.valid:
            raise AnalysisError('AirfoilCFD: invalid BPAirfoil')

        top, buttom = self.bzFoil.get_cooridnates_top_buttom(500)
        #self.air.set_coordinates(top, buttom)
        cfd.set_airfoul_coords(top, buttom)

        cfd.construct2d_generate_mesh(scale=SCALE, savePlot=False)
        cfd.su2_fix_mesh()
        cfd.su2_solve(config)
        #totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()
        results = cfd.su2_parse_iteration_result()
        cfd.clean_up()

        if results['CD'] <= 0. or results['CD'] > 100.:
            raise AnalysisError('AirfoilCFD: c_d is out of range (cfd failed)')

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
                     + str(inputs['offsetFront']) + ','
                     + str(inputs['angle']) + ','
                     + str(inputs['r_le']) + ','
                     + str(inputs['beta_te']) + ','
                     + str(inputs['x_t']) + ','
                     + str(inputs['y_t']) + ','
                     + str(inputs['gamma_le']) + ','
                     + str(inputs['x_c']) + ','
                     + str(inputs['y_c']) + ','
                     + str(inputs['alpha_te']) + ','
                     + str(inputs['z_te']) + ','
                     + str(inputs['b_8']) + ','
                     + str(inputs['b_15']) + ','
                     + str(inputs['b_0']) + ','
                     + str(inputs['b_17']) + ','
                     + str(inputs['b_2']))
        self.executionCounter += 1

class CabinFitting(ExplicitComponent):

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
        #self.add_input('dz_te', val=0., desc='thickness trailing edge')
        self.add_input('x_t', val=0.3, desc='dickenruecklage')
        #self.add_input('y_t', val=0.1, desc='max thickness')

        self.add_input('gamma_le', val=0.5, desc='camber angle leading edge')
        self.add_input('x_c', val=0.5, desc='woelbungsruecklage')
        self.add_input('y_c', val=0.1, desc='max camber')
        self.add_input('alpha_te', val=-0.1, desc='camber angle trailing edge')
        self.add_input('z_te', val=0., desc='camber trailing edge')

        # bezier parameters
        self.add_input('b_8', val=0.05, desc='')
        self.add_input('b_15', val=0.75, desc='')
        self.add_input('b_0', val=0.1, desc='')
        self.add_input('b_2', val=0.25, desc='')
        self.add_input('b_17', val=0.9, desc='')

        self.add_input('offsetFront', val=0.1, desc='...')
        #self.add_input('length', val=.5, desc='...')
        self.add_input('angle', val=.0, desc='...')

        ### OUTPUTS
        #self.add_output('height', val=0.0)
        self.add_output('y_t', val=.1)

        self.declare_partials('*', '*', method='fd')
        self.executionCounter = 0

    def compute(self, inputs, outputs):
        self.bzFoil.r_le = inputs['r_le']
        self.bzFoil.beta_te = inputs['beta_te']
        #self.bzFoil.dz_te = inputs['dz_te']
        self.bzFoil.x_t = inputs['x_t']
        #self.bzFoil.y_t = 0.1 #inputs['y_t']

        self.bzFoil.gamma_le = inputs['gamma_le']
        self.bzFoil.x_c = inputs['x_c']
        self.bzFoil.y_c = inputs['y_c']
        self.bzFoil.alpha_te = inputs['alpha_te']
        self.bzFoil.z_te = inputs['z_te']

        self.bzFoil.b_8 = inputs['b_8']
        self.bzFoil.b_15 = inputs['b_15']
        self.bzFoil.b_0 = inputs['b_0']
        self.bzFoil.b_2 = inputs['b_2']
        self.bzFoil.b_17 = inputs['b_17']
        xFront = inputs['offsetFront']
        xBack = xFront + cabinLength #inputs['length']
        angle = inputs['angle']

        top, buttom = self.bzFoil.get_cooridnates_top_buttom(500)
        self.air.set_coordinates(top, buttom)
        self.air.rotate(angle)
        yMinButtom = max(self.air.get_buttom_y(xFront), self.air.get_buttom_y(xBack))
        yMaxTop = min(self.air.get_top_y(xFront), self.air.get_top_y(xBack))
        height = yMaxTop - yMinButtom
        iterCounter = 0
        while(abs(height - cabinHeigth) > 0.0001):
            self.bzFoil.y_t += cabinHeigth - height
            top, buttom = self.bzFoil.get_cooridnates_top_buttom(500)
            self.air.set_coordinates(top, buttom)
            self.air.rotate(angle)
            yMinButtom = max(self.air.get_buttom_y(xFront), self.air.get_buttom_y(xBack))
            yMaxTop = min(self.air.get_top_y(xFront), self.air.get_top_y(xBack))
            height = yMaxTop - yMinButtom
            iterCounter += 1
        if not self.bzFoil.valid:
            raise AnalysisError('CabinFitting: invalid BPAirfoil')

        #yMinButtom = max(self.air.get_buttom_y(xFront), self.air.get_buttom_y(xBack))
        #yMaxTop = min(self.air.get_top_y(xFront), self.air.get_top_y(xBack))
        #outputs['height'] = yMaxTop - yMinButtom
        print('cabin fitting needed ' + str(iterCounter) + ' iterations')
        print('cabinHeight= ' + str(height))
        outputs['y_t'] = self.bzFoil.y_t
        print('new y_t= ' + str(outputs['y_t']))
        self.executionCounter += 1


def write_to_log(outStr):
    outStr = outStr.replace('[', '')
    outStr = outStr.replace(']', '')
    outputF = open(LOG_FILE_PATH, 'a') #'a' so we append the file
    outputF.write(outStr + '\n')
    outputF.close()


if __name__ == '__main__':
    prob = Problem()

    #first guesses here
    indeps = prob.model.add_subsystem('indeps', IndepVarComp(), promotes=['*'])
    #indeps.add_output('length', .5)
    #indeps.add_output('height', .1)
    indeps.add_output('offsetFront', .11)
    indeps.add_output('angle', 0.)


    # load defaults from BPAirfoil
    bp = BPAirfoil()
    # read last optimization result if available (has to be copied here manually)
    if os.path.isfile(INPUT_DIR+'/'+'airfoil.txt'):
        bp.read_parameters_from_file(INPUT_DIR+'/'+'airfoil.txt')
    indeps.add_output('r_le', bp.r_le)
    indeps.add_output('beta_te', bp.beta_te)
    #indeps.add_output('dz_te', bp.dz_te) # we want a sharp trailing edge
    indeps.add_output('x_t', bp.x_t)
    #indeps.add_output('y_t', bp.y_t) # this is adapted by cabinFitter

    indeps.add_output('gamma_le', bp.gamma_le)
    indeps.add_output('x_c', bp.x_c)
    indeps.add_output('y_c', bp.y_c)
    indeps.add_output('alpha_te', bp.alpha_te)
    indeps.add_output('z_te', bp.z_te)

    indeps.add_output('b_8', bp.b_8)
    indeps.add_output('b_15', bp.b_15)
    indeps.add_output('b_0', bp.b_0)
    indeps.add_output('b_2', bp.b_2)
    indeps.add_output('b_17', bp.b_17)

    prob.model.add_subsystem('airfoil_cfd', AirfoilCFD())
    prob.model.add_subsystem('cabin_fitter', CabinFitting())

    #prob.model.connect('length', 'cabin_fitter.length')
    prob.model.connect('offsetFront', ['cabin_fitter.offsetFront', 'airfoil_cfd.offsetFront'])
    prob.model.connect('angle', ['cabin_fitter.angle', 'airfoil_cfd.angle'])

    prob.model.connect('r_le', ['airfoil_cfd.r_le', 'cabin_fitter.r_le'])
    prob.model.connect('beta_te', ['airfoil_cfd.beta_te', 'cabin_fitter.beta_te'])
    #prob.model.connect('dz_te', ['airfoil_cfd.dz_te', 'cabin_fitter.dz_te'])
    prob.model.connect('x_t', ['airfoil_cfd.x_t', 'cabin_fitter.x_t'])

    prob.model.connect('cabin_fitter.y_t', 'airfoil_cfd.y_t')

    prob.model.connect('gamma_le', ['airfoil_cfd.gamma_le', 'cabin_fitter.gamma_le'])
    prob.model.connect('x_c', ['airfoil_cfd.x_c', 'cabin_fitter.x_c'])
    prob.model.connect('y_c', ['airfoil_cfd.y_c', 'cabin_fitter.y_c'])
    prob.model.connect('alpha_te', ['airfoil_cfd.alpha_te', 'cabin_fitter.alpha_te'])
    prob.model.connect('z_te', ['airfoil_cfd.z_te', 'cabin_fitter.z_te'])

    prob.model.connect('b_8', ['airfoil_cfd.b_8', 'cabin_fitter.b_8'])
    prob.model.connect('b_15', ['airfoil_cfd.b_15', 'cabin_fitter.b_15'])
    prob.model.connect('b_0', ['airfoil_cfd.b_0', 'cabin_fitter.b_0'])
    prob.model.connect('b_2', ['airfoil_cfd.b_2', 'cabin_fitter.b_2'])
    prob.model.connect('b_17', ['airfoil_cfd.b_17', 'cabin_fitter.b_17'])

    # setup the optimization
    prob.driver = ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'SLSQP'
    prob.driver.options['tol'] = 1e-9
    prob.driver.options['maxiter'] = 100000

    # setup recorder
    recorder = SqliteRecorder(WORKING_DIR + '/openMdaoLog.sql')
    prob.driver.add_recorder(recorder)
    prob.driver.recording_options['record_desvars'] = True
    prob.driver.recording_options['record_responses'] = True
    prob.driver.recording_options['record_objectives'] = True
    prob.driver.recording_options['record_constraints'] = True

    #limits and constraints
    #prob.model.add_design_var('length', lower=0.4, upper=0.5)

    lowerPro = 0.9
    upperPro = 1.1

    prob.model.add_design_var('r_le', upper=0.)#, lower=-1*bp.y_t, upper=0)
    prob.model.add_design_var('beta_te')#, lower=bp.beta_te*lowerPro, upper=bp.beta_te*upperPro)
    #ToDo: dz_te constant to 0, no thickness at trailing edge
    #prob.model.add_design_var('dz_te', lower=0., upper=0.)
    prob.model.add_design_var('x_t', lower=0.)#, lower=0.25, upper=0.5)
    #prob.model.add_design_var('y_t', lower=0.075, upper=0.09)

    prob.model.add_design_var('gamma_le')#, lower=bp.gamma_le*lowerPro, upper=bp.gamma_le*upperPro)
    prob.model.add_design_var('x_c')#, lower=bp.x_c*lowerPro, upper=bp.x_c*upperPro)
    prob.model.add_design_var('y_c')#, lower=bp.y_c*lowerPro, upper=bp.y_c*upperPro)
    prob.model.add_design_var('alpha_te')#, lower=bp.alpha_te*upperPro, upper=bp.alpha_te*lowerPro)
    prob.model.add_design_var('z_te')#, lower=0., upper=0.)

    prob.model.add_design_var('b_8')#, lower=bp.b_8*lowerPro, upper=bp.b_8*upperPro)
    prob.model.add_design_var('b_15')#, lower=bp.b_15*lowerPro, upper=bp.b_15*upperPro)
    prob.model.add_design_var('b_0')#, lower=bp.b_0*lowerPro, upper=bp.b_0*upperPro)
    prob.model.add_design_var('b_2')#, lower=bp.b_2*lowerPro, upper=bp.b_2*upperPro)
    prob.model.add_design_var('b_17')#, lower=bp.b_17*lowerPro, upper=bp.b_17*upperPro)

    prob.model.add_design_var('offsetFront', lower=0.0, upper=.5)
    prob.model.add_design_var('angle', lower=-5, upper=5)

    prob.model.add_objective('airfoil_cfd.c_d', scaler=1)

    #prob.model.add_constraint('cabin_fitter.height', lower=0.090, upper=0.15)

    prob.model.add_constraint('airfoil_cfd.c_l', lower=0.23, upper=.3)
    prob.model.add_constraint('airfoil_cfd.c_m', lower=-0.05, upper=99.)

    write_to_log('iterations,time,c_l,c_d,c_m,CL/CD,cfdIterations,offsetFront,angle,r_le,beta_te,x_t,y_t,gamma_le,x_c,y_c,alpha_te,z_te,b_8,b_15,b_0,b_17,b_2]))')

    prob.setup()
    prob.set_solver_print(level=0)
    prob.model.approx_totals()
    prob.run_driver()

    print('done')
    print('cabin frontOddset: ' + str(prob['offsetFront']))
    print('cabin angle: ' + str(-1. * prob['angle']) + ' deg')

    print('c_l= ' + str(prob['airfoil_cfd.c_l']))
    print('c_d= ' + str(prob['airfoil_cfd.c_d']))
    print('c_m= ' + str(prob['airfoil_cfd.c_m']))

    print('execution counts cabin fitter: ' + str(prob.model.cabin_fitter.executionCounter))
    print('execution counts airfoil cfd: ' + str(prob.model.airfoil_cfd.executionCounter))


