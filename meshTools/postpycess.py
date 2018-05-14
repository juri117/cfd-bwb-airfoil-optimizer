#!/usr/bin/env python

#  This is PostPycess, the CFD postprocessor

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

#  Copyright 2013 - 2018 Daniel Prosser

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colorobj
import matplotlib.cm as cmobj
from matplotlib.collections import LineCollection
import math

################################################################################
#
# Main program
#
################################################################################
def main():

  loadnew = True

# Load new data every time this loop is entered
  while loadnew:

#   Default is not to load new data files unless requested
    loadnew = False

#   File prefix
    #prefix = pyviz_init()
    prefix = 'naca2406'

#   Grid file to read
    gridfile = prefix + '.p3d'

#   In the future, additional Plot3D function files may be entered here
#   Data in these files will be automatically available for plotting,
#   provided the proper header is included in comments.
    datafiles=[]
    datafiles += [prefix + '_stats.p3d']

#   Check if files exist
#   (Grid file)
    try:
      f = open(gridfile)
    except IOError:
      print(('Error: can\'t read the file ' + gridfile +'\n'))
      return
    else:
      f.close

#   (Function files)
    fchecks = []
    for i in range(0, len(datafiles)):
      try:
        f = open(datafiles[i])
      except IOError:
        fchecks += [False]
      else:
        f.close
        fchecks += [True]

#   Read grid data
    imax, jmax, kmax, x, y, threed = read_grid(gridfile)

#   Read function files, storing categories, variable names, values, mins, maxes
    counter = 0
    catglist = []
    varlist = []
    for i in range(0, len(datafiles)):
      if fchecks[i]:
        tmpcatg, tmpvars, tmpvals, tmpmins, tmpmaxes = \
                         read_function_file(datafiles[i], imax, jmax, 
                                            kmax, threed)
        tmpnvars = len(tmpvars)
        catglist += [tmpcatg]*tmpnvars
        varlist += tmpvars
        if i == 0:
          values = tmpvals
          minvals = tmpmins
          maxvals = tmpmaxes
        else:
          values = np.concatenate((values, tmpvals))
          minvals = np.concatenate((minvals, tmpmins))
          maxvals = np.concatenate((maxvals, tmpmaxes))
    print('')

#   Store total number of variables
    nvars = len(varlist)

#   Default program options
    plaincolor = 'black'
    colormap = 'jet'
    contlevels = 15
    topcolor = 'red'
    botcolor = 'blue'
    current_options = [plaincolor, colormap, contlevels, topcolor, botcolor]

#   User selects plot type
    plottypedone = False
    while (not plottypedone):

      validtype = False
      plotselection = select_plot_type()

      if plotselection == '1':
        validtype = True
        plottype = 'grid'
      elif plotselection == '2':
        validtype = True
        plottype = 'contour'
      elif plotselection == '3':
        validtype = True
        plottype = 'surface'
      elif plotselection == 'O' or plotselection == 'o':
        validtype = False
        plottype = 'options'
      elif plotselection == 'L' or plotselection == 'l':
        validtype = False
        plottypedone = True
        loadnew = True
        plottype = 'reload'
      elif plotselection == 'Q' or plotselection == 'q':
        validtype = False
        plottypedone = True
        plottype = 'exit'
      else:
        plottype = 'exit'
        validtype = False
        plottypedone = False
        print(('Error: plotting option ' + str(plotselection) + ' not recognized.\n'))

#     User selects plotting variable from list
      if (validtype):
      
        plotdone = False
        while (not plotdone):

          validvar = False
          plotnum = select_plot_var(plottype, catglist, varlist)

#         Set variable by user input
          if plotnum == '1':
            validvar = True
            varname = None
            plotvar = None
            minvar = None
            maxvar = None 
          elif plotnum == 'Q' or plotnum == 'q':
            validvar = False
            plotdone = True
          elif is_int(plotnum) and int(plotnum) <= nvars + 1:
            validvar = True
            varnum = int(plotnum) - 2
            varname = varlist[varnum]
            plotvar = values[varnum,:,:]
            minvar = minvals[varnum]
            maxvar = maxvals[varnum]
          else:
            validvar = False
            plotdone = False
            print(('Error: plotting variable ' + plotnum + ' not recognized.\n'))
  
