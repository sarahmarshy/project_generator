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
import sys

class Target:
    def __init__(self, name, tools, config):
        self.name = name
        self.supported_tools = tools
        self.config = config
        self.core = self.config['mcu']['core']

    def get_tool_configuration(self, tool):
        if not(tool in self.supported_tools):
            logging.critical("Target %s does not support %s." % (self.name,tool))
            return None
        return self.config['tool_specific'][tool]


class Targets:

    MCU_TEMPLATE = {
        'mcu' : {
            'vendor' : ['Manually add vendor (st, freescale, etc) instead of this text'],
            'name' : [''],
            'core' : ['Manually add core (cortex-mX) instead of this text'],
        },
    }

    def __init__(self, directory=None):
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
        for target in self.targets:
            if alias.lower() in target.name.lower():
                return target
        targets = [target.name for target in self.targets]
        logging.critical("\n%s must be contained in one of these strings: \n%s" % (alias,"\n".join(targets)))
        return None

    def get_mcu_definition(self):
        return self.MCU_TEMPLATE

    def update_definitions(self, force=False, settings=ProjectSettings()):
        defdir_exists = True
        if not exists(settings.paths['definitions']):
            defdir_exists = False
            makedirs(settings.paths['definitions'])

        # For default, use up to date repo from github
        if settings.get_env_settings('definitions') == settings.get_env_settings('definitions_default'):
            if not defdir_exists:
                cmd = ('git', 'clone', '--quiet',
                       'https://github.com/project-generator/project_generator_definitions.git', '.')
                subprocess.call(cmd, cwd=settings.paths['definitions'])
            elif force:
                # rebase only if force, otherwise use the current version
                cmd = ('git', 'pull', '--rebase', '--quiet', 'origin', 'master')
                subprocess.call(cmd, cwd=settings.paths['definitions'])
            else:
                # check if we are on top of origin/master
                cmd = ('git', 'fetch', 'origin','master', '--quiet')
                subprocess.call(cmd, cwd=settings.paths['definitions'])
                cmd = ('git', 'diff', 'master', 'origin/master', '--quiet')
                p = subprocess.call(cmd, cwd=settings.paths['definitions'])
                # any output means we are behind the master, update
                if p:
                    logging.debug("Definitions are behind the origin/master, rebasing.")
                    cmd = ('git', 'pull', '--rebase', '--quiet', 'origin', 'master')
                    subprocess.call(cmd, cwd=settings.paths['definitions'])

# This helps to create a new target. As target consists of mcu, this function
# parses the provided proj_file and creates a valid yaml file, which can be pushed
# to pgen definitions.
def mcu_create(ToolParser, mcu_name, proj_file, tool):
    data = ToolParser(None, None).get_mcu_definition(proj_file)
    data['mcu']['name'] = [mcu_name]
    # we got target, now damp it to root using target.yaml file
    # we can make it better, and ask for definitions repo clone, and add it
    # there, at least to MCU folder
    with open(join(getcwd(), mcu_name + '.yaml'), 'wt') as f:
        f.write(yaml.safe_dump(data, default_flow_style=False, width=200))
    return 0
