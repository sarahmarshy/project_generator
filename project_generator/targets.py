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

import yaml
import subprocess

from os.path import join, splitext, exists
from os import listdir, makedirs, getcwd

from .settings import ProjectSettings
import logging

class Target:
    def __init__(self, name, tools, config):
        self.name = name
        self.supported_tools = tools
        self.config = config
        self.core = self.config['mcu']['core']
        self.fpu = self.core[-1] == 'f'

    def get_tool_configuration(self, tool):
        if not(tool in self.supported_tools):
            logging.critical("Target %s does not support %s." % (self.name,tool))
            return None
        return self.config['tool_specific'][tool]

class Targets:

    MCU_TEMPLATE = {
        'mcu' : {
            'vendor' : 'Manually add vendor (st, freescale, etc) instead of this text',
            'name' : '',
            'core' : '',
        },
        'tool_specific':{}
    }

    def __init__(self, directory=None):
        logging.debug("Target definitions captured from %s."%directory)
        if directory:
            self.definitions_directory = directory
            self.targets = [Target(splitext(f)[0],self._find_tools(f),self._load_record(f)) for f in listdir(directory)
                            if splitext(f)[1] == '.yaml' ]

    def _load_record(self, file):
        project_file = open(join(self.definitions_directory,file))
        config = yaml.load(project_file)
        project_file.close()
        return config

    def _find_tools(self,file):
        config = self._load_record(file)
        return config['tool_specific'].keys()

    def get_target(self, alias):
        targs = []
        for target in self.targets:
            if alias.lower() in target.name.lower():
                targs.append(target)
        if len(targs) == 1:
            return targs[0]
        elif len(targs) > 1:
            print("Multiple targets contain %s"%alias)
            for i, target in enumerate(targs):
                print(str(i) + ": " + target.name)
            answer = raw_input('\nWhich target do you want? ')
            while int(answer) not in range(0,len(targs)):
                answer = raw_input('Answer not in list. Which target do you want? ')
            return targs[int(answer)]
        targets = [target.name for target in self.targets]
        logging.critical("\n%s must be contained in one of these strings: \n%s" % (alias,"\n".join(targets)))
        return None

    def get_mcu_definition(self):
        return self.MCU_TEMPLATE

# This helps to create a new target. As target consists of mcu, this function
# parses the provided proj_file and creates a valid yaml file, which can be pushed
# to pgen definitions.
def mcu_create(ToolParser, mcu_name, proj_file, definitions = None):
    settings = ProjectSettings()
    if definitions is not None:
        settings.update_definitions_dir(definitions)
    def_dir = settings.get_env_settings('definitions')

    filename = join(def_dir, mcu_name + '.yaml')
    mcu = Targets().get_mcu_definition()
    if exists(filename):
        with open(filename, 'rt') as f:
                mcu = yaml.load(f)

    data = ToolParser(None, None).get_mcu_definition(proj_file,mcu)
    data['mcu']['name'] = mcu_name
    # we got target, now damp it to root using target.yaml file
    # we can make it better, and ask for definitions repo clone, and add it
    # there, at least to MCU folder
    with open(filename, 'wt') as f:
        f.write(yaml.safe_dump(data, default_flow_style=False, width=200))
    return 0
