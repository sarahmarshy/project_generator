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

from os.path import join, normpath, splitext, isfile, exists
from os import listdir, makedirs, getcwd

from .settings import ProjectSettings
import logging
class Target:
    def __init__(self, name, tools, config):
        self.name = name
        self.supported_tools = tools
        self.config = config
        self.core = self.config['mcu']['core']

    def get_tool_configuration(self, tool):
        if not(tool in self.supported_tools):
            raise RuntimeError("Target %s does not support %s." % (self.name,tool))
        return self.config['tool_specific'][tool]

