# ==============================================================================
# description     :creates airfoil coordinates with bezier-parsec parametrization (http://pubs.sciepub.com/ajme/2/4/1/)
# author          :Lennart Kracke
# date            :2018-04-24
# version         :0.1a
# notes           :420 blaze it
# python_version  :3.6
# ==============================================================================

# imports

import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from operator import add
from Airfoil import Airfoil


class BPAirfoil:

    def __init__(self):
        self.valid = True
        # necessary variables
        # aerodynamic parameters
        self.r_le = -0.025  # nose radius
        self.beta_te = 0.15  # thickness angle trailing edge
        self.dz_te = 0  # thickness trailing edge
        self.x_t = 0.33  # dickenruecklage
        self.y_t = 0.07  # max thickness

        self.gamma_le = 0.2  # camber angle leading edge
        self.x_c = 0.5  # woelbungsruecklage
        self.y_c = 0.02  # max camber
        self.alpha_te = -.00001  # camber angle trailing edge
        self.z_te = 0.  # camber trailing edge

        # bezier parameters
        self.b_8 = 0.05
        self.b_15 = 0.75

        self.b_0 = 0.1
        self.b_2 = 0.25
        self.b_17 = 0.9
        if not (0 < self.b_8 < min(self.y_t, math.sqrt(-2 * self.r_le * self.x_t / 3))):
            print("Parameter b_8 out of bounds!")
            self.valid = False

    def generate_airfoil(self, pointCount, show_plot=True, save_plot_path='', param_dump_file=''):
        # bezier points
        # thickness leading edge
        self.x0_tle = 0
        self.y0_tle = 0
        self.x1_tle = 0
        self.y1_tle = self.b_8
        self.x2_tle = -3 * self.b_8 ** 2 / (2 * self.r_le)
        self.y2_tle = self.y_t
        self.x3_tle = self.x_t
        self.y3_tle = self.y_t

        # thickness trailing edge
        self.x0_tte = self.x_t
        self.y0_tte = self.y_t
        self.x1_tte = (7 * self.x_t + 9 * self.b_8 ** 2 / (2 * self.r_le)) / 4
        self.y1_tte = self.y_t
        self.x2_tte = 3 * self.x_t + 15 * self.b_8 ** 2 / (4 * self.r_le)
        self.y2_tte = (self.y_t + self.b_8) / 2
        self.x3_tte = self.b_15
        self.y3_tte = self.dz_te + (1 - self.b_15) * math.tan(self.beta_te)
        self.x4_tte = 1
        self.y4_tte = self.dz_te

        # camber leading edge
        self.x0_cle = 0
        self.y0_cle = 0
        self.x1_cle = self.b_0
        self.y1_cle = self.b_0 * math.tan(self.gamma_le)
        self.x2_cle = self.b_2
        self.y2_cle = self.y_c
        self.x3_cle = self.x_c
        self.y3_cle = self.y_c

        # camber trailing edge
        self.x0_cte = self.x_c
        self.y0_cte = self.y_c
        self.x1_cte = (3 * self.x_c - self.y_c * 1 / math.tan(self.gamma_le)) / 2
        self.y1_cte = self.y_c
        self.x2_cte = (-8 * self.y_c * 1 / math.tan(self.gamma_le) + 13 * self.x_c) / 6
        self.y2_cte = 5 * self.y_c / 6
        self.x3_cte = self.b_17
        self.y3_cte = self.z_te - (1 - self.b_17) * math.tan(self.alpha_te)
        self.x4_cte = 1
        self.y4_cte = self.z_te

        points = np.linspace(0, 1, 1000)
        pointsThicknessCurve = list(map(self.thicknessCurve, points))
        xThick = [i[0] for i in pointsThicknessCurve]
        yThick = [i[1] for i in pointsThicknessCurve]

        pointsCamberCurve = list(map(self.camberCurve, points))
        xCam = [i[0] for i in pointsCamberCurve]
        yCam = [i[1] for i in pointsCamberCurve]

        INTERPOL_DEG = 'linear'

        #thickInterp = interp1d(xThick, yThick, kind=INTERPOL_DEG)
        thickInterp = interp1d(np.asarray(xThick).squeeze(), np.asarray(yThick).squeeze(), kind=INTERPOL_DEG)
        #camInterp = interp1d(xCam, yCam, kind=INTERPOL_DEG)
        camInterp = interp1d(np.asarray(xCam).squeeze(), np.asarray(yCam).squeeze(), kind=INTERPOL_DEG)

        x = np.linspace(0, 1, pointCount)
        yT = thickInterp(x)
        yC = camInterp(x)

        yTop = map(add, yC, yT)
        yBut = map(add, yC, (-1. * yT))

        pltCam, = plt.plot(x, yC, '--g', label='camber')
        pltThi, = plt.plot(x, yT, '--y', label='thickness')
        pltTop, = plt.plot(x, yTop, '-r', label='airfoil top')
        pltBut, = plt.plot(x, yBut, '-b', label='airfoil buttom')
        plt.legend(handles=[pltCam, pltThi, pltTop, pltBut])
        plt.title('Airfoil')
        plt.axis('equal')

        if show_plot:
            plt.show()
        if not save_plot_path == '':
            plt.savefig(save_plot_path)
        plt.clf()
        if not param_dump_file == '':
            ouputF = open(param_dump_file, 'w')
            ouputF.write('r_le= ' + str(self.r_le) + '\n')
            ouputF.write('beta_te= ' + str(self.beta_te) + '\n')
            ouputF.write('dz_te= ' + str(self.dz_te) + '\n')
            ouputF.write('x_t= ' + str(self.x_t) + '\n')
            ouputF.write('y_t= ' + str(self.y_t) + '\n')

            ouputF.write('gamma_le= ' + str(self.gamma_le) + '\n')
            ouputF.write('x_c= ' + str(self.x_c) + '\n')
            ouputF.write('y_c= ' + str(self.y_c) + '\n')
            ouputF.write('alpha_te= ' + str(self.alpha_te) + '\n')
            ouputF.write('z_te= ' + str(self.z_te) + '\n')

            ouputF.write('b_8= ' + str(self.b_8) + '\n')
            ouputF.write('b_15= ' + str(self.b_15) + '\n')
            ouputF.write('b_0= ' + str(self.b_0) + '\n')
            ouputF.write('b_2= ' + str(self.b_2) + '\n')
            ouputF.write('b_17= ' + str(self.b_17) + '\n')
            ouputF.close()
        self.topCoords = np.array([x, yTop]).transpose()
        self.buttomCoords = np.array([x[::-1], yBut[::-1]]).transpose()
        return np.vstack((np.array([x, yTop]).transpose(), np.array([x[::-1], yBut[::-1]]).transpose()))[:-1]

    def get_cooridnates_top_buttom(self, pointCount):
        self.generate_airfoil(pointCount, show_plot=False)
        return self.topCoords, self.buttomCoords

    # calculations
    def thicknessCurve(self, t):
        if t <= self.x_t:
            u = t / self.x_t
            x = self.x0_tle*(1-u)**3 + 3*self.x1_tle*u*(u-1)**2 + 3*self.x2_tle*u**2*(1-u) + self.x3_tle*u**3
            y = self.y0_tle*(1-u)**3 + 3*self.y1_tle*u*(u-1)**2 + 3*self.y2_tle*u**2*(1-u) + self.y3_tle*u**3
        elif t > self.x_t:
            u = (t-self.x_t) / (1-self.x_t)
            x = self.x0_tte*(1-u)**4 + 4*self.x1_tte*u*(1-u)**3 + 6*self.x2_tte*u**2*(1-u)**2 + 4*self.x3_tte*u**3*(1-u) + self.x4_tte*u**4
            y = self.y0_tte*(1-u)**4 + 4*self.y1_tte*u*(1-u)**3 + 6*self.y2_tte*u**2*(1-u)**2 + 4*self.y3_tte*u**3*(1-u) + self.y4_tte*u**4
        elif t > 1:
            print("Out of bounds")
            return
        return x,y

    def camberCurve(self, t):
        if t <= self.x_t:
            u = t / self.x_t
            x = self.x0_cle*(1-u)**3 + 3*self.x1_cle*u*(u-1)**2 + 3*self.x2_cle*u**2*(1-u) + self.x3_cle*u**3
            y = self.y0_cle*(1-u)**3 + 3*self.y1_cle*u*(u-1)**2 + 3*self.y2_cle*u**2*(1-u) + self.y3_cle*u**3
        elif t > self.x_t:
            u = (t-self.x_t) / (1-self.x_t)
            x = self.x0_cte*(1-u)**4 + 4*self.x1_cte*u*(1-u)**3 + 6*self.x2_cte*u**2*(1-u)**2 + 4*self.x3_cte*u**3*(1-u) + self.x4_cte*u**4
            y = self.y0_cte*(1-u)**4 + 4*self.y1_cte*u*(1-u)**3 + 6*self.y2_cte*u**2*(1-u)**2 + 4*self.y3_cte*u**3*(1-u) + self.y4_cte*u**4
        elif t > 1:
            print("Out of bounds")
            return
        return x, y


