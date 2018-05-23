__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import numpy as np

from cfd.CFDrun import CFDrun
from constants import *

import matplotlib.pyplot as plt


##################################
### naca Test                  ###

#su2 = SU2(SU2_BIN_PATH, used_cores=SU2_USED_CORES, mpi_exec=OS_MPI_COMMAND)

def run_convergence_analysis_gmsh():
    config = dict()
    config['PHYSICAL_PROBLEM'] = 'EULER'
    config['MACH_NUMBER'] = str(0.65)
    config['AOA'] = str(1.25)
    config['FREESTREAM_PRESSURE'] = str(24999.8) #for altitude 10363 m
    config['FREESTREAM_TEMPERATURE'] = str(220.79) #for altitude 10363 m
    #config['GAS_CONSTANT'] = str(287.87)
    #config['REF_LENGTH'] = str(1.0)
    #config['REF_AREA'] = str(1.0)
    config['MARKER_EULER'] = '( airfoil )'
    config['MARKER_FAR'] = '( farfield )'
    config['EXT_ITER'] = str(1000)
    config['OUTPUT_FORMAT'] = 'PARAVIEW'
    config['MG_DAMP_RESTRICTION'] = str(0.75)
    config['MG_DAMP_PROLONGATION'] = str(0.75)

    #for gmsh
    innerMeshSize = np.linspace(0.001, 0.01, 21)
    outerMeshSize = np.linspace(0.1, 1., 21)
    innerMeshSize = np.flip(innerMeshSize, 0)
    outerMeshSize = np.flip(outerMeshSize, 0)

    cdList = np.zeros((len(innerMeshSize),len(outerMeshSize)))
    clList = np.zeros((len(innerMeshSize),len(outerMeshSize)))
    cmList = np.zeros((len(innerMeshSize),len(outerMeshSize)))
    eList = np.zeros((len(innerMeshSize),len(outerMeshSize)))

    ouputF = open(WORKING_DIR + '/' + 'convergenceResult.txt', 'w')
    ouputF.write('innerMeshSize,outerMeshSize,CL,CD,CM,E,Iterations,Time(min)\n')

    for iI in range(0, len(innerMeshSize)):
        for iO in range(0, len(outerMeshSize)):

            projectName = 'nacaMesh_i%06d_o%06d' % (int(innerMeshSize[iI]*1000), int(outerMeshSize[iO]*1000))
            projectDir = WORKING_DIR + '/' + projectName
            #create project dir if necessary
            if not os.path.isdir(projectDir):
                os.mkdir(projectDir)

            cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)
            cfd.load_airfoil_from_file(INPUT_DIR + '/naca641-212.csv')
            cfd.gmsh.innerMeshSize = innerMeshSize[iI]
            cfd.gmsh.outerMeshSize = outerMeshSize[iO]
            #cfd.gmsh_generate_mesh()
            cfd.gmsh_generate_mesh()
            cfd.su2_fix_mesh()
            cfd.su2_solve(config)
            results = cfd.su2_parse_iteration_result()
            #totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()
            totalCL = results['CL']
            totalCD = results['CD']
            totalCM = results['CMz']
            totalE = results['CL/CD']
            clList[iI][iO] = totalCL
            cdList[iI][iO] = totalCD
            cmList[iI][iO] = totalCM
            eList[iI][iO] = totalE
            ouputF.write(str(innerMeshSize[iI])+','
                         +str(outerMeshSize[iO])+','
                         +str(totalCL)+','
                         +str(totalCD)+','
                         +str(totalCM)+','
                         +str(totalE)+','
                         +str(results['Iteration'])+','
                         +str(results['Time(min)'])+'\n')
            ouputF.flush()

            print('totalCL: ' + str(totalCL))
            print('totalCD: ' + str(totalCD))
            print('iI: ' + str(iI) + ' iO: ' + str(iO))


    plt.pcolor(innerMeshSize, outerMeshSize, clList)
    plt.colorbar()
    plt.show()
    print('done')

