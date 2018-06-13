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

import numpy as np
import os
from airfoil.Airfoil import Airfoil
from airfoil.BPAirfoil import BPAirfoil

import matplotlib.pyplot as plt

from scipy.optimize import basinhopping
from scipy.optimize import minimize

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
executionCounter = 0

def fit_cabin(xFront, angle):
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

def calc_heightLoss(inputs):
    angle = inputs[2]
    offsetFront = inputs[1]
    bzFoil.y_t = inputs[0]
    # check how high the cabin can be
    height, maxHeight = fit_cabin(offsetFront, angle)
    if not bzFoil.valid:
        print('ANALYSIS ERROR !')
        height = 1.
        heightLoss = 1.
        heightLoss = float('NaN')
    else:
        height = height #yMaxTop- yMinButtom
        heightLoss = max(abs(maxHeight - cabinHeigth), abs(height - cabinHeigth))
    #executionCounter += 1
    print(str(0) + '\t' + str(heightLoss) + '\t' + str(bzFoil.y_t) + '\t' + str(angle)+ '\t' + str(offsetFront))
    return heightLoss

def run_cabin_opti(show_plot=False):

    x0 = [0.08, 0.1, 0.]
    res = minimize(calc_heightLoss, x0, method='SLSQP', tol=1e-11)
    minimizer_kwargs = {"method": "BFGS"}

    #res = basinhopping(calc_heightLoss, x0, minimizer_kwargs=minimizer_kwargs)
    angle = res.x[2]
    y_t = res.x[0]
    offsetFront = res.x[1]

    bzFoil.y_t = y_t
    height, maxHeight = fit_cabin(offsetFront, angle)

    print('y_t: ' + str(y_t))
    print('offsetFront: ' + str(offsetFront))
    print('angle: ' + str(angle))
    print('height: ' + str(height))

    if show_plot:
        #angle = 0.
        #offsetFront = 0.11
        length = 0.55
        #air = Airfoil(INPUT_DIR + '/' + 'airfoil.dat')

        top, buttom = bzFoil.get_cooridnates_top_buttom(500)
        if bzFoil.valid == False:
            return False, False
        air.set_coordinates(top, buttom)

        air.rotate(angle)
        # air.rotate(angle)
        px_ul = offsetFront
        px_ur = offsetFront + length
        py_ul = max(air.get_buttom_y(px_ul), air.get_buttom_y(px_ur))
        py_ur = py_ul
        px_ol = px_ul
        px_or = px_ur
        py_ol = min(air.get_top_y(px_ol), air.get_top_y(px_or))
        py_or = py_ol
        print('geometrical calculated height = ' + str(py_ol - py_ul))
        (px_ol, py_ol) = air.rotatePoint((0, 0), (px_ol, py_ol), -angle)
        (px_ul, py_ul) = air.rotatePoint((0, 0), (px_ul, py_ul), -angle)

        # py_ur = air.get_buttom_y(px_ur)
        # px_or = px_ur
        # py_or = py_ur + height
        (px_or, py_or) = air.rotatePoint((0, 0), (px_or, py_or), -angle)
        (px_ur, py_ur) = air.rotatePoint((0, 0), (px_ur, py_ur), -angle)
        air.rotate(0.)
        fig, ax = air.plotAirfoil(showPlot=False)
        ax.plot([px_ol, px_ul, px_ur, px_or, px_ol], [py_ol, py_ul, py_ur, py_or, py_ol], 'rx-')
        plt.show()

    return y_t, height, angle, offsetFront

if __name__ == '__main__':
    run_cabin_opti(show_plot=True)