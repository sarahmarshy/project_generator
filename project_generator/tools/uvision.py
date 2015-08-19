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
from ..targets import Targets

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
    source_files_dic = ['source_files_c', 'source_files_s', 'source_files_cpp', 'source_files_a', 'source_files_obj']
    file_types = {'cpp': 8, 'c': 1, 's': 2, 'obj': 3,'o':3, 'lib': 4, 'ar': 4}

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

    def _expand_data(self, old_data, new_data, attribute, group, rel_path):
        """ data expansion - uvision needs filename and path separately. """
        if group == 'Sources':
            old_group = None
        else:
            old_group = group
        for file in old_data[old_group]:
            if file:
                extension = file.split(".")[-1]
                if extension in self.file_types:
                    new_file = {"FilePath": rel_path + normpath(file), "FileName": basename(file),
                                "FileType": self.file_types[extension]}
                    new_data['groups'][group].append(new_file)
                else:
                    continue

    def _iterate(self, data, expanded_data, rel_path):
        """ Iterate through all data, store the result expansion in extended dictionary. """
        for attribute in self.source_files_dic:
            for k, v in data[attribute].items():
                if k == None:
                    group = 'Sources'
                else:
                    group = k
                self._expand_data(data[attribute], expanded_data, attribute, group, rel_path)

    def parse_specific_options(self, data):
        """ Parse all uvision specific setttings. """
        default_set = copy.deepcopy(self.definitions.uvision_settings)
        data['uvision_settings'].update(default_set)  # set specific options to default values
        for k, v in data['misc'].items():
                if k == 'MiscControls':
                    data['uvision_settings']['Cads']['MiscControls'] = "--"+str(v)

    def _get_groups(self, data):
        """ Get all groups defined. """
        groups = []
        for attribute in self.source_files_dic:
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

    def _normalize_mcu_def(self, mcu_def):
        for k, v in mcu_def['TargetOption'].items():
            mcu_def['TargetOption'][k] = v[0]

    def _fix_paths(self, data, rel_path):
        data['includes'] = [join(rel_path, normpath(path)) for path in data['includes']]

        if type(data['source_files_a']) == type(dict()):
            for k in data['source_files_a'].keys():
                data['source_files_a'][k] = [
                    join(rel_path, normpath(path)) for path in data['source_files_a'][k]]
        else:
            data['source_files_a'] = [
                join(rel_path, normpath(path)) for path in data['source_files_a']]

        if type(data['source_files_obj']) == type(dict()):
            for k in data['source_files_obj'].keys():
                data['source_files_obj'][k] = [
                    join(rel_path, normpath(path)) for path in data['source_files_obj'][k]]
        else:
            data['source_files_obj'] = [
                join(rel_path, normpath(path)) for path in data['source_files_obj']]

        if data['linker_file']:
            data['linker_file'] = join(rel_path, normpath(data['linker_file']))

    def export_project(self):
        expanded_dic = self.workspace.copy()

        groups = self._get_groups(self.workspace)
        expanded_dic['groups'] = {}
        for group in groups:
            expanded_dic['groups'][group] = []

        # get relative path and fix all paths within a project
        self._iterate(self.workspace, expanded_dic, expanded_dic['output_dir']['rel_path'])
        self._fix_paths(expanded_dic, expanded_dic['output_dir']['rel_path'])

        expanded_dic['uvision_settings'] = {}
        self.parse_specific_options(expanded_dic)

        expanded_dic['build_dir'] = '.\\' + expanded_dic['build_dir'] + '\\'

        # set target only if defined, otherwise use from template/default one

        mcu_def_dic = expanded_dic['target'].get_tool_configuration('uvision')
        if mcu_def_dic is None:
            return None
            # self.normalize_mcu_def(mcu_def_dic)
        self._normalize_mcu_def(mcu_def_dic)
        logging.debug("Mcu definitions: %s" % mcu_def_dic)
        self.append_mcu_def(expanded_dic, mcu_def_dic)
            # self.append_mcu_def(expanded_dic, mcu_def_dic)
        # load debugger
        driver = self.definitions.debuggers[expanded_dic['debugger']]['TargetDlls']['Driver']
        expanded_dic['uvision_settings']['TargetDlls']['Driver'] = driver
        # optimization set to correct value, default not used
        expanded_dic['uvision_settings']['Cads']['Optim'][0] = 1

        # Project file
        self.gen_file_jinja(
            'uvision4.uvproj.tmpl', expanded_dic, '%s.uvproj' % self.workspace['name'], expanded_dic['output_dir']['path'])
        self.gen_file_jinja(
            'uvision4.uvopt.tmpl', expanded_dic, '%s.uvopt' % self.workspace['name'], expanded_dic['output_dir']['path'])
        return 0

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['uvproj']]}

    def supports_target(self, target):
        return target in self.definitions.mcu_def

    def build_project(self):
        # > UV4 -b [project_path]
        path = join(self.workspace['output_dir']['path'],self.workspace['name'])
        if path.split('.')[-1] != 'uvproj':
            path = path + '.uvproj'
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

    def get_mcu_definition(self, project_file):
        """ Parse project file to get target definition """
        project_file = join(getcwd(), project_file)
        uvproj_dic = xmltodict.parse(file(project_file), dict_constructor=dict)
        # Generic Target, should get from Target class !
        mcu = Targets().get_mcu_definition()

        mcu['tool_specific'] = {
            # legacy device
            'uvision' : {
                'TargetOption' : {
                    'Device' : [uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Device']],
                    'Vendor' : [uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Vendor']],
                    'Cpu' : [uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Cpu']],
                    'FlashDriverDll' : [uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['FlashDriverDll']],
                    'DeviceId' : [int(uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['DeviceId'])],
                    'SFDFile' : [uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['SFDFile']],
                }
            }
        }
        return mcu
