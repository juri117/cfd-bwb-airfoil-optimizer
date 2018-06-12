# ==============================================================================
# description     :implements openMDAO Component, loads variables from cpacs
# author          :Juri Bieler
# date            :2018-04-17
# version         :0.01
# notes           :
# python_version  :2.7
# ==============================================================================

from __future__ import print_function
import sys
sys.path.insert(0, '../OpenMDAO')
sys.path.insert(0, '../pyDOE2')

import os
import numpy as np
from airfoil.Airfoil import Airfoil
from airfoil.BPAirfoil import BPAirfoil

#from openmdao.api import Group, Problem, Component, IndepVarComp
from openmdao.core.explicitcomponent import ExplicitComponent
from openmdao.api import Problem, ScipyOptimizeDriver, IndepVarComp, ExplicitComponent
from openmdao.drivers.pyoptsparse_driver import pyOptSparseDriver
import matplotlib.pyplot as plt

from openmdao.core.problem import Problem
from openmdao.core.group import Group
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.analysis_error import AnalysisError

#import libaries.readInput as readInputs
#from libaries.readInput import ParamValue
#value = readInputs.readInputFile()


bzFoil = BPAirfoil()
if os.path.isfile('../dataIn/airfoil.txt'):
    bzFoil.read_parameters_from_file('../dataIn/airfoil.txt')

air = Airfoil(None)
top, buttom = bzFoil.get_cooridnates_top_buttom(500)
if bzFoil.valid == False:
    print('ERROR: invalid bzArifoil')
air.set_coordinates(top, buttom)

cabinLength = 0.55
cabinHeigth = 0.14

class CabinArea(ExplicitComponent):

    def setup(self):
        #####################
        ### openMDAO init ###
        ### INPUTS
        self.add_input('height', val=0., desc='...')
        #self.add_input('length', val=1.0, desc='...')
        ### OUTPUTS
        self.add_output('area', val=.2)

        self.declare_partials('*', '*', method='fd')
        self.executionCounter = 0

    def compute(self, inputs, outputs):
        outputs['area'] = inputs['height'] * cabinLength #inputs['length']
        print(str(outputs['area']))
        self.executionCounter += 1

class ProfileFitting(ExplicitComponent):

    def setup(self):
        #####################
        ### openMDAO init ###
        ### INPUTS
        self.add_input('offsetFront', val=0.1, desc='...')
        self.add_input('length', val=1.0, desc='...')
        self.add_input('angle', val=1.0, desc='...')
        self.add_input('bz_y_t', val=.2, desc='...')
        ### OUTPUTS
        self.add_output('height', val=0.0)
        self.add_output('heightLoss', val=0.0)

        self.declare_partials('*', '*', method='fd')
        self.executionCounter = 0

    def fit_cabin(self, xFront, angle):
        top, buttom = bzFoil.get_cooridnates_top_buttom(500)
        if bzFoil.valid == False:
            return False, False
        xBack = xFront + cabinLength  # inputs['length']
        air.set_coordinates(top, buttom)
        air.rotate(angle)
        yMinButtom = max(air.get_buttom_y(xFront), air.get_buttom_y(xBack))
        yMaxTop = min(air.get_top_y(xFront), air.get_top_y(xBack))
        maxHeight = max(air.get_top_y(xFront) - air.get_buttom_y(xFront), air.get_top_y(xBack) - air.get_buttom_y(xBack))
        height = yMaxTop - yMinButtom
        return height, maxHeight

    def compute(self, inputs, outputs):
        bzError = False
        bzFoil.y_t = inputs['bz_y_t']
        # check how high the cabin can be
        height, maxHeight = self.fit_cabin(inputs['offsetFront'], inputs['angle'])
        if not bzFoil.valid:
            bzError = True

        #if bzFoil.valid:
        #    iterCounter = 0
        #    while (abs(height - cabinHeigth) > 1e-9):
        #        bzFoil.y_t += cabinHeigth - height
        #        height = self.fit_cabin(inputs['offsetFront'], inputs['angle'])
        #        if height == False or iterCounter > 200:
        #            bzError = True
        #            break
        #        iterCounter += 1
        #    print('used Iterations: ' + str(iterCounter))
        #else:
        #    bzError = True

        if bzError:
            print('ANALYSIS ERROR !')
            #raise AnalysisError()
            outputs['height'] = 1.
            outputs['heightLoss'] = 1.
            #outputs['bz_y_t'] = 999.
        else:
            outputs['height'] = height #yMaxTop- yMinButtom
            outputs['heightLoss'] = maxHeight - height
            #outputs['bz_y_t'] = bzFoil.y_t
        self.executionCounter += 1
        print(str(self.executionCounter) + '\t' + str(outputs['heightLoss']) + '\t' + str(inputs['bz_y_t']) + '\t' + str(outputs['height']))

### TEST PROGRAM

