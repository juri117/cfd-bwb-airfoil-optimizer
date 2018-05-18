__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import os
import sys
import math
import traceback

from Gmsh import Gmsh
from Airfoil import Airfoil
from SU2 import SU2
from BPAirfoil import BPAirfoil
from CFDrun import CFDrun
from constants import *

import bwbAirfoilOptimizer as opti

try:
    opti.cabinLength = 0.55
    opti.cabinHeigth = 0.13
    opti.PROJECT_NAME_PREFIX = 'test01'
    opti.config['AOA'] = str(0.0)
    opti.runOpenMdao()
except:
    print('#################################################################')
    print('ERROR: some exception accured in run: ' + opti.PROJECT_NAME_PREFIX)
    print('')
    traceback.print_exc()
    print('#################################################################')

try:
    opti.cabinLength = 0.55
    opti.cabinHeigth = 0.14
    opti.PROJECT_NAME_PREFIX = 'test02'
    opti.config['AOA'] = str(0.0)
    opti.runOpenMdao()
except:
    print('#################################################################')
    print('ERROR: some exception accured in run: ' + opti.PROJECT_NAME_PREFIX)
    print('')
    traceback.print_exc()
    print('#################################################################')

try:
    opti.cabinLength = 0.6
    opti.cabinHeigth = 0.13
    opti.PROJECT_NAME_PREFIX = 'test03'
    opti.config['AOA'] = str(0.0)
    opti.runOpenMdao()
except:
    print('#################################################################')
    print('ERROR: some exception accured in run: ' + opti.PROJECT_NAME_PREFIX)
    print('')
    traceback.print_exc()
    print('#################################################################')
