#!/usr/bin/env python

## \file Expandp3d.py
#  \brief Python script for converting from plot3D to SU2
#  \author _________
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
parser.add_option("-f", "--file", dest="filename", default="default.p3d",
                  help="write mesh to FILE", metavar="FILE")
(options, args)=parser.parse_args()

# Read the input file
p3d_File = open(options.filename,"r")

# Read the body
body = p3d_File.read().replace("\n"," ").replace("\t"," ").split()

# Write the body
filename = options.filename.rsplit( ".", 1 )[ 0 ] + ".Expp3d"


Expp3d_File = open(filename,"w")

for x in range(0, len(body)):
  
  if len(body[x].rsplit("*")) == 2:
    mult = int(body[x].rsplit("*")[0])
    for y in range(0, mult):
      Expp3d_File.write("%s   " % body[x].rsplit("*")[1])

  else:
    Expp3d_File.write("%s   " % body[x])
    

Expp3d_File.close()
p3d_File.close()