def run_cabin_opti():
    prob = Problem()

    #first guesses here
    indeps = prob.model.add_subsystem('indeps', IndepVarComp(), promotes=['*'])
    #indeps.add_output('length', .5)
    indeps.add_output('offsetFront', .1)
    indeps.add_output('angle', 0.)
    indeps.add_output('bz_y_t', bzFoil.y_t)

    prob.model.add_subsystem('profile_fitter', ProfileFitting())
    #prob.model.add_subsystem('cabin_area', CabinArea())

    #prob.model.connect('profile_fitter.height', 'cabin_area.height')
    #prob.model.connect('length', ['profile_fitter.length', 'cabin_area.length'])
    prob.model.connect('offsetFront', 'profile_fitter.offsetFront')
    prob.model.connect('angle', 'profile_fitter.angle')
    prob.model.connect('bz_y_t', 'profile_fitter.bz_y_t')

    # setup the optimization
    #prob.driver = pyOptSparseDriver()#ScipyOptimizeDriver()
    #prob.driver.options['optimizer'] = 'ALPSO'

    # setup the optimization
    prob.driver = ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'SLSQP'
    prob.driver.options['tol'] = 1e-9
    prob.driver.options['maxiter'] = 100000

    #limits and constraints
    #prob.model.add_design_var('length', lower=0.01, upper=0.99)
    prob.model.add_design_var('offsetFront', lower=0., upper=1.)
    prob.model.add_design_var('angle', lower=-10, upper=10)
    prob.model.add_design_var('bz_y_t', lower=0., upper=1.)
    prob.model.add_objective('profile_fitter.heightLoss', scaler=1)
    #here a maximum cabin height can be set (e.g. upper=0.08)
    prob.model.add_constraint('profile_fitter.height', lower= cabinHeigth*0.95, upper=cabinHeigth*1.05)

    prob.setup()
    prob.run_driver()

    #print and plot results
    #print('cabin area: ' + str(prob['cabin_area.area']))
    print('cabin frontOddset: ' + str(prob['offsetFront']))
    #print('cabin length: ' + str(prob['length']))
    print('cabin height: ' + str(prob['profile_fitter.height']))
    print('cabin angle: ' + str(-1. * prob['angle']) + ' deg')
    #print('execution counts cabin area: ' + str(prob.model.cabin_area.executionCounter))
    print('execution counts profile fitter: ' + str(prob.model.profile_fitter.executionCounter))

    air.rotate(prob['angle'])
    px_ol = prob['offsetFront']
    py_ol = air.get_top_y(px_ol)
    (px_ol, py_ol) = air.rotatePoint((0, 0), (px_ol, py_ol), prob['angle'])
    px_ul = prob['offsetFront']
    py_ul = air.get_buttom_y(px_ul)
    (px_ul, py_ul) = air.rotatePoint((0, 0), (px_ul, py_ul), prob['angle'])
    px_or = prob['offsetFront'] + cabinLength
    py_or = air.get_top_y(px_or)
    (px_or, py_or) = air.rotatePoint((0, 0), (px_or, py_or), prob['angle'])
    px_ur = prob['offsetFront'] + cabinLength
    py_ur = air.get_buttom_y(px_ur)
    (px_ur, py_ur) = air.rotatePoint((0, 0), (px_ur, py_ur), prob['angle'])
    #value['px_ol'] = ParamValue('px_ol', px_ol, '', 'x of the upper left corner of the cabin normed to length 1')
    #value['py_ol'] = ParamValue('py_ol', py_ol, '', '')
    #value['px_ul'] = ParamValue('px_ul', px_ul, '', '')
    #value['py_ul'] = ParamValue('py_ul', py_ul, '', '')
    #value['px_or'] = ParamValue('px_or', px_or, '', '')
    #value['py_or'] = ParamValue('py_or', py_or, '', '')

    print('Koordinates:')
    print('ol: ' + str(px_ol) + ', ' + str(py_ol))
    print('ul: ' + str(px_ul) + ', ' + str(py_ul))
    print('or: ' + str(px_or) + ', ' + str(py_or))
    print('ur: ' + str(px_ur) + ', ' + str(py_ur))

    ax = air.plotAirfoil(showPlot=False)
    xFront = prob['offsetFront']
    xBack = xFront + cabinLength
    height = prob['profile_fitter.height']
    yLowFront = air.get_buttom_y(xFront)
    yLowBack = air.get_buttom_y(xBack)
    yLowMax = max(yLowFront, yLowBack)
    ax.plot([xFront, xBack, xBack, xFront, xFront], [yLowMax, yLowMax, yLowMax+height, yLowMax+height, yLowMax], '-r')

    ax.plot([px_ol, px_ul, px_or, px_ur], [py_ol, py_ul, py_or, py_ur], 'xr')

    plt.show()

if __name__ == '__main__':
    run_cabin_opti()