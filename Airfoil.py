__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

# ==============================================================================
# description     :reads in Airfoil and creates interpol
# date            :2018-04-16
# notes           :
# python_version  :3.6
# ==============================================================================

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import math

class Airfoil:

    #Specifies the kind of interpolation as a string (linear, nearest, zero, slinear, quadratic, cubic

    INTERPOL_DEG = 'linear'


    def __init__(self, filename):
        if filename != None:
            airfoilData = np.genfromtxt(filename, delimiter=',')
            #in the used csv database they stored first the upper shell coorinates and then the bottum both
            #starting from the nose... so we separate the list here in top and buttom
            i = 1
            while airfoilData[i, 0] > 0.000001:
                    i += 1
            self.airfoilTop = airfoilData[:i]
            self.airfoilButtom = airfoilData[i:]

            self.originalTop = self.airfoilTop.copy()
            self.originalButtom = self.airfoilButtom.copy()

            #easy as this we let scipy handle the interpolation
            #the return is a function that can be called with an x coordinate... f(x)
            #self.airfoilInterpolTop = interp1d(self.airfoilTop[:,0], self.airfoilTop[:,1], kind=self.INTERPOL_DEG)
            #self.airfoilInterpolButtom = interp1d(self.airfoilButtom[:, 0], self.airfoilButtom[:, 1], kind=self.INTERPOL_DEG)
            self.rotate( 0.)

    def set_coordinates(self, top, buttom):
        self.airfoilTop = top
        self.airfoilButtom = buttom
        self.originalTop = self.airfoilTop.copy()
        self.originalButtom = self.airfoilButtom.copy()
        #self.rotate(0.)

    def get_sorted_point_list(self):
        #sort top and buttom
        top = sorted(self.airfoilTop, key=lambda elem: elem[0])
        but = sorted(self.airfoilButtom, key=lambda elem: elem[0])[::-1]
        #elimenate duplicates
        listOut = np.array(top)
        for e in but:
            if not e in listOut:
                listOut = np.append(listOut, [e], axis=0)
        return np.array(listOut)

    """
    :parself.originalTopam x coorinate [0..1]
    :return y cooridinate of top shell or 0 if x is not in interpolation range
    """
    def get_top_y(self, x):
        if x < min(self.airfoilTop[:,0]) or  x > max(self.airfoilTop[:,0]):
            return 0.
        return self.airfoilInterpolTop(x)

    """
    :param x coorinate [0..1]
    :return y cooridinate of buttom shell or 0 if x is not in interpolation range
    """
    def get_buttom_y(self, x):
        if x < min(self.airfoilButtom[:,0]) or  x > max(self.airfoilButtom[:,0]):
            return 0.
        return self.airfoilInterpolButtom(x)

    def rotate(self, angle):
        self.newTop = np.empty([len(self.airfoilTop), 2])
        for i in range(0, len(self.airfoilTop)):
            self.airfoilTop[i] = self.rotatePoint((0, 0), self.originalTop[i], angle)
        self.newButtom = np.empty([len(self.airfoilButtom), 2])
        for i in range(0, len(self.airfoilButtom)):
            self.airfoilButtom[i] = self.rotatePoint((0, 0), self.originalButtom[i], angle)
        self.airfoilInterpolTop = interp1d(self.airfoilTop[:, 0], self.airfoilTop[:, 1], kind=self.INTERPOL_DEG)
        self.airfoilInterpolButtom = interp1d(self.airfoilButtom[:, 0], self.airfoilButtom[:, 1], kind=self.INTERPOL_DEG)



    def rotatePoint(self, origin, point, angle):
        angle = angle * math.pi / 180.
        ox, oy = origin
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return [qx, qy]

    """ kooridinate direction
            <----              start
     .--------------__
    /                 ---__
    |                      ---___
     '----------------------------
            ------->           end
    """
    def write_to_dat(self, file_name, working_dir='dataOut/'):
        fileName = file_name.replace('.dat', '')
        outF = open(working_dir + '/' + fileName + '.dat', 'w')
        outF.write(file_name + '\n')
        top = sorted(self.airfoilTop, key=lambda elem: elem[0])[::-1]
        but = sorted(self.airfoilButtom, key=lambda elem: elem[0])
        lastX = -999.
        lastY = -999.
        for row in top:
            #outF.write(str(row[0]) + '  ' + str(row[1]) + '\n')
            if not (lastX == row[0] and lastY == row[1]):
                outF.write("{:.7f}  {:.7f}\n".format(row[0], row[1]))
            lastX = row[0]
            lastY = row[1]
        for row in but:
            #outF.write(str(row[0]) + '  ' + str(row[1]) + '\n')
            if not (lastX == row[0] and lastY == row[1]):
                outF.write("{:.7f}  {:.7f}\n".format(row[0], row[1]))
            lastX = row[0]
            lastY = row[1]
        outF.close()




    def plotAirfoil(self, showPlot=True):
        xList = []
        yTopList = []
        yButtomList = []
        for x in np.arange(-0.1, 1.1, 0.001):
            xList.append(x)
            yTopList.append(self.get_top_y(x))
            yButtomList.append(self.get_buttom_y(x))

        fig, ax = plt.subplots()
        line1, = ax.plot(xList, yTopList, '-g', label='top Interpol')
        line2, = ax.plot(xList, yButtomList, '-b', label='buttom Interpol')

        line3, = ax.plot(self.airfoilTop[:,0], self.airfoilTop[:,1], '.g', label='top rawData')
        line4, = ax.plot(self.airfoilButtom[:,0], self.airfoilButtom[:, 1], '.b', label='buttom rawData')

        ax.set(xlabel='x in %', ylabel='y in %', title='WingPlot')
        ax.grid()
        ax.set_aspect('equal', 'datalim')
        ax.legend(handles=[line1, line2, line3, line4])
        # fig.savefig("airfoil.png")
        if showPlot:
            plt.show()
        return ax


if __name__ == '__main__':
    air = Airfoil('../design/04_aerodynamics/profiles/BwBAirfoilFixed.csv')
    air.rotate(-5)
    air.plotAirfoil()