#         Create the plot
          if (validvar):
            if varname != None:
              print(('Max ' + varname + ': ', maxvar))
              print(('Min ' + varname + ': ', minvar))
              print('')
            if plottype == 'grid':
              plot_grid(x, y, colormap, plaincolor, 
                        varname, plotvar, minvar, maxvar)
            elif plottype == 'contour':
              plot_contours(x, y, colormap, plaincolor, contlevels, 
                            varname, plotvar, minvar, maxvar)
            elif plottype == 'surface':
              if varname == None:
                passedvar = None
              else:
                passedvar = plotvar[:,0]
              plot_surface(x[:,0], y[:,0], plaincolor, topcolor, botcolor,
                           varname, passedvar)

      else:
        if plottype == 'options':
          new_options = change_options(current_options)
          plaincolor = new_options[0]
          colormap = new_options[1]
          contlevels = new_options[2]
          topcolor = new_options[3]
          botcolor = new_options[4]

################################################################################
#
# Checks if a string can be converted to int
#
################################################################################
def is_int(string):

  try:
    int(string)
    return True
  except ValueError:
    return False

################################################################################
#
# Displays greeting and gets project name
#
################################################################################
def pyviz_init():

  print('\nThis is PostPycess, the CFD postprocessor')
  print('Version: 1.1')
  
  pname = eval(input('\nEnter project name: '))
  print('')

  return pname

################################################################################
#
# Function to read grid
#
################################################################################
def read_grid(fname):

# Open grid file
  f = open(fname)

# Read imax, jmax
# 3D grid specifies number of blocks on top line
  line1 = f.readline()
  flag = len(line1.split())
  if flag == 1:
    threed = True
  else:
    threed = False

  if threed:
    line1 = f.readline()
    imax, kmax, jmax = [int(x) for x in line1.split()]
  else:
    imax, jmax = [int(x) for x in line1.split()]
    kmax = 1

# Read geometry data
  x = np.zeros((imax,jmax))
  y = np.zeros((imax,jmax))
  if threed:
    for j in range(0, jmax):
      for k in range(0, kmax):
        for i in range(0, imax):
          x[i,j] = float(f.readline())
    for j in range(0, jmax):
      for k in range(0, kmax):
        for i in range(0, imax):
          dummy = float(f.readline())
    for j in range(0, jmax):
      for k in range(0, kmax):
        for i in range(0, imax):
          y[i,j] = float(f.readline())
  else:
    for j in range(0, jmax):
      for i in range(0, imax):
        x[i,j] = float(f.readline())

    for j in range(0, jmax):
      for i in range(0, imax):
        y[i,j] = float(f.readline())

# Print message
  print(('Successfully read grid file ' + fname))

# Close the file
  f.close

  return (imax, jmax, kmax, x, y, threed)

################################################################################
#
# Function to read Plot3D function file
#
################################################################################
def read_function_file(fname, imax, jmax, kmax, threed):

# Open stats file
  f = open(fname)

# Read first line to get variables category
  line1 = f.readline()
  varcat = line1[1:].rstrip()

# Second line gives variable names
  line1 = f.readline()
  varnames = line1[1:].rstrip()
  variables = varnames.split(", ")

# Number of variables
  nvars = len(variables)

# Initialize data and skip the next line
  values = np.zeros((nvars,imax,jmax))
  maxes = np.zeros((nvars))*-1000.0
  mins = np.ones((nvars))*1000.0
  line1 = f.readline()

# Read grid stats data, storing min and max
  for n in range(0, nvars):
    if (threed):
      for j in range(0, jmax):
        for k in range(0, kmax):
          for i in range(0, imax):
            values[n,i,j] = float(f.readline())
            if values[n,i,j] > maxes[n]:
              maxes[n] = values[n,i,j]
            if values[n,i,j] < mins[n]:
              mins[n] = values[n,i,j]
    else:
      for j in range(0, jmax):
        for i in range(0, imax):
          values[n,i,j] = float(f.readline())
          if values[n,i,j] > maxes[n]:
            maxes[n] = values[n,i,j]
          if values[n,i,j] < mins[n]:
            mins[n] = values[n,i,j]

