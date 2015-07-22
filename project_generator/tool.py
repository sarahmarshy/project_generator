# Copyright 2014 0xc0170
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
import subprocess
import yaml

from .targets import Targets
from .tools.iar import IAREmbeddedWorkbench
from .tools.uvision import Uvision
from .tools.coide import Coide
from .tools.eclipse import EclipseGnuARM
from .tools.gccarm import MakefileGccArm
from .tools.sublimetext import SublimeTextMakeGccARM
from .tools.gdb import GDB
from .tools.gdb import ARMNoneEABIGDB



class ToolsSupported:
    """ Represents all tools available """

    # Tools dictionary, defines toolchain and all tools used
    TOOLS = {
        'iar_arm': {
            'toolchain': 'iar',
            'toolnames': ['iar_arm'],
            'exporter': IAREmbeddedWorkbench,
            'builder': IAREmbeddedWorkbench,
            'flasher': IAREmbeddedWorkbench,
        },
        'uvision': {
            'toolchain': 'uvision',
            'toolnames': ['uvision'],
            'exporter': Uvision,
            'builder': Uvision,
            'flasher': Uvision,
        },
        'coide': {
            'toolchain': 'gcc_arm',
            'toolnames': ['coide'],
            'exporter': Coide,
            'builder': None,
            'flasher': None,
        },
        'make_gcc_arm': {
            'toolchain': 'gcc_arm',
            'toolnames': ['make_gcc_arm'],
            'exporter': MakefileGccArm,
            'builder': MakefileGccArm,
            'flasher': None,
        },
        'eclipse_make_gcc_arm': {
            'toolchain': 'gcc_arm',
            'toolnames': ['eclipse_make_gcc_arm', 'make_gcc_arm'],
            'exporter': EclipseGnuARM,
            'builder': None,
            'flasher': None,
        },
        'sublime_make_gcc_arm': {
            'toolchain': 'gcc_arm',
            'toolnames': ['sublime_make_gcc_arm', 'make_gcc_arm', 'sublime'],
            'exporter': SublimeTextMakeGccARM,
            'builder': MakefileGccArm,
            'flasher': None,
        },
        'sublime': {
            'toolchain': None,
            'toolnames': ['sublime'],
            'exporter': None,
            'builder': None,
            'flasher': None,
        },
        'gdb': {
            'toolchain': None,
            'toolnames': ['gdb'],
            'exporter': GDB,
            'builder': None,
            'flasher': None,
        },
        'arm_none_eabi_gdb': {
            'toolchain': None,
            'toolnames': ['gdb'],
            'exporter': ARMNoneEABIGDB,
            'builder': None,
            'flasher': None,
        },
    }

    TOOLCHAINS = list(set([v['toolchain'] for k, v in TOOLS.items() if v['toolchain'] is not None]))
    EXPORTERS = list(set([v['exporter'] for k, v in TOOLS.items() if v['exporter'] is not None]))
    BUILDERS = list(set([v['builder'] for k, v in TOOLS.items() if v['builder'] is not None]))
    FLASHERS = list(set([v['flasher'] for k, v in TOOLS.items() if v['flasher'] is not None]))

    def get_value(self, tool, key):
        try:
            value = self.TOOLS[tool][key]
        except (KeyError, TypeError):
            raise RuntimeError("%s does not support specified tool: %s" % (key, tool))
        return value

    def get_supported(self):
        return self.TOOLS.keys()

def mcu_create(ToolParser, mcu_name, proj_file):
    data = ToolParser(None, None).get_mcu_template(proj_file)
    data['mcu']['name'] = [mcu_name]
    # we got target, now damp it to root using target.yaml file
    # we can make it better, and ask for definitions repo clone, and add it
    # there, at least to MCU folder
    with open(os.path.join(os.getcwd(), mcu_name + '.yaml'), 'wt') as f:
        f.write(yaml.safe_dump(data, default_flow_style=False, width=200))

