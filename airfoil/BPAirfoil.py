__author__ = "Lennart Kracke"
__version__ = "0.0.1"
__status__ = "Development"

# ==============================================================================
# description     :creates airfoil coordinates with bezier-parsec parametrization (http://pubs.sciepub.com/ajme/2/4/1/)
# date            :2018-04-24
# notes           :420 blaze it
# python_version  :3.6
# ==============================================================================

# imports

import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from operator import add
from airfoil.Airfoil import Airfoil


class BPAirfoil:

    def __init__(self):
        self.valid = True
        # necessary variables
        # aerodynamic parameters
        self.r_le = -0.025  # nose radius
        self.beta_te = 0.15  # thickness angle trailing edge
        self.dz_te = 0.  # thickness trailing edge
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

    def generate_airfoil(self, pointCount, show_plot=True, save_plot_path='', param_dump_file=''):
        #reset status
        self.valid = True
        # check requirenment
        if not (0 < self.b_8 < min(self.y_t, math.sqrt(-2 * self.r_le * self.x_t / 3))):
            print("Parameter b_8 out of bounds!")
            self.valid = False
            return False

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

        yTop = list(map(add, yC, yT))
        yBut = list(map(add, yC, (-1. * yT)))

        if show_plot or save_plot_path != '':
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
        if show_plot or save_plot_path != '':
            plt.clf()
        if not param_dump_file == '':
            self.save_parameters_to_file(param_dump_file)
        self.topCoords = np.array([x, yTop]).transpose()
        self.buttomCoords = np.array([x[::-1], yBut[::-1]]).transpose()
        return np.vstack((np.array([x, yTop]).transpose(), np.array([x[::-1], yBut[::-1]]).transpose()))[:-1]

    def plot_airfoil_with_cabin(self, offsetFront, length, height, angle, show_plot=True, save_plot_path='', clear_plot=True):
        """
        air = Airfoil(None)
        air.set_coordinates(self.topCoords, self.buttomCoords)
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
        ax = air.plotAirfoil(showPlot=False, showPoints=False)
        ax.plot([px_ol, px_ul, px_ur, px_or, px_ol], [py_ol, py_ul, py_ur, py_or, py_ol], 'rx-')

        return ax

        """
        air = Airfoil(None)
        air.set_coordinates(self.topCoords, self.buttomCoords)
        air.rotate(angle)
        px_ul = offsetFront
        py_ul = air.get_buttom_y(px_ul)
        px_ol = offsetFront
        py_ol = py_ul + height
        (px_ol, py_ol) = self.rotatePoint((0, 0), (px_ol, py_ol), angle)
        (px_ul, py_ul) = self.rotatePoint((0, 0), (px_ul, py_ul), angle)
        px_ur = offsetFront + length
        py_ur = air.get_buttom_y(px_ur)
        px_or = offsetFront + length
        py_or = py_ur + height
        (px_or, py_or) = self.rotatePoint((0, 0), (px_or, py_or), angle)
        (px_ur, py_ur) = air.rotatePoint((0, 0), (px_ur, py_ur), angle)

        pltTop, = plt.plot(self.topCoords[:,0], self.topCoords[:,1], '-b', label='airfoil')
        pltBut, = plt.plot(self.buttomCoords[:,0], self.buttomCoords[:,1], '-b', label='not in use')
        cabin, = plt.plot([px_ol, px_ul, px_ur, px_or, px_ol], [py_ol, py_ul, py_ur, py_or, py_ol], '-r', label='cabin')

        plt.legend(handles=[pltTop, cabin])
        plt.title('Airfoil with cabin')
        plt.axis('equal')
        if save_plot_path != '':
            plt.savefig(save_plot_path)
        if show_plot:
            plt.show()
        if clear_plot:
            plt.clf()

    def rotatePoint(self, origin, point, angle):
        angle = angle * math.pi / 180.
        ox, oy = origin
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return [qx, qy]

    def save_parameters_to_file(self, file_path):
        ouputF = open(file_path, 'w')
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

    def read_parameters_from_file(self, file_path):
        inputF = open(file_path, 'r')
        lines = inputF.read().splitlines()
        for l in lines:
            l = l.strip()
            l = l.replace(' ', '')
            l = l.replace('[', '')
            l = l.replace(']', '')
            param = l.split('=')
            if len(param) == 2:
                try:
                    if param[0] == 'r_le':
                        self.r_le = float(param[1])
                    elif param[0] == 'beta_te':
                        self.beta_te = float(param[1])
                    elif param[0] == 'dz_te':
                        self.dz_te = float(param[1])
                    elif param[0] == 'x_t':
                        self.x_t = float(param[1])
                    elif param[0] == 'y_t':
                        self.y_t = float(param[1])

                    elif param[0] == 'gamma_le':
                        self.gamma_le = float(param[1])
                    elif param[0] == 'x_c':
                        self.x_c = float(param[1])
                    elif param[0] == 'y_c':
                        self.y_c = float(param[1])
                    elif param[0] == 'alpha_te':
                        self.alpha_te = float(param[1])
                    elif param[0] == 'z_te':
                        self.z_te = float(param[1])

                    elif param[0] == 'b_8':
                        self.b_8 = float(param[1])
                    elif param[0] == 'b_15':
                        self.b_15 = float(param[1])
                    elif param[0] == 'b_0':
                        self.b_0 = float(param[1])
                    elif param[0] == 'b_2':
                        self.b_2 = float(param[1])
                    elif param[0] == 'b_17':
                        self.b_17 = float(param[1])
                except:
                    print('ERROR: parsing BZAirfoil parameter from file: ' + file_path)
        inputF.close()

    def get_cooridnates_top_buttom(self, pointCount, show_plot=False):
        self.generate_airfoil(pointCount, show_plot=show_plot)
        if not self.valid:
            return [], []
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
    #bp = BPAirfoil()
    #bp.generate_airfoil(500, show_plot=True)

    ###compare arifoils

    bp1 = BPAirfoil()
    bp1.read_parameters_from_file('../dataIn/airfoil.txt')
    bp1.generate_airfoil(500, show_plot=False)
    #plt1, = plt.plot(bp1.topCoords[:, 0], bp1.topCoords[:, 1], '--g', label='airfoil 1')
    #plt.plot(bp1.buttomCoords[:, 0], bp1.buttomCoords[:, 1], '--g', label='airfoil 1')

    bp2 = BPAirfoil()
    bp2.read_parameters_from_file('../dataOut/airfoil.txt')
    bp2.generate_airfoil(500, show_plot=False)
    #plt2, = plt.plot(bp2.topCoords[:, 0], bp2.topCoords[:, 1], '-g', label='airfoil 2')
    #plt.plot(bp2.buttomCoords[:, 0], bp2.buttomCoords[:, 1], '-g', label='airfoil 2')

    #bp2.plot_airfoil_with_cabin(0.12275856, 0.55, 0.14, -0.00203671)

    bp2.plot_airfoil_with_cabin(0.12275856, 0.55, 0.14, -0.00203671,
                                        show_plot=True,
                                        save_plot_path='')

    #plt.legend(handles=[plt1, plt2])
    plt.title('Airfoil with cabin')
    plt.axis('equal')
    plt.show()

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

