# airfoil optimization for BwB

This program implements an openMdao component, that optimizes an airfoil for minimum drag while making sure a defined rectangle is still fitting inside it. This rectangle represents the cabin tube of a blended wing body (BwB).

## Requirements:
- python:
  - the tested versions are 2.7 and 3.5
  - beside some standard packages openMdao is needed
    - http://openmdao.org/
- su2:
  - https://su2code.github.io/download.html
- construct2d(recommended):
  - https://sourceforge.net/projects/construct2d/
- or gmsh:
  - http://gmsh.info/

## How to run it:

use your favourite python editor and open this repo as a new project...
- main.py: the main optimization program
- cfdTestRun.py: simple test script that runs one cfd job with a given input airfoil coordinate file
- cfdConvergenceTest.py: does convergence analysis with different mesh sizes