# Print message
  print(('Successfully read data file ' + fname))

# Close the file
  f.close

  return (varcat, variables, values, mins, maxes)
  
################################################################################
#
# Function to select plot type
#
################################################################################
def select_plot_type():

# Get user input
  print('Select plot type or other operation:\n')
  print(' 1) Grid plot (grid only or colored by variable)')
  print(' 2) Contour plot of variables on grid') 
  print(' 3) Line plot of variables on surface') 
  print(' O) Change PostPycess options') 
  print(' L) Load new grid and data')
  print(' Q) Quit PostPycess')

  plottype = eval(input('\nInput: '))
  if (plottype != 'L' and plottype != 'l'):
    print('')

  return plottype

################################################################################
#
# Function to select plotting variable
#
################################################################################
def select_plot_var(plottype, catglist, varlist):

  nvars = len(varlist)

# Get user input for what to plot
  print(('Select plotting variable for ' + plottype + ' plot:\n'))
  print(' 1) plain - show geometry only')

  for i in range(0, nvars):
    print((' ' + str(i+2) + ') ' + varlist[i] + ' [' + catglist[i] + ']'))

  print(' Q) go back to main menu')
  plotvar = eval(input('\nInput: '))
  print('')

  return plotvar

################################################################################
#
# Function to change program options
#
################################################################################
def change_options(current_options):

# Available options
  optlist = ['Color for plain plots', 
             'Colormap for colored grid and contour plots',
             'Number of levels in contour plots',
             'Top-surface variable color in line plot',
             'Bottom-surface variable color in line plot']

  nopts = len(optlist)

# List of colors for plain plot
  colorlist = ['black', 'red', 'blue', 'green', 'orange', 'yellow', 'purple',
               'brown']

# List of colormaps
  cmaplist = ['autumn', 'brg', 'bwr', 'cool', 'coolwarm', 'copper', 'gray',
              'hot', 'hsv', 'jet', 'ocean', 'rainbow', 'spring', 'summer',
              'winter']

# Get user input for what option to change
  optdone = False
  while not optdone:
  
    print('Select option to change:\n')

    for i in range(0, nopts):
      print((' ' + str(i+1) + ') ' + optlist[i] \
            + ' (current = ' + str(current_options[i]) + ')'))

    print(' Q) Go back to the main menu')

    optselect = eval(input('\nInput: '))

#   Change requested option
    new_options = current_options
    if optselect == '1':
      new_options[0] = change_list_option(colorlist, 'plain color', 
                                          current_options[0])
    elif optselect == '2':
      new_options[1] = change_list_option(cmaplist, 'colormap', 
                                          current_options[1])
    elif optselect == '3':
      new_options[2] = change_int_option('number of contour levels',
                                         current_options[2])
    elif optselect == '4':
      new_options[3] = change_list_option(colorlist, 
                                          'top-surface variable color', 
                                          current_options[3])
    elif optselect == '5':
      new_options[4] = change_list_option(colorlist, 
                                          'bottom-surface variable color', 
                                          current_options[4])
    elif optselect == 'Q' or optselect == 'q':
      optdone = True
    else:
      print(('\nError: option ' + optselect + ' not recognized.\n'))

  print('')
  return new_options

################################################################################
#
# Function to change options specified in a list
#
################################################################################
def change_list_option(input_list, optname, currentval):

# Number of choices
  nvals = len(input_list)

  seldone = False
  while not seldone:

#   Print out available choices
    print(('\nAvailable choices for ' + optname + ':\n'))

    for i in range(0, nvals):
      print((' ' + str(i+1) + ') ' + input_list[i]))

    print(' Q) Go back to options menu')

    selected = eval(input('\nInput: '))

#   Change the option
    if is_int(selected) and int(selected) <= nvals:
      newval = input_list[int(selected) - 1]
      seldone = True
    elif selected == 'Q' or selected == 'q':
      seldone = True
      newval = currentval
    else:
      print(('\nError: option ' + selected + ' not recognized.'))
      seldone = False
    
  print('')
  return newval

################################################################################
#
# Function to change options that take int value
#
################################################################################
def change_int_option(optname, currentval):

  seldone = False
  while not seldone:

#   Print out prompt
    print(('\nEnter new value for ' + optname)) 
    print('  or Q to return to options menu:')

    selected = eval(input('\nInput: '))

#   Change the option
    if is_int(selected):
      newval = int(selected)
      seldone = True
    elif selected == 'Q' or selected == 'q':
      seldone = True
      newval = currentval
    else:
      print(('\nError: option ' + selected + ' not recognized.\n'))
      seldone = False

  print('')
  return newval

################################################################################
#
# Function to transform a line (x and y vectors) to numpy segments for line
# Collection
#
################################################################################
def line_to_segments(x, y):

  points = np.array([x, y]).T.reshape(-1, 1, 2)
  segments = np.concatenate([points[:-1], points[1:]], axis=1)
  return segments

################################################################################
#
# Function to add a colorbar to a plot colored by the range (minvar, maxvar)
# colormap is 'jet', 'greyscale', etc
#
################################################################################
def faux_colorbar(minvar, maxvar, varname, colormap):

  colorx = np.linspace(0.0, 1.0, 10)
  colory = np.linspace(minvar, maxvar, 10)
  segments = line_to_segments(colorx, colory)
  colors = LineCollection(segments, cmap=plt.get_cmap(colormap),
           norm=plt.Normalize(minvar, maxvar))
  colors.set_array(colory)
  cbar=plt.colorbar(colors)
  cbar.set_label(varname, rotation=270)

################################################################################
#
# Function to plot colored or plain grid
#
################################################################################
def plot_grid(x, y, colormap=None, plaincolor=None,
              varname=None, var=None, minvar=None, maxvar=None):

# colormap and plaincolor are optional - set defaults
  if colormap == None:
    colormap = 'jet'
  if plaincolor == None:
    plaincolor = 'black'

# Last four parameters optional: if not supplied, plain grid is plotted
  if varname == None:
    print('Plotting plain grid ...\n')
    colorplot = False
  else:
    print(('Plotting grid colored by ' + varname + ' ...\n'))
    colorplot = True

# Determine grid dimensions
  imax = x.shape[0]
  jmax = x.shape[1]

# Initialize plot
  fig = plt.figure()
  ax = fig.add_subplot(111)

# See http://wiki.scipy.org/Cookbook/Matplotlib/MulticoloredLine
# LineCollection type allows color to vary along the line according
#   to a parameter.
  for j in range(0, jmax):
    segments = line_to_segments(x[:,j], y[:,j])
    if colorplot:
      lc = LineCollection(segments, cmap=plt.get_cmap(colormap),
           norm=plt.Normalize(minvar, maxvar))
      lc.set_array(var[:,j])
    else:
      lc = LineCollection(segments, colors=plaincolor)
    ax.add_collection(lc)
  for i in range(0, imax):
    segments = line_to_segments(x[i,:], y[i,:])
    if colorplot:
      lc = LineCollection(segments, cmap=plt.get_cmap(colormap),
           norm=plt.Normalize(minvar, maxvar))
      lc.set_array(var[i,:])
    else:
      lc = LineCollection(segments, colors=plaincolor)
    ax.add_collection(lc)

# Create colorbar and title
  if colorplot:
    faux_colorbar(minvar, maxvar, varname, colormap)
    title = 'Grid geometry colored by ' + varname
  else:
    title = 'Grid geometry'

# Show plot
  plt.title(title)
  plt.xlabel('x')
  plt.ylabel('y')
  plt.axis('equal')
  #plt.show(block=False)
  plt.show()

################################################################################
#
# Bilinear interpolation to interpolate between 4 points in rectangular grid
# Inputs:
#   corners: 4x2 numpy array of points (x, y), arranged starting from bottom
#      left in counter-clockwise order
#   cornervals: 4x1 numpy array of values at the corner points
#   point: numpy 1x2 array of input point
# Output:
#   pointval: the interpolated value of the function at the given point
#
################################################################################
def bilinear_interpolation(corners, cornervals, point):

  x = corners[:,0]
  y = corners[:,1]

  x1 = x[0]
  y1 = y[0]
  x2 = x[1]
  y2 = y[2]
  x = point[0]
  y = point[1]

  pointval = 1./(x2-x1)*(cornervals[0]*(x2 - x)*(y2 - y) +
                         cornervals[1]*(x - x1)*(y2 - y) +
                         cornervals[3]*(x2 - x)*(y - y1) +
                         cornervals[2]*(x - x1)*(y - y1))
  return pointval