if __name__ == '__main__':
    bp = BPAirfoil()
    bp.generate_airfoil(500, show_plot=True)

'''
# output
plt.plot([x0_tle,x1_tle,x2_tle,x3_tle,x0_tte,x1_tte,x2_tte,x3_tte,x4_tte],[y0_tle,y1_tle,y2_tle,y3_tle,y0_tte,y1_tte,y2_tte,y3_tte,y4_tte],'bx')
plt.title('Bezier points thickness curve')
#plt.xlim(0,1)
#plt.ylim(0,0.15)
plt.axis('equal')
plt.show()
plt.plot([x0_cle,x1_cle,x2_cle,x3_cle,x0_cte,x1_cte,x2_cte,x3_cte,x4_cte],[y0_cle,y1_cle,y2_cle,y3_cle,y0_cte,y1_cte,y2_cte,y3_cte,y4_cte],'rx')
plt.title('Bezier points camber curve')
plt.axis('equal')
plt.show()

# plots
points=np.linspace(0,1,100)
pointsThicknessCurve=list(map(thicknessCurve,points))
xThick = [i[0] for i in pointsThicknessCurve]
yThick = [i[1] for i in pointsThicknessCurve]
#plt.plot(pointsThicknessCurve)
#plt.show()
plt.plot(xThick, yThick)
plt.title('Thickness curve')
plt.axis('equal')
plt.show()

pointsCamberCurve=list(map(camberCurve,points))
xCam = [i[0] for i in pointsCamberCurve]
yCam = [i[1] for i in pointsCamberCurve]
#plt.plot(pointsCamberCurve)
#plt.show()
plt.plot(xCam, yCam)
plt.title('Camber curve')
plt.axis('equal')
plt.show()
'''

