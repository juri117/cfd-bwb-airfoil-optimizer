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

parser=OptionParser()
parser.add_option("-f", "--file", dest="filename", default="default.p2d",
                  help="write mesh to FILE", metavar="FILE")
(options, args)=parser.parse_args()

options.filename='../dataOut/meshTest/cTest.p3d'#naca641-212_stats.p3d'

# Read the input file
p2d_File = open(options.filename,"r")

# Read the header
#header = p2d_File.readline()
header = p2d_File.readline().replace("\n"," ").replace("\t"," ").split()
nNode = int(header[0].strip())
mNode = int(header[1].strip())

# Read the body
body = p2d_File.read().replace("\n"," ").replace("\t"," ").split()

p2d_File.close()

# Write the .su2 file
filename = options.filename.rsplit( ".", 1 )[ 0 ] + ".su2"
su2_File = open(filename,"w")

# Write the header
su2_File.write( "NDIME=2\n" )
su2_File.write( "NELEM=%s\n" % ((mNode-1)*(nNode-1)))

#Extra points to remove to adjust the conectivity
points_airfoil = (mNode-1)*2
points_remove = ((nNode+1)-points_airfoil)/2
FirstPoint = points_remove + points_airfoil - 1 # minus 1 because C++ uses 0
LastPoint = FirstPoint + points_remove - 1

# Write the connectivity
iElem = 0
for jNode in range(mNode-1):
  for iNode in range(nNode-1):
    Point0 = jNode*nNode + iNode
    Point1 = jNode*nNode + iNode + 1
    Point2 = (jNode+1)*nNode + (iNode+1)
    Point3 = (jNode+1)*nNode + iNode
    
    if Point0 >= FirstPoint and Point0 <= LastPoint :
      Point0 = nNode - Point0 - 1
    if Point0 > LastPoint :
      Point0 = Point0 - points_remove

    
    if Point1 >= FirstPoint and Point1 <= LastPoint :
      Point1 = nNode - Point1 - 1
    if Point1 > LastPoint :
      Point1 = Point1 - points_remove

    Point2 = Point2 - points_remove
    
    Point3 = Point3 - points_remove
    
    su2_File.write( "9 \t %s \t %s \t %s \t %s \t %s\n" % (Point0, Point1, Point2, Point3, iElem) )
    iElem = iElem + 1

# Write the coordinates
nPoint = (nNode)*(mNode)
su2_File.write( "NPOIN=%s\n" % ((nNode)*(mNode) - points_remove))
iPoint = 0
for jNode in range(mNode):
  for iNode in range(nNode):
    XCoord = body[jNode*nNode + iNode]
    YCoord = body[(nNode*mNode) + jNode*nNode + iNode]
    
    if iPoint < FirstPoint or iPoint > LastPoint :
      su2_File.write( "%s \t %s \t %s\n" % (XCoord, YCoord, iPoint) )
    
    iPoint = iPoint + 1

# Write the boundaries
su2_File.write( "NMARK=2\n" )

su2_File.write( "MARKER_TAG= airfoil\n" )
points = (mNode-1)*2
elems = points
FirstPoint = ( (nNode+1)-points )/2
su2_File.write( "MARKER_ELEMS=%s\n" % elems )
for iNode in range(points-1):
  su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + iNode -1 , FirstPoint + iNode + 1 - 1) ) # minus 1 because C++ uses 0

su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + points -1 -1, FirstPoint -1 ) ) # minus 1 because C++ uses 0


su2_File.write( "MARKER_TAG= farfield\n" )
TotalElem = (nNode-1) + (mNode-1) + (mNode-1)
su2_File.write( "MARKER_ELEMS=%s\n" % TotalElem)

points_airfoil = (mNode-1)*2
elems = (nNode-1)
FirstPoint = nNode*(points_airfoil/2) + 1 # minus 1 because C++ uses 0
for iNode in range(elems):
  su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + iNode - 1 - points_remove, FirstPoint + iNode + 1 - 1 - points_remove) )

elems = (mNode-1)
for jNode in range(elems):
  if jNode == 0 :
    su2_File.write( "3 \t 0 \t %s\n" % ((jNode*nNode + 1) + nNode - 1 - points_remove) )
  else :
    su2_File.write( "3 \t %s \t %s\n" % ((jNode*nNode + 1) - 1 - points_remove, (jNode*nNode + 1) + nNode - 1 - points_remove) )

elems = (mNode-1)
for jNode in range(elems):
  if jNode == 0 :
    su2_File.write( "3 \t 0 \t %s\n" % ( (jNode + 1)*nNode + nNode - 1 - points_remove) )
  else :
    su2_File.write( "3 \t %s \t %s\n" % (jNode*nNode + nNode - 1 - points_remove,  (jNode + 1)*nNode + nNode - 1 - points_remove) )


su2_File.close()