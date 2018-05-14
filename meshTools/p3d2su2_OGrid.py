#!/usr/bin/env python

## \file p3d2su2_OGrid.py
#  \brief Python script for converting O-Grids from plot3D to SU2
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


def p2_to_su2_ogrid(input_file_path):

  #parser=OptionParser()
  #parser.add_option("-f", "--file", dest="filename", default="default.p2d",
  #                  help="write mesh to FILE", metavar="FILE")
  #(options, args)=parser.parse_args()

  #options.filename='naca/naca2406.p3d'
  #options.filename='../dataOut/meshTest/naca641-212.p3d'
  #options.filename = input_file_path

  # Read the input file
  p2d_File = open(input_file_path,"r")

  # Read the header
  #header = p2d_File.readline()
  header = p2d_File.readline().replace("\n"," ").replace("\t"," ").split()
  nNode = int(header[0].strip())
  mNode = int(header[1].strip())

  # Read the body
  body = p2d_File.read().replace("\n"," ").replace("\t"," ").split()

  p2d_File.close()

  # Write the .su2 file
  filename = input_file_path.rsplit( ".", 1 )[ 0 ] + ".su2"
  su2_File = open(filename,"w")

  # Write the header
  su2_File.write( "NDIME=2\n" )
  su2_File.write( "NELEM=%s\n" % ((mNode-1)*(nNode-1)))

  # Write the connectivity
  iElem = 0
  for jNode in range(mNode-1):
    for iNode in range(nNode-1):

      Point0 = iNode + (jNode*(nNode-1))
      Point1 = (iNode+1) + (jNode*(nNode-1))
      Point2 = (iNode+1) + (jNode+1)*(nNode-1)
      Point3 = iNode + (jNode+1)*(nNode-1)

      if iNode == nNode-2:
        Point1 = jNode*(nNode-1)
        Point2 = (jNode+1)*(nNode-1)

      su2_File.write( "9 \t %s \t %s \t %s \t %s \t %s\n" % (Point0, Point1, Point2, Point3, iElem) )
      iElem = iElem + 1

  # Write the coordinates
  nPoint = (nNode)*(mNode)
  su2_File.write( "NPOIN=%s\n" % ((nNode-1)*(mNode)))
  iPoint = 0
  for jNode in range(mNode):
    for iNode in range(nNode):
      XCoord = body[jNode*nNode + iNode]
      YCoord = body[(nNode*mNode) + jNode*nNode + iNode]

      if iNode != (nNode-1) :
        su2_File.write( "%s \t %s \t %s\n" % (XCoord, YCoord, iPoint) )
        iPoint = iPoint + 1

  # Write the boundaries
  su2_File.write( "NMARK=2\n" )

  su2_File.write( "MARKER_TAG= airfoil\n" )
  points = (nNode-1)
  FirstPoint = 1
  su2_File.write( "MARKER_ELEMS=%s\n" % points )
  for iNode in range(points-1):
    su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + iNode -1 , FirstPoint + iNode + 1 - 1) ) # minus 1 because C++ uses 0
  su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + points -1 -1, FirstPoint -1 ) ) # minus 1 because C++ uses 0


  su2_File.write( "MARKER_TAG= farfield\n" )
  points = (nNode-1)
  elems = points
  FirstPoint = 1+(nNode-1)*(mNode-1)
  su2_File.write( "MARKER_ELEMS=%s\n" % points )
  for iNode in range(points-1):
    su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + iNode -1 , FirstPoint + iNode + 1 - 1) ) # minus 1 because C++ uses 0
  su2_File.write( "3 \t %s \t %s\n" % (FirstPoint + points -1 -1, FirstPoint -1 ) ) # minus 1 because C++ uses 0

  su2_File.close()