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

"""
Settings needed:
UV4
IARBUILD
PROJECT_ROOT
GCC_BIN_PATH
"""

import os

from os.path import expanduser, normpath, join, pardir, sep


class ProjectSettings:
    PROJECT_ROOT = os.environ.get('PROJECT_GENERATOR_ROOT') or join(pardir, pardir)
    DEFAULT_TOOL = os.environ.get('PROJECT_GENERATOR_DEFAULT_TOOL') or 'uvision'

    DEFAULT_EXPORT_LOCATION_FORMAT = join('generated_projects', '{tool}_{project_name}')

    def __init__(self):
        """ This are default enviroment settings for build tools. To override,
        define them in the projects.yaml file. """
        self.paths = {}
        self.templates = {}
        self.paths['uvision'] = os.environ.get('UV4') or join('C:', sep,
            'Keil', 'UV4', 'UV4.exe')
        self.paths['iar'] = os.environ.get('IARBUILD') or join(
            'C:', sep, 'Program Files (x86)',
            'IAR Systems', 'Embedded Workbench 7.0',
            'common', 'bin')
        self.paths['gcc'] = os.environ.get('ARM_GCC_PATH') or ''
        self.paths['definitions_default'] = join(expanduser('~/.pg'), 'definitions')
        self.paths['definitions'] = self.paths['definitions_default']
        if not os.path.exists(join(expanduser('~/.pg'))):
            os.mkdir(join(expanduser('~/.pg')))

        self.export_location_format = self.DEFAULT_EXPORT_LOCATION_FORMAT

    def update(self, settings):
        if settings:
            if 'tools' in settings:
                for k, v in settings['tools'].items():
                    if k in self.paths:
                        if 'path' in v.keys():
                            self.paths[k] = v['path'][0]
                    if 'template' in v.keys():
                        self.templates[k] = v['template']

            if 'definitions_dir' in settings:
                self.paths['definitions'] = normpath(settings['definitions_dir'][0])

            if 'export_dir' in settings:
                self.export_location_format = normpath(settings['export_dir'][0])

    def update_definitions_dir(self, def_dir):
        self.paths['definitions'] = normpath(def_dir)

    def get_env_settings(self, env_set):
        return self.paths[env_set]

class ToolSpecificSettings:

    """represents the settings that are specific to targets"""

    def __init__(self):
        self.includes = []
        self.include_files = []
        self.source_paths = []
        self.source_groups = {}
        self.macros = []
        self.misc = {}

        self.linker_file = None
        self.template = None

    def add_settings(self, data_dictionary, group_name):
        if 'sources' in data_dictionary:
            self._process_source_files(
                data_dictionary['sources'], group_name)

        if 'includes' in data_dictionary:
            self._process_include_files(data_dictionary['includes'])

        if 'macros' in data_dictionary:
            self.macros.extend([x for x in data_dictionary['macros'] if x is not None])

        if 'export_dir' in data_dictionary:
            self.export_dir.update(data_dictionary['export_dir'])

        if 'linker_file' in data_dictionary:
            self.linker_file = data_dictionary['linker_file'][0]

        if 'misc' in data_dictionary:
            self.misc.update(data_dictionary['misc'])

        if 'template' in data_dictionary:
            self.template = data_dictionary['template']

    def source_of_type(self, filetype):
        """return a dictionary of groups and the sources of a specified type within them"""
        files = {}
        for group, group_contents in self.source_groups.items():
            files[group] = []
            if filetype in group_contents:
                files[group].extend(group_contents[filetype])

        return files

    def all_sources_of_type(self, filetype):
        """return a list of the sources of a specified type"""
        files = []

        for group, group_contents in self.source_groups.items():
            if filetype in group_contents:
                files.extend(group_contents[filetype])

        return files

    def _process_source_files(self, files, group_name):
        extensions = ['cpp', 'c', 's', 'obj', 'lib']
        mappings = defaultdict(lambda: None)

        mappings['o'] = 'obj'

        mappings['a'] = 'lib'
        mappings['ar'] = 'lib'
        mappings['cc'] = 'cpp'

        if group_name not in self.source_groups:
            self.source_groups[group_name] = {}

        for source_file in files:
            extension = source_file.split('.')[-1]
            extension = mappings[extension] or extension

            if extension not in extensions:
                continue

            if extension not in self.source_groups[group_name]:
                self.source_groups[group_name][extension] = []

            self.source_groups[group_name][extension].append(source_file)

            if os.path.dirname(source_file) not in self.source_paths:
                self.source_paths.append(os.path.dirname(source_file))

    # TODO 0xc0170: remove this and process source files - duplicate. Probably we should reconsider
    # this class
    def _process_include_files(self, files):
        # If it's dic add it , if file, add it to files
        for include_file in files:
            if os.path.isfile(include_file):
                if not include_file in self.include_files:
                    self.include_files.append(os.path.normpath(include_file))
            if not os.path.dirname(include_file) in self.includes:
                self.includes.append(os.path.normpath(include_file))
