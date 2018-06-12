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
from airfoil.Airfoil import Airfoil
from airfoil.BPAirfoil import BPAirfoil

from openmdao.api import Problem, ScipyOptimizeDriver, IndepVarComp, ExplicitComponent
import matplotlib.pyplot as plt

from openmdao.core.problem import Problem
from openmdao.core.indepvarcomp import IndepVarComp

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
        bzFoil.y_t = inputs['bz_y_t']
        # check how high the cabin can be
        height, maxHeight = self.fit_cabin(inputs['offsetFront'], inputs['angle'])
        if not bzFoil.valid:
            print('ANALYSIS ERROR !')
            outputs['height'] = 1.
            outputs['heightLoss'] = 1.
        else:
            outputs['height'] = height #yMaxTop- yMinButtom
            outputs['heightLoss'] = maxHeight - height
        self.executionCounter += 1
        print(str(self.executionCounter) + '\t' + str(outputs['heightLoss']) + '\t' + str(inputs['bz_y_t']) + '\t' + str(outputs['height']))


def run_cabin_opti(show_plot=False):
    prob = Problem()

    #first guesses here
    indeps = prob.model.add_subsystem('indeps', IndepVarComp(), promotes=['*'])
    indeps.add_output('offsetFront', .1)
    indeps.add_output('angle', 0.)
    indeps.add_output('bz_y_t', bzFoil.y_t)

    prob.model.add_subsystem('profile_fitter', ProfileFitting())
    prob.model.connect('offsetFront', 'profile_fitter.offsetFront')
    prob.model.connect('angle', 'profile_fitter.angle')
    prob.model.connect('bz_y_t', 'profile_fitter.bz_y_t')

    # setup the optimization
    prob.driver = ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'SLSQP'
    prob.driver.options['tol'] = 1e-6
    prob.driver.options['maxiter'] = 1000

    #limits and constraints
    prob.model.add_design_var('offsetFront', lower=0., upper=1.)
    prob.model.add_design_var('angle', lower=-10, upper=10)
    prob.model.add_design_var('bz_y_t', lower=0., upper=1.)
    prob.model.add_objective('profile_fitter.heightLoss', scaler=1)
    prob.model.add_constraint('profile_fitter.height', lower= cabinHeigth*0.95, upper=cabinHeigth*1.05)

    prob.setup()
    prob.run_driver()

    #print and plot results
    print('cabin frontOddset: ' + str(prob['offsetFront']))
    print('cabin height: ' + str(prob['profile_fitter.height']))
    print('cabin angle: ' + str(-1. * prob['angle']) + ' deg')
    print('execution counts profile fitter: ' + str(prob.model.profile_fitter.executionCounter))

    if show_plot:
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
    return prob['bz_y_t'], prob['profile_fitter.height'], prob['angle'], prob['offsetFront']


if __name__ == '__main__':
    run_cabin_opti(show_plot=True)