def run_convergence_analysis_construct2d():
    config = dict()
    config['PHYSICAL_PROBLEM'] = 'EULER'
    config['MACH_NUMBER'] = str(0.65)
    config['AOA'] = str(0.)
    config['FREESTREAM_PRESSURE'] = str(24999.8)  # for altitude 10363 m
    config['FREESTREAM_TEMPERATURE'] = str(220.79)  # for altitude 10363 m
    # config['GAS_CONSTANT'] = str(287.87)
    # config['REF_LENGTH'] = str(1.0)
    # config['REF_AREA'] = str(1.0)
    config['MARKER_EULER'] = '( airfoil )'
    config['MARKER_FAR'] = '( farfield )'
    config['EXT_ITER'] = str(1000)
    config['OUTPUT_FORMAT'] = 'PARAVIEW'
    config['MG_DAMP_RESTRICTION'] = str(0.75)
    config['MG_DAMP_PROLONGATION'] = str(0.75)


    #for construct 2d
    normalMeshDivider = [100] #range(60, 500, 10)
    secondParam = [250]


    cdList = np.zeros((len(normalMeshDivider),len(secondParam)))
    clList = np.zeros((len(normalMeshDivider),len(secondParam)))
    cmList = np.zeros((len(normalMeshDivider),len(secondParam)))
    eList = np.zeros((len(normalMeshDivider),len(secondParam)))

    ouputF = open(WORKING_DIR + '/' + 'convergenceResult.txt', 'w')
    ouputF.write('innerMeshSize,outerMeshSize,CL,CD,CM,E,Iterations,Time(min)\n')

    for iI in range(0, len(normalMeshDivider)):
        for iO in range(0, len(secondParam)):

            projectName = 'nacaMesh_i%06d_o%06d' % (int(normalMeshDivider[iI]), int(secondParam[iO]))
            projectDir = WORKING_DIR + '/' + projectName
            #create project dir if necessary
            if not os.path.isdir(projectDir):
                os.mkdir(projectDir)

            cfd = CFDrun(projectName, used_cores=SU2_USED_CORES)
            cfd.load_airfoil_from_file(INPUT_DIR + '/naca641-212.csv')
            cfd.c2d.pointsInNormalDir = normalMeshDivider[iI]
            #cfd.gmsh.outerMeshSize = outerMeshSize[iO]
            #cfd.gmsh_generate_mesh()
            cfd.construct2d_generate_mesh()
            cfd.su2_fix_mesh()
            cfd.su2_solve(config)
            results = cfd.su2_parse_iteration_result()
            #totalCL, totalCD, totalCM, totalE = cfd.su2_parse_results()
            totalCL = results['CL']
            totalCD = results['CD']
            totalCM = results['CMz']
            totalE = results['CL/CD']
            clList[iI][iO] = totalCL
            cdList[iI][iO] = totalCD
            cmList[iI][iO] = totalCM
            eList[iI][iO] = totalE
            ouputF.write(str(normalMeshDivider[iI])+','
                         +str(secondParam[iO])+','
                         +str(totalCL)+','
                         +str(totalCD)+','
                         +str(totalCM)+','
                         +str(totalE)+','
                         +str(results['Iteration'])+','
                         +str(results['Time(min)'])+'\n')
            ouputF.flush()

            print('totalCL: ' + str(totalCL))
            print('totalCD: ' + str(totalCD))
            print('iI: ' + str(iI) + ' iO: ' + str(iO))


    ouputF.close()
    plt.pcolor(normalMeshDivider, secondParam, clList)
    plt.colorbar()
    plt.show()
    print('done')

def plot_output_data():
    data = np.genfromtxt(WORKING_DIR + '/' + 'convergenceResult.txt', delimiter=',', skip_header=1)
    x = data[:,0]
    y = data[:,1]
    cl = data[:,2]
    cd = data[:,3]
    iters = data[:,6]
    times = data[:,7]
    xAx = np.unique(x)
    yAx = np.unique(y)
    clMat = np.empty((len(yAx), len(xAx)))
    clMat[:] = np.nan
    cdMat = np.empty((len(yAx), len(xAx)))
    cdMat[:] = np.nan
    iterMat = np.empty((len(yAx), len(xAx)))
    iterMat[:] = np.nan
    timeMat = np.empty((len(yAx), len(xAx)))
    timeMat[:] = np.nan

    for i in range(0, len(cl)):
        clMat[int(np.where(yAx == y[i])[0])][int(np.where(xAx == x[i])[0])] = cl[i]
        cdMat[int(np.where(yAx == y[i])[0])][int(np.where(xAx == x[i])[0])] = cd[i]
        iterMat[int(np.where(yAx == y[i])[0])][int(np.where(xAx == x[i])[0])] = iters[i]
        timeMat[int(np.where(yAx == y[i])[0])][int(np.where(xAx == x[i])[0])] = times[i]

    fig, ax = plt.subplots()
    ax1  = plt.subplot(1, 2, 1)
    im1 = ax1.imshow(clMat)
    ax1.set_xticks(np.arange(len(xAx)))
    ax1.set_yticks(np.arange(len(yAx)))
    ax1.set_xticklabels(xAx)
    ax1.set_yticklabels(yAx)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    plt.colorbar(im1)

    ax1 = plt.subplot(1, 2, 2)
    im1 = ax1.imshow(cdMat)
    ax1.set_xticks(np.arange(len(xAx)))
    ax1.set_yticks(np.arange(len(yAx)))
    ax1.set_xticklabels(xAx)
    ax1.set_yticklabels(yAx)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    plt.colorbar(im1)
    plt.show()


if __name__ == '__main__':
    #run_convergence_analysis_gmsh()
    run_convergence_analysis_construct2d()
    #plot_output_data()
