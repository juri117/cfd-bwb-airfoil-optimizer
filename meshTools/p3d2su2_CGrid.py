#!/usr/bin/env python

## \file p3d2su2_CGrid.py
#  \brief Python script for converting C-Grids from plot3D to SU2
#  \author F. Palacios
#  \version 3.2.8 "eagle"
#
# SU2 Lead Developers: Dr. Francisco Palacios (fpalacios@stanford.edu).
#                      Dr. Thomas D. Economon (economon@stanford.edu).
#
# SU2 Developers: Prof. Juan J. Alonso's group at Stanford University.
#                 Prof. Piero Colonna's group at Delft University of Technology.
#                 Prof. Nicolas R. Gauger's group at Kaiserslautern University of Technology.
#                 Prof. Alberto Guardone's group at Polytechnic University of Milan.
#                 Prof. Rafael Palacios' group at Imperial College London.
#
# Copyright (C) 2012-2015 SU2, the open-source CFD code.
#
# SU2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# SU2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SU2. If not, see <http://www.gnu.org/licenses/>.

from optparse import OptionParser
import string
import postpycess
import numpy as np
import matplotlib.pyplot as plt


def p2_to_su2_cgrid(input_file_path):
    # parser=OptionParser()
    # parser.add_option("-f", "--file", dest="filename", default="default.p2d",
    #                  help="write mesh to FILE", metavar="FILE")
    # (options, args)=parser.parse_args()

    # options.filename='../dataOut/meshTest/cTest.p3d'#naca641-212_stats.p3d'

    # Read the input file
    # p2d_File = open(options.filename,"r")

    imax, jmax, kmax, x, y, threed = postpycess.read_grid(input_file_path)

    colormap = 'jet'
    plaincolor = 'black'
    varname = None
    plotvar = None
    minvar = None
    maxvar = None
    #ax = postpycess.plot_grid(x, y, colormap, plaincolor, varname, plotvar, minvar, maxvar)
    fig = plt.figure()
    ax = fig.add_subplot(111)



    p2d_File = open(input_file_path, "r")

    # Read the header
    # header = p2d_File.readline()
    header = p2d_File.readline().replace("\n", " ").replace("\t", " ").split()
    nNode = int(header[0].strip())
    mNode = int(header[1].strip())

    # Read the body
    body = p2d_File.read().replace("\n", " ").replace("\t", " ").split()

    p2d_File.close()

    # Write the .su2 file
    filename = input_file_path.rsplit(".", 1)[0] + ".su2"
    su2_File = open(filename, "w")

    # Write the header
    su2_File.write("NDIME=2\n")
    su2_File.write("NELEM=%s\n" % ((mNode - 1) * (nNode - 1)))

    # Extra points to remove to adjust the conectivity
    points_airfoil = (mNode - 1) * 2
    #points_remove = ((nNode + 1) - points_airfoil) / 2
    points_remove = 0
    FirstPoint = points_remove + points_airfoil - 1  # minus 1 because C++ uses 0
    LastPoint = FirstPoint + points_remove - 1

    # Write the coordinates
    nPoint = (nNode) * (mNode)
    iPoint = 0
    pointList = np.zeros((nPoint, 2))
    for jNode in range(mNode):
        for iNode in range(nNode):
            XCoord = body[jNode * nNode + iNode]
            YCoord = body[(nNode * mNode) + jNode * nNode + iNode]
            pointList[iPoint][0] = XCoord
            pointList[iPoint][1] = YCoord
            iPoint = iPoint + 1



    # Write the connectivity
    iElem = 0
    for jNode in range(mNode - 1):
        for iNode in range(nNode - 1):
            Point0 = jNode * nNode + iNode
            Point1 = jNode * nNode + iNode + 1
            Point2 = (jNode + 1) * nNode + (iNode + 1)
            Point3 = (jNode + 1) * nNode + iNode

            if Point0 >= FirstPoint and Point0 <= LastPoint:
                Point0 = nNode - Point0 - 1
            if Point0 > LastPoint:
                Point0 = Point0 - points_remove

            if Point1 >= FirstPoint and Point1 <= LastPoint:
                Point1 = nNode - Point1 - 1
            if Point1 > LastPoint:
                Point1 = Point1 - points_remove

            Point2 = Point2 - points_remove

            Point3 = Point3 - points_remove

            su2_File.write("9 \t %s \t %s \t %s \t %s \t %s\n" % (Point0, Point1, Point2, Point3, iElem))
            iElem = iElem + 1
            ax.plot([pointList[Point0][0], pointList[Point1][0], pointList[Point2][0], pointList[Point3][0]],
                    [pointList[Point0][1], pointList[Point1][1], pointList[Point2][1], pointList[Point3][1]], 'bx-')

    #plt.show()


    # Write the coordinates
    nPoint = (nNode) * (mNode)
    su2_File.write("NPOIN=%s\n" % ((nNode) * (mNode) - points_remove))
    iPoint = 0
    #pointList = np.zeros((nPoint, 2))
    for jNode in range(mNode):
        for iNode in range(nNode):
            XCoord = body[jNode * nNode + iNode]
            YCoord = body[(nNode * mNode) + jNode * nNode + iNode]
            #pointList[iPoint][0] = XCoord
            #pointList[iPoint][1] = YCoord

            if iPoint < FirstPoint or iPoint > LastPoint:
                su2_File.write("%s \t %s \t %s\n" % (XCoord, YCoord, iPoint))

            iPoint = iPoint + 1

    # Write the boundaries
    su2_File.write("NMARK=2\n")

    su2_File.write("MARKER_TAG= airfoil\n")
    points = (mNode - 1) * 2
    elems = 1 #because we will add one at the end
    FirstPoint = ((nNode + 1) - points) / 2
    outStr = ''
    startNodeId = None
    lastNodeId = 0
    for iNode in range(points - 1):
        fistNodeId = FirstPoint + iNode - 1
        secondNodeId = FirstPoint + iNode + 1 - 1
        if pointList[fistNodeId][0] <= 1. and pointList[secondNodeId][0] <= 1.:
            outStr += "3 \t %s \t %s\n" % (fistNodeId, secondNodeId)  # minus 1 because C++ uses 0
            elems += 1
            ax.plot([pointList[fistNodeId][0], pointList[secondNodeId][0]], [pointList[fistNodeId][1], pointList[secondNodeId][1]], 'bx--')
            if startNodeId == None:
                startNodeId = fistNodeId
            lastNodeId = secondNodeId

    su2_File.write("MARKER_ELEMS=%s\n" % elems)
    su2_File.write(outStr)
    #fistNodeId = FirstPoint + iNode - 1
    su2_File.write("3 \t %s \t %s\n" % (lastNodeId, startNodeId))  # minus 1 because C++ uses 0

    su2_File.write("MARKER_TAG= farfield\n")
    TotalElem = (nNode - 1) + (mNode - 1) + (mNode - 1)
    #su2_File.write("MARKER_ELEMS=%s\n" % TotalElem)

    points_airfoil = (mNode - 1) * 2
    #elems = (nNode - 1)
    FirstPoint = nNode * (points_airfoil / 2) + 1  # minus 1 because C++ uses 0
    elems = 0
    outStr = ''

    farfieldIDs = []

    for iNode in range(nNode - 1):
        fistNodeId = FirstPoint + iNode - 1 #- points_remove
        secondNodeId = FirstPoint + iNode + 1 - 1 #- points_remove
        outStr += "3 \t %s \t %s\n" % (fistNodeId, secondNodeId)
        elems += 1
        ax.plot([pointList[fistNodeId][0], pointList[secondNodeId][0]], [pointList[fistNodeId][1], pointList[secondNodeId][1]], 'gx--')

        if pointList[fistNodeId][0] == pointList[secondNodeId][0] and pointList[fistNodeId][1] == pointList[secondNodeId][1]:
            print('ERROR!!!!!!!!!')
            print(str(fistNodeId) + ' to ' + str(secondNodeId))
            ax.plot([pointList[fistNodeId][0], pointList[secondNodeId][0]], [pointList[fistNodeId][1], pointList[secondNodeId][1]], 'rx--', markersize=20)
        farfieldIDs.append(fistNodeId)
    #farfieldIDs.append(secondNodeId)

    #now add the rear edge
    rearX = max([e[0] for e in pointList])
    rearEdgePoints = []
    for i in range(0,len(pointList)):
        if abs(pointList[i][0] - rearX) < 0.1:
            rearEdgePoints.append([pointList[i], i])
            #print(str(pointList[i][0]))

    rearEdgePoints = sorted(rearEdgePoints, key=lambda elem: elem[0][1])[::-1]

    firstNode = rearEdgePoints[0]
    for i in range(1, len(rearEdgePoints)):
        outStr += "3 \t %s \t %s\n" % (firstNode[1], rearEdgePoints[i][1])
        elems += 1
        ax.plot([firstNode[0][0], rearEdgePoints[i][0][0]],
                [firstNode[0][1], rearEdgePoints[i][0][1]], 'gx-')
        if firstNode[0][1] == rearEdgePoints[i][0][1] and firstNode[0][0] == rearEdgePoints[i][0][0]:
            print('ERROR!!!!!!!!!')
            print(str(firstNode[1]) + ' to ' + str(rearEdgePoints[i][1]))
            ax.plot([firstNode[0][0], rearEdgePoints[i][0][0]],
                    [firstNode[0][1], rearEdgePoints[i][0][1]], 'rx-', markersize=20)
        else:
            farfieldIDs.append(firstNode[1])
        firstNode = rearEdgePoints[i]

    farfieldIDs.append(firstNode[1])

    prev = farfieldIDs[0]
    for i in range(1, len(farfieldIDs)):
        thisID = farfieldIDs[i]
        if abs(pointList[prev][0] - pointList[thisID][0]) < 0.00001 and abs(pointList[prev][1] - pointList[thisID][1]) < 0.00001:
            print('immernoch ERROR!')
            print(str(prev) + ' to ' + str(thisID))
            ax.plot([pointList[prev][0], pointList[thisID][0]],
                    [pointList[prev][1], pointList[thisID][1]], 'rx-', markersize=20)
        prev = thisID

    ax.plot([pointList[219][0], pointList[220][0]],
            [pointList[219][1], pointList[220][1]], 'rx--', markersize=30)
    ax.plot([pointList[440][0], pointList[220][0]],
            [pointList[440][1], pointList[220][1]], 'yx--', markersize=30)

    """
    #elems = (mNode - 1)
    for jNode in range(mNode - 1):
        if jNode == 0:
            su2_File.write("3 \t 0 \t %s\n" % ((jNode * nNode + 1) + nNode - 1 - points_remove))
            #ax.plot([pointList[0][0], pointList[(jNode * nNode + 1) + nNode - 1 - points_remove][0]],
            #        [pointList[0][1], pointList[(jNode * nNode + 1) + nNode - 1 - points_remove][1]], 'gx-')
        else:
            su2_File.write("3 \t %s \t %s\n" % (
            (jNode * nNode + 1) - 1 - points_remove, (jNode * nNode + 1) + nNode - 1 - points_remove))
            #ax.plot([pointList[(jNode * nNode + 1) - 1 - points_remove][0], pointList[(jNode * nNode + 1) + nNode - 1 - points_remove][0]],
            #        [pointList[(jNode * nNode + 1) - 1 - points_remove][1], pointList[(jNode * nNode + 1) + nNode - 1 - points_remove][1]], 'gx-')

    #elems = (mNode - 1)
    for jNode in range(mNode - 1):
        if jNode == 0:
            su2_File.write("3 \t 0 \t %s\n" % ((jNode + 1) * nNode + nNode - 1 - points_remove))
        else:
            su2_File.write("3 \t %s \t %s\n" % (
            jNode * nNode + nNode - 1 - points_remove, (jNode + 1) * nNode + nNode - 1 - points_remove))
            ax.plot([pointList[jNode * nNode + nNode - 1 - points_remove][0], pointList[(jNode + 1) * nNode + nNode - 1 - points_remove][0]],
                    [pointList[jNode * nNode + nNode - 1 - points_remove][1], pointList[(jNode + 1) * nNode + nNode - 1 - points_remove][1]], 'rx-')
    """

    su2_File.write("MARKER_ELEMS=%s\n" % elems)
    su2_File.write(outStr)


    su2_File.close()

    plt.show()


if __name__ == '__main__':
    p2_to_su2_cgrid('naca641-212.p3d')