################################################################################
#
# Given xi-eta coordinates of points on line in xi-eta space, returns
# indices of points for interpolation on grid
#
################################################################################
def interpolation_indices(xipt, etapt, imax, jmax):

  xi1 = int(math.floor(xipt)) - 1
  if xi1 == imax - 1:
    xi1 = imax - 2
  xi2 = xi1 + 1
  eta1 = int(math.floor(etapt)) - 1
  if eta1 == jmax - 1:
    eta1 = jmax - 2
  eta2 = eta1 + 1

  return (xi1, eta1, xi2, eta2)

################################################################################
#
# Takes contours of a variable from xi-eta space, interpolates them to
# x-y space, and generates colored contour plot. CS is the contour object
# from xi-eta space.  Also requires min and max variable values for coloring
#
################################################################################
def interpolate_contours(x, y, xi, eta, CS, minval, maxval, colormap):

  imax = x.shape[0]
  jmax = x.shape[1]

# Set up coloring data
  cNorm = colorobj.Normalize(vmin=minval, vmax=maxval)
  scalarMap = cmobj.ScalarMappable(norm=cNorm, cmap=plt.get_cmap(colormap))

# Number of collections - this is the number of distinct contour levels
  ncollect = len(CS.collections)

# Iterate over each collection
  for i in range(0, ncollect):
    npaths = len(CS.collections[i].get_paths())

#   Iterate over each line in each collection
    for j in range(0, npaths):

#     Path and contour level
      path = CS.collections[i].get_paths()[j]
      level = CS.levels[i]

#     Store points in xi, eta vectors for each line
      # Should use iter_segments()
      vertices = path.vertices
      xiln = vertices[:,0]
      etaln = vertices[:,1]
      nvert = xiln.shape[0]

      xln = np.zeros((nvert,1))
      yln = np.zeros((nvert,1))
      for k in range(0, nvert):

#       Use bilinear interpolation to transform from xi-eta to x
        xi1, eta1, xi2, eta2 = \
             interpolation_indices(xiln[k], etaln[k], imax, jmax)
        corners = np.array([[xi[xi1,eta1], eta[xi1,eta1]],
                            [xi[xi2,eta1], eta[xi2,eta1]],
                            [xi[xi2,eta2], eta[xi2,eta2]],
                            [xi[xi1,eta2], eta[xi1,eta2]]])
        cornervals = np.array([x[xi1,eta1], x[xi2,eta1], 
                               x[xi2,eta2], x[xi1,eta2]])
        point = np.array([xiln[k], etaln[k]])
        xln[k] =  bilinear_interpolation(corners, cornervals, point)

#       Use bilinear interpolation to transform from xi-eta to y
        corners = np.array([[xi[xi1,eta1], eta[xi1,eta1]],
                            [xi[xi2,eta1], eta[xi2,eta1]],
                            [xi[xi2,eta2], eta[xi2,eta2]],
                            [xi[xi1,eta2], eta[xi1,eta2]]])
        cornervals = np.array([y[xi1,eta1], y[xi2,eta1], 
                               y[xi2,eta2], y[xi1,eta2]])
        point = np.array([xiln[k], etaln[k]])
        yln[k] =  bilinear_interpolation(corners, cornervals, point)

#     Plot line with mapped color
      colorval = scalarMap.to_rgba(level)
      plt.plot(xln,yln,color=colorval)

################################################################################
#
# Driver function to plot contours
#
################################################################################
def plot_contours(x, y, colormap=None, plaincolor=None, nlevels=None, 
                  varname=None, var=None, minvar=None, maxvar=None):

# optional settings - set defaults
  if colormap == None:
    colormap = 'jet'
  if nlevels == None:
    nlevels = 15
  if plaincolor == None:
    plaincolor = 'black'

