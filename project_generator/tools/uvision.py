# Copyright 2015 0xc0170
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import xmltodict
import copy

from os.path import basename, join, normpath
from os import getcwd
from .exporter import Exporter
from .builder import Builder
import re
from ..util import FILES_EXTENSIONS,SOURCE_KEYS

class uVisionDefinitions():
    debuggers = {
        'cmsis-dap': {
            'TargetDlls': {
                'Driver' : 'BIN\CMSIS_AGDI.dll',
            },
        },
        'j-link': {
            'TargetDlls': {
                'Driver' : 'Segger\JL2CM3.dll',
            },
        }
    }

    uvision_settings = {
        # C/C++ settings
        'Cads': {
            'Optim':[0],
            'MiscControls': [],  # Misc controls
        },

        # Assembly settings
        'Aads': {
            'MiscControls': [],    # Misc controls
            'IncludePath': [],     # Include paths
        },
        'TargetDlls': {

        },
    }


class Uvision(Builder, Exporter):

    optimization_options = ['O0', 'O1', 'O2', 'O3']
    file_types = {}
    for key in SOURCE_KEYS:
        for extension in FILES_EXTENSIONS[key]:
            type = key.split("_")[-1]
            if type == 'cpp':
                file_types[extension] = 8
            if type == 'c':
                file_types[extension] = 1
            if type == 's':
                file_types[extension] = 2
            if type == 'a':
                file_types[extension] = 4
            if type == 'obj':
                file_types[extension] = 3

    #file_types = {'cpp': 8, 'c': 1, 's': 2, 'S':2,'obj': 3,'o':3, 'lib': 4, 'ar': 4}

    ERRORLEVEL = {
        0: '(0 warnings, 0 errors)',
        1: 'warnings',
        2: 'errors',
        3: 'fatal errors',
        11: 'cant write to project file',
        12: 'device error',
        13: 'error writing',
        15: 'error reading xml file',
    }

    SUCCESSVALUE = 0
    WARNVALUE = 1

    def __init__(self, workspace, env_settings):
        self.definitions = uVisionDefinitions()
        # workspace or project
        self.workspace = workspace
        self.env_settings = env_settings

    @staticmethod
    def get_toolnames():
        return ['uvision']

    @staticmethod
    def get_toolchain():
        return 'uvision'

    def _expand_data(self, file, new_data, group):
        """ data expansion - uvision needs filename and path separately. """
        extension = file.split(".")[-1]
        new_file = {"FilePath": file, "FileName": basename(file),
                                "FileType": self.file_types[extension]}
        new_data['groups'][group].append(new_file)

    def _iterate(self, data, expanded_data):
        """ Iterate through all data, store the result expansion in extended dictionary. """
        for attribute in SOURCE_KEYS:
            for k, v in data[attribute].items():
                for file in v:
                    self._expand_data(file, expanded_data, k)

    def parse_specific_options(self, data):
        """ Parse all uvision specific setttings. """
        default_set = copy.deepcopy(self.definitions.uvision_settings)
        data['uvision_settings'].update(default_set)  # set specific options to default values
        for section, controls in data['misc'].items():
            for k,v in controls.items():
                for setting in v:
                    if section == "C" and k == 'MiscControls':
                        data['uvision_settings']['Cads']['MiscControls'].append(str(setting))
                    if section == "ASM" and k == 'MiscControls':
                        data['uvision_settings']['Aads']['MiscControls'].append(str(setting))

    def _get_groups(self, data):
        """ Get all groups defined. """
        groups = []
        for attribute in SOURCE_KEYS:
                if data[attribute]:
                    for k, v in data[attribute].items():
                        if k == None:
                            k = 'Sources'
                        if k not in groups:
                            groups.append(k)
        return groups

    def append_mcu_def(self, data, mcu_def):
        """ Get MCU definitons as Flash algo, RAM, ROM size , etc. """
        try:
            data['uvision_settings'].update(mcu_def['TargetOption'])
        except KeyError:
            # does not exist, create it
            data['uvision_settings'] = mcu_def['TargetOption']

    def parse_data(self, tool, data):
        groups = self._get_groups(self.workspace)
        data['groups'] = {}
        for group in groups:
            data['groups'][group] = []

        self._iterate(self.workspace, data)

        data['uvision_settings'] = {}
        self.parse_specific_options(data)

        data['build_dir'] = '.\\' + data['build_dir'] + '\\'

        # set target only if defined, otherwise use from template/default one

        mcu_def_dic = data['target'].get_tool_configuration(tool)
        if mcu_def_dic is None:
            return None
        logging.debug("Mcu definitions: %s" % mcu_def_dic)
        self.append_mcu_def(data, mcu_def_dic)

        # load debugger
        driver = self.definitions.debuggers[data['debugger']]['TargetDlls']['Driver']
        data['uvision_settings']['TargetDlls']['Driver'] = driver
        # optimization set to correct value, default not used
        data['uvision_settings']['Cads']['Optim'][0] = 1

        data ['core'] = data ['target'].core

        #Target has f postfix, IE cortex-m4f
        if data['target'].fpu:
            #Remove the f from the end
            data['core'] = data['core'][:-1]
            data['uvision_settings']['Cpu'] = "CPUTYPE(\""+data['core']+"\")"
            #Add FPU option to CPU info
            data['uvision_settings']['Cpu'] += " FPU2"
        else:
            data['uvision_settings']['Cpu'] = "CPUTYPE(\""+data['core']+"\")"

    def generate_project(self):
        expanded_dic = self.workspace.copy()
        self.parse_data('uvision',expanded_dic)
        # Project file
        self.generate_file('uvision4.uvproj.tmpl',expanded_dic,'uvproj')
        return 0

    def generate_file(self,tmpl,data,ext):
         self.gen_file_jinja(
            tmpl, data, '%s.%s'%(self.workspace['name'],ext), data['output_dir']['path'])

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['uvproj']]}

    def supports_target(self, target):
        return target in self.definitions.mcu_def

    def build_project(self):
        # > UV4 -b [project_path]
        path = ''
        pattern = str(self.workspace['name']) + r"\.uvproj[x]?"
        for file in os.listdir(self.workspace['output_dir']['path']):
            if re.match(pattern,file):
                path = join(self.workspace['output_dir']['path'],file)

        if not os.path.exists(path):
            logging.critical("The file: %s does not exist. You must call generate before build." % path)
            return None

        proj_name = path.split(os.path.sep)[-1]

        args = [self.env_settings.get_env_settings('uvision'), '-r', '-j0', '-o', './build/build_log.txt', path]
        ret = Builder.build_command(args, self, "Uvision", proj_name)
        if ret < 0 and logging.getLogger().isEnabledFor(logging.DEBUG):
            build_path = join(self.workspace['output_dir']['path'], 'build', 'build_log.txt')
            with open(build_path, 'r+') as f:
                logging.debug(" BUILD LOG\n" + "\n".join(f.readlines()))
        return ret

    def get_mcu_definition(self, project_file, mcu):
        """ Parse project file to get target definition """
        project_file = join(getcwd(), project_file)
        uvproj_dic = xmltodict.parse(file(project_file), dict_constructor=dict)
        # Generic Target, should get from Target class !
        core = uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Cpu']
        regex = r"CPUTYPE\(\"([\w-]+)\"\)\s*(FPU2)?"
        match = re.search(regex,core)
        if match:
            mcu['mcu']['core'] = match.group(1)
            if match.group(2):
                mcu['mcu']['core']+='f'

        mcu['tool_specific']['uvision'] = {
                'TargetOption' : {
                    'Device' : uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Device'],
                    'DeviceId' : int(uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['DeviceId']),
                }
        }

        return mcu
