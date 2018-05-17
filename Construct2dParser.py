import string
import meshTools.postpycess
import numpy as np
import matplotlib.pyplot as plt
import random


class Elem:
    def __init__(self, id):
        self.id = id
        self.pointIDs = []

    def add_point(self, pointID):
        self.pointIDs.append(pointID)

    def plot_elem(self, ax, pointList):
        xLine = []
        yLine = []
        for i in range(0, len(self.pointIDs)):
            xLine.append(pointList[self.pointIDs[i]][0])
            yLine.append(pointList[self.pointIDs[i]][1])
        xLine.append(pointList[self.pointIDs[0]][0])
        yLine.append(pointList[self.pointIDs[0]][1])
        ax.plot(xLine, yLine, 'bx--')#, color=random.randint(3,1))



class Construct2dParser:

    def __init__(self, input_file_path):
        # 220, 100
        self.nNode, self.mNode, self.kmax, self.x, self.y, threed = meshTools.postpycess.read_grid(input_file_path)

        self.pointList = np.zeros((self.nNode * self.mNode, 3))
        iPoint = 0
        for m in range(self.mNode):
            for n in range(self.nNode):
                XCoord = self.x[n][m]  # body[jNode * nNode + iNode]
                YCoord = self.y[n][m]  # body[(nNode * mNode) + jNode * nNode + iNode]
                self.pointList[iPoint][0] = XCoord
                self.pointList[iPoint][1] = YCoord
                self.pointList[iPoint][2] = iPoint
                iPoint = iPoint + 1
        print('done reading points')


    def get_pointID(self, n, m):
        return m * self.nNode + n

    def plot_mesh(self, scale=1.):
        colormap = 'jet'
        plaincolor = 'black'
        varname = None
        plotvar = None
        minvar = None
        maxvar = None
        ax = meshTools.postpycess.plot_grid(self.x * scale, self.y * scale, colormap, plaincolor, varname, plotvar, minvar, maxvar)
        #plt.savefig(file_name, facecolor='w', edgecolor='w',
        #orientation='landscape')
        plt.show()

    def check_for_duplicates(self, listToCheck, x, y, oldId, ax):
        for l in listToCheck:
            if l[0] == x and l[1] == y:
                if oldId != int(l[2]):
                    print('kicked out point: ' + str(oldId))
                    if ax != None:
                        ax.plot([x], [y], 'rx', markersize=50)
                return int(l[2])
        return oldId


    def p3d_to_su2_cgrid(self, output_file_name, scale=1.):

        #fig = plt.figure()
        #ax = fig.add_subplot(111)

        su2_File = open(output_file_name, "w")

        # Write the header
        su2_File.write("NDIME=2\n")

        strOut = ''
        elementCount = 0
        elements = []
        for m in range(0, self.mNode - 1):
            for n in range(self.nNode - 1):
                p1ID = self.get_pointID(n, m)
                p2ID = self.get_pointID(n+1, m)
                p3ID = self.get_pointID(n+1, m+1)
                p4ID = self.get_pointID(n, m+1)
                if m == 0:
                    #remove duplicate nodes
                    p1ID = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p1ID][0], self.pointList[p1ID][1], p1ID, None)
                    p2ID = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p2ID][0], self.pointList[p2ID][1], p2ID, None)
                    p3ID = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p3ID][0], self.pointList[p3ID][1], p3ID, None)
                    p4ID = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p4ID][0], self.pointList[p4ID][1], p4ID, None)

                e = Elem(elementCount)
                e.add_point(p1ID)
                e.add_point(p2ID)
                e.add_point(p3ID)
                e.add_point(p4ID)
                elements.append(e)
                #if m < 4:
                #    e.plot_elem(ax, self.pointList)
                elementCount += 1

        su2_File.write("NELEM=%s\n" % len(elements))
        for e in elements:
            su2_File.write("9 \t %s \t %s \t %s \t %s \t %s\n" % (e.pointIDs[0], e.pointIDs[1], e.pointIDs[2], e.pointIDs[3], e.id))

        su2_File.write("NPOIN=%s\n" % (len(self.pointList)))
        for p in self.pointList:
            point1 = p[0] * scale
            point2 = p[1] * scale
            su2_File.write("%s \t %s \t %s\n" % (point1, point2, int(p[2])))


        su2_File.write("NMARK=2\n")
        su2_File.write("MARKER_TAG= airfoil\n")
        outStr = ''
        elementCount = 0
        m = 0
        for n in range(self.nNode - 1):
            p1 = self.get_pointID(n, m)
            p2 = self.get_pointID(n + 1, m)
            if self.pointList[p1][0] <= 1. and self.pointList[p2][0] <= 1.:
                p1 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p1][0],
                                                 self.pointList[p1][1], p1, None)
                p2 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p2][0],
                                               self.pointList[p2][1], p2, None)
                outStr += "3 \t %s \t %s\n" % (p1, p2)
                #ax.plot([self.pointList[p1][0], self.pointList[p2][0]], [self.pointList[p1][1], self.pointList[p2][1]], 'gx--')
                elementCount += 1
        #outStr += "3 \t %s \t %s\n" % (lastID, firstID)
        #ax.plot([self.pointList[p1][0], self.pointList[p2][0]], [self.pointList[p1][1], self.pointList[p2][1]], 'gx--')


        su2_File.write("MARKER_ELEMS=%s\n" % elementCount)
        su2_File.write(outStr)

        su2_File.write("MARKER_TAG= farfield\n")
        outStr = ''
        elementCount = 0
        m = self.mNode - 1
        #outer c ring buttom to top
        for n in range(0, self.nNode - 1):
            p1 = self.get_pointID(n, m)
            p2 = self.get_pointID(n + 1, m)
            p1 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p1][0],
                                           self.pointList[p1][1], p1, None)
            p2 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p2][0],
                                           self.pointList[p2][1], p2, None)
            outStr += "3 \t %s \t %s\n" % (p1, p2)
            #ax.plot([self.pointList[p1][0], self.pointList[p2][0]], [self.pointList[p1][1], self.pointList[p2][1]],
            #        'rx--')
            elementCount += 1
        #outer right edge, top to half
        n = self.nNode - 1
        for m in range(0, self.mNode - 1)[::-1]:
            p1 = self.get_pointID(n, m)
            p2 = self.get_pointID(n, m + 1)
            p1 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p1][0],
                                           self.pointList[p1][1], p1, None)
            p2 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p2][0],
                                           self.pointList[p2][1], p2, None)
            outStr += "3 \t %s \t %s\n" % (p1, p2)
            #ax.plot([self.pointList[p1][0], self.pointList[p2][0]], [self.pointList[p1][1], self.pointList[p2][1]],
            #        'gx--')
            elementCount += 1

        #outer right edge, half to buttom
        n = 0
        for m in range(0, self.mNode - 1):
            p1 = self.get_pointID(n, m)
            p2 = self.get_pointID(n, m + 1)
            p1 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p1][0],
                                           self.pointList[p1][1], p1, None)
            p2 = self.check_for_duplicates(self.pointList[:self.nNode], self.pointList[p2][0],
                                           self.pointList[p2][1], p2, None)
            outStr += "3 \t %s \t %s\n" % (p1, p2)
            #ax.plot([self.pointList[p1][0], self.pointList[p2][0]], [self.pointList[p1][1], self.pointList[p2][1]],
            #        'rx--')
            elementCount += 1

        su2_File.write("MARKER_ELEMS=%s\n" % elementCount)
        su2_File.write(outStr)



        #plt.show()
        #plt.clf()

        su2_File.close()

        """
        iElem = 0
        for jNode in range(mNode - 1):
            for iNode in range(nNode - 1):
                Point0 = jNode * nNode + iNode
                Point1 = jNode * nNode + iNode + 1
                Point2 = (jNode + 1) * nNode + (iNode + 1)
                Point3 = (jNode + 1) * nNode + iNode

                #if Point0 >= FirstPoint and Point0 <= LastPoint:
                #    Point0 = nNode - Point0 - 1
                #if Point0 > LastPoint:
                #    Point0 = Point0 - points_remove

                #if Point1 >= FirstPoint and Point1 <= LastPoint:
                #    Point1 = nNode - Point1 - 1
                #if Point1 > LastPoint:
                #    Point1 = Point1 - points_remove

                #Point2 = Point2 - points_remove

                #Point3 = Point3 - points_remove

                su2_File.write("9 \t %s \t %s \t %s \t %s \t %s\n" % (Point0, Point1, Point2, Point3, iElem))
                iElem = iElem + 1
                ax.plot([pointList[Point0][0], pointList[Point1][0], pointList[Point2][0], pointList[Point3][0]],
                        [pointList[Point0][1], pointList[Point1][1], pointList[Point2][1], pointList[Point3][1]], 'bx-')
        """


if __name__ == '__main__':
    c2d2su2 = Construct2dParser('naca641-212.p3d')
    #c2d2su2 = Construct2dParser('meshTools/airfoil.p3d')
    c2d2su2.p3d_to_su2_cgrid('mesh_.su2')