# Last four parameters optional: if not supplied, only boundaries shown
  if varname == None:
    print('Plotting grid boundaries only ...\n')
    contourplot = False
  else:
    print(('Plotting contours of ' + varname + ' ...\n'))
    contourplot = True

  imax = x.shape[0]
  jmax = x.shape[1]

# Do the following only if a plotting variable is actually supplied
  if contourplot:

#   Initially, create contours in xi-eta space, since it is rectangular
    xilev = np.arange(1.0, float(imax+1), 1.0)
    etalev = np.arange(1.0, float(jmax+1), 1.0)
    xi, eta = np.meshgrid(xilev, etalev)

    xi = np.transpose(xi)
    eta = np.transpose(eta)

    plt.figure()
    CS = plt.contour(xi, eta, var, nlevels)
    
#   Remove rectangular grid contours
    plt.clf()

#   Interpolate contours to x-y space and plot manually
    interpolate_contours(x, y, xi, eta, CS, minvar, maxvar, colormap)

#   Create colorbar for plot
    faux_colorbar(minvar, maxvar, varname, colormap)

#   Set title
    title = 'Contours of ' + varname

  else:

#   Set title
    title = 'Grid boundaries'

# Add grid boundaries to plot
  plt.plot(x[:,0], y[:,0], color=plaincolor)
  plt.plot(x[:,jmax-1], y[:,jmax-1], color=plaincolor)
  plt.plot(x[0,:], y[0,:], color=plaincolor)
  plt.plot(x[imax-1,:], y[imax-1,:], color=plaincolor)

# Show plot
  plt.title(title)
  plt.xlabel('x')
  plt.ylabel('y')
  plt.axis('equal')
  plt.show()

################################################################################
#
# Function to get indices of airfoil surface
# Distinguishes between airfoil surface and cut plane for C-grid
#
################################################################################
def get_srf_bounds(x, y):

  imax = x.shape[0]

  surface = False
  i = 1
  while not surface:
    cutindex = imax - 1 - i
    if x[i] != x[cutindex] or y[i] != y[cutindex]:
      surface = True
      srf1 = i - 1
      srf2 = cutindex + 1
    i += 1

  return (srf1, srf2)

################################################################################
#
# Function to get index of leading edge
#
################################################################################
def get_leading_edge(x):

  imax = x.shape[0]

  xmin = 1000
  for i in range(0, imax):
    if x[i] < xmin:
      xmin = x[i]
      le_index = i

  return le_index

################################################################################
#
# Function to plot variables on airfoil surface
# x, y, and the variable are only passed to this function on j=0
#
################################################################################
def plot_surface(x, y, plaincolor=None, topcolor=None, botcolor=None,
                 varname=None, var=None):

# Optional settings: set defaults
  if plaincolor == None:
    plaincolor = 'black'
  if topcolor == None:
    topcolor = 'red'
  if botcolor == None:
    botcolor = 'blue'

# Last two parameters optional: if not supplied, only surface shown
  if varname == None:
    print('Plotting airfoil surface only ...\n')
    surfplot = False
  else:
    print(('Plotting ' + varname + ' on airfoil surface ...\n'))
    surfplot = True

# Determine airfoil boundaries (distinguish from symmetry boundary in C-grid)
  srf1, srf2 = get_srf_bounds(x, y)

# Determine leading edge location
  le_index = get_leading_edge(x)

# Plot only the airfoil surface if no variable is identified
  if surfplot:
    plt.plot(x[srf1:le_index], var[srf1:le_index], color=topcolor,
             label='Top')
    plt.plot(x[le_index:srf2], var[le_index:srf2], color=botcolor,
             label='Bottom')
    ylabel = varname
    title = 'Airfoil surface ' + varname
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width*0.87, box.height])
    plt.legend(bbox_to_anchor=(1.02, 1.), loc=2, borderaxespad=0.)
  else:
    plt.plot(x[srf1:srf2], y[srf1:srf2], color=plaincolor)
    ylabel = 'y'
    title = 'Airfoil surface'
    plt.axis('equal')

# Show plot
  plt.title(title)
  plt.xlabel('x')
  plt.ylabel(ylabel)
  plt.show()

### End of functions ###
################################################################################

# Run main program
main()
