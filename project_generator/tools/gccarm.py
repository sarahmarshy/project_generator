# Copyright 2014-2015 0xc0170
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

import copy
import os
from .builder import Builder
from .exporter import Exporter
from ..targets import Targets
import logging
import ntpath
import shutil
from ..util import SOURCE_KEYS
from itertools import chain
from operator import add


class MakefileGccArm(Exporter):

    # http://www.gnu.org/software/make/manual/html_node/Running.html
    ERRORLEVEL = {
        0: 'no errors',
        1: 'targets not already up to date',
        2: 'errors'
    }

    SUCCESSVALUE = 0
    WARNVALUE = 1

    optimization_options = ['O0', 'O1', 'O2', 'O3', 'Os']

    generated_projects = {
        'path': '',
        'files': {
            'makefile' : '',
        }
    }

    def __init__(self, workspace, env_settings):
        self.workspace = workspace
        self.env_settings = env_settings

    @staticmethod
    def get_toolnames():
        return ['make_gcc_arm']

    @staticmethod
    def get_toolchain():
        return 'make_gcc_arm'

    def _parse_specific_options(self, data):
        """ Parse all uvision specific setttings. """
        data['compiler_options'] = []
        data['linker_options'] = []
        for k, v in data['misc'].items():
            if type(v) is list:
                if k not in data:
                    data[k] = []
                data[k].extend(v)
            else:
                if k not in data:
                    data[k] = ''
                data[k] = v

    def _get_libs(self, data):
        data['lib_paths'] =[]
        data['libraries'] =[]
        for lib in data['source_files_a']:
            head, tail = ntpath.split(lib)
            file = tail
            if (os.path.splitext(file)[1] != ".a"):
                continue
            else:
                file = file.replace(".a","")
                data['lib_paths'].append(head)
                data['libraries'].append(file.replace("lib",''))

    def _process_mcu(self, data):
        for k,v in data['mcu'].items():
            data[k] = v

    def generate_project(self):
        """ Processes misc options specific for GCC ARM, and run generator. """
        generated_projects = copy.deepcopy(self.generated_projects)
        self.process_data_for_makefile(self.workspace)
        self.gen_file_jinja('makefile_gcc.tmpl', self.workspace, 'Makefile', self.workspace['output_dir']['path'])
        return 0

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['makefile']]}

    def process_data_for_makefile(self, data):
        #Flatten our dictionary, we don't need groups
        data['source_paths'] = []
        for key in SOURCE_KEYS:
            data[key] = list(chain(*data[key].values()))
            data['source_paths'].extend([ntpath.split(path)[0] for path in data[key]])
        data['source_paths'] = set(data['source_paths'])

        self._get_libs(data)

        self._parse_specific_options(data)
        if 'instruction_mode' not in data:
            data['instruction_mode']= 'thumb'
        self._process_mcu(data)
        data['toolchain'] = 'arm-none-eabi-'
        data['toolchain_bin_path'] = self.env_settings.get_env_settings('gcc')

        target = Targets(self.env_settings.get_env_settings('definitions'))

        data['core'] = data['target'].core.lower()
        # gcc arm is funny about cortex-m4f.
        # gcc arm is funny about cortex-m4f.
        if data['core'] == 'cortex-m4f':
            data['core'] = 'cortex-m4'

        # change cortex-m0+ to cortex-m0plus
        if data['core'] == 'cortex-m0+':
            data['core'] = 'cortex-m0plus'

        # set default values
        if 'optimization_level' not in data:
            data['optimization_level'] = self.optimization_options[0]

    def build_project(self):
        # cwd: relpath(join(project_path, ("gcc_arm" + project)))
        # > make all
        path = self.workspace['output_dir']['path']
        os.chdir(path)
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("bin"):
            shutil.rmtree("bin")

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            args = ['make', 'all']
        else:
            args =['make','-s','all']

        ret = Builder.build_command(args, self, "GCC", path.split(os.path.sep)[-1])
        return ret
