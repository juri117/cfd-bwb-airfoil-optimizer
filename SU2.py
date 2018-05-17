__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

import subprocess
import os
import numpy as np
import re

class SU2:

    def __init__(self, su2_binaries_path, used_cores=1, mpi_exec='mpiexec'):
        self.su2BinPath = su2_binaries_path
        self.usedCores = used_cores
        self.mpiExec = mpi_exec
        self.errorFlag = False

    def fix_mesh(self, input_su2_file, output_su2_file, working_dir='outDir/'):
        config = dict()
        config['MESH_FILENAME'] = input_su2_file
        config['MESH_OUT_FILENAME'] = output_su2_file
        self.generate_config_file('meshFix.cfg', config, working_dir=working_dir)
        p = subprocess.Popen([self.su2BinPath + '/SU2_MSH',
                              'meshFix.cfg'],
                             cwd=working_dir, stdout=subprocess.PIPE)
        out, err = p.communicate()
        print(out.decode('UTF-8'))
        if err is not None:
            print('SU2_MSH process failed')
            self.errorFlag = True
        if 'Exit Success (SU2_MSH)' in out.decode('UTF-8'):
            print('SU2_MSH process successful')

    def write_single_core_batch_file(self, input_cfg_file='cfdRun.cfg', working_dir='outDir/'):
        runCommand = '"'
        runCommand += os.path.abspath(self.su2BinPath) + '/SU2_CFD.exe'
        runCommand += '" '
        runCommand += input_cfg_file
        ouputF = open(working_dir + '/' + 'singleCoreCfdRun.bat', 'w')
        ouputF.write(runCommand)
        ouputF.close()

    def write_multi_core_batch_file(self, input_cfg_file='cfdRun.cfg', working_dir='outDir/'):
        runCommand = 'powershell.exe -Command '
        runCommand += '"'
        runCommand += self.mpiExec + ' '
        runCommand += '-n ' + str(self.usedCores) + ' '
        runCommand += os.path.abspath(self.su2BinPath) + '/SU2_CFD.exe '
        runCommand += input_cfg_file
        runCommand += '"'

        ouputF = open(working_dir + '/' + 'cfdMpiRun.bat', 'w')
        ouputF.write(runCommand)
        ouputF.close()

    def run_cfd(self, input_su2_file, configDict, input_cfg_file='cfdRun.cfg', working_dir='outDir/'):
        configDict['MESH_FILENAME'] = input_su2_file
        self.generate_config_file('cfdRun.cfg', configDict, working_dir=working_dir)
        print('run SU2_CFD on ' + str(self.usedCores) + ' core(s)...')
        if self.usedCores == 1:
            p = subprocess.Popen([self.su2BinPath + '/SU2_CFD',
                                  input_cfg_file],
                                 cwd=working_dir)#, stdout=subprocess.PIPE)
        else:
            ####powershell.exe -Command "mpiexec ../../su2-windows-latest/ExecParallel/bin/SU2_CFD.exe cfdRun.cfg"
            self.write_multi_core_batch_file(input_cfg_file=input_cfg_file, working_dir=working_dir)
            batchFilePath = os.path.abspath(working_dir + '/' + 'cfdMpiRun.bat')
            p = subprocess.Popen([batchFilePath], cwd=working_dir)
        p.wait()
        '''
        out, err = p.communicate()
        print(out.decode('UTF-8'))
        if err is not None:
            print('SU2_MSH process failed')
            self.errorFlag = True
        if 'Exit Success (SU2_CFD)' in out.decode('UTF-8'):
            print('SU2_CFD process successful')
        '''


    def generate_config_file(self, ouput_cfg_file_name, configDict, working_dir='outDir/', default_cfg_file_path='dataIn/default.cfg'):
        inputF =  open(default_cfg_file_path, 'r')
        lines = inputF.read().splitlines()
        config = configDict.copy()

        ouputF = open(working_dir + '/' + ouput_cfg_file_name, 'w')

        for line in lines:
            #just copy the comments
            if len(line) > 0:
                if line.lstrip()[0] == '%':
                    ouputF.write(line + '\n')
                else:
                    paramName = line.strip().replace(' ','').split('=')[0].upper()
                    if paramName in config.keys():
                        ouputF.write(paramName + '= ' + config[paramName] + '\n')
                        del config[paramName]
                    else:
                        ouputF.write(line + '\n')
            else:
                ouputF.write('\n')
        inputF.close()
        # add remaining config variables if there are any
        if len(config) > 0:
            ouputF.write('\n%remaining custom variables\n')
            for key, value in config.items():
                ouputF.write(key + '= ' + value + '\n')
        ouputF.close()

    def parse_force_breakdown(self, forces_breakdown_file_name, working_dir='outDir/'):
        f = open(working_dir + '/' + forces_breakdown_file_name)
        lines = f.read().splitlines()
        totalCL = 0.
        totalCD = 0.
        totalCM = 0.
        totalE = 0.
        for l in lines:
            if 'Total CL:' in l:
                totalCL = float(self._parse_param_from_row(l))
            if 'Total CD:' in l:
                totalCD = float(self._parse_param_from_row(l))
            if 'Total CL/CD:' in l:
                totalE = float(self._parse_param_from_row(l))
            if 'Total CMz:' in l:
                totalCM = float(self._parse_param_from_row(l))
        return totalCL, totalCD, totalCM, totalE

    def parse_result_from_history(self, history_file_name, working_dir='outDir/'):
        f = open(working_dir + '/' + history_file_name)
        lines = f.read().splitlines()
        outDict = dict()
        paraNames = lines[0].split(',')
        paraNames = [p.replace('"', '') for p in paraNames]
        finalLine = lines[-1]
        if len(finalLine) == 0:
            finalLine = lines[-2]
        finalLine = finalLine.strip().replace(' ', '')
        values = finalLine.split(',')
        if len(paraNames) != len(values):
            print('ERROR: csv is not homegenious, file path: ' + working_dir + '/' + history_file_name)
        for i in range(0, len(values)):
            outDict[paraNames[i]] = values[i]
        return outDict

    def _parse_param_from_row(self, rowStr):
        rowStr = rowStr.strip()
        rowStr = rowStr.replace(' ', '')
        param = list(filter(None, re.findall(r"[-+]?[0-9]*\.?[0-9]*", rowStr)))
        return param[0]