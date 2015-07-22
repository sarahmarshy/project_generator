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


import logging

from collections import defaultdict
from .tool import ToolsSupported
from .util import *
from .settings import *

class Project:

    """represents a project, which can be formed of many yaml files"""
    def __init__(self, projects_file='projects.yaml', name = ''):
        if type(projects_file) is not dict:
            try:
                with open(projects_file, 'rt') as f:
                    self.projects_dict = yaml.load(f)
            except IOError:
               raise IOError("The main pgen projects file %s doesn't exist." % projects_file)
        else:
            self.projects_dict = projects_file

        self.settings = ProjectSettings()
        if 'settings' in self.projects_dict:
            self.settings.update(self.projects_dict['settings'])

        self.name = name
        project_dicts = {}
        if 'projects' in self.projects_dict:
            if len(self.projects_dict['projects'].keys()) > 1:
                if name == '':
                    raise RuntimeError("You must specify a project name when using a multi-project yaml file.")
                elif name not in self.projects_dict['projects'].keys():
                    raise RuntimeError("You specified an invalid project name.")
                else:
                    records = self.projects_dict['projects'][name]
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
            else:
                for name, records in self.projects_dict['projects'].items():
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
        else:
            logging.debug("No projects found in the main record file.")

        self.tool_specific = defaultdict(ToolSpecificSettings)
        self.tools = ToolsSupported()
        self.source_groups = {}
        self.project = {}
        self._fill_project_defaults()
        # process all projects dictionaries
        for project in project_dicts:
            self._set_project_attributes(project)
        self.generated_files = {}

    def _fill_project_defaults(self):

        self.project = {
            'name': self.name,          # project name
            'core': '',                 # core
            'linker_file': None,        # linker command file
            'build_dir' : 'build',      # Build output path
            'debugger' : 'cmsis-dap',   # Debugger
            'includes': [],             # include paths
            'copy_sources': False,      # [internal] Copy sources to destination flag
            'include_files': [],        # [internal] files to be included
            'source_paths': [],         # [internal] source paths
            'source_files_c': [],       # [internal] c source files
            'source_files_cpp': [],     # [internal] c++ source files
            'source_files_s': [],       # [internal] assembly source files
            'source_files_obj': [{}],   # [internal] object files
            'source_files_lib': [{}],   # [internal] libraries
            'macros': [],               # macros (defines)
            'misc': {},                 # misc tools settings, which are parsed by tool
            'output_dir': {             # [internal] The generated path dict
                'path': '',             # path with all name mangling we add to export_dir
                'rel_path': '',         # how far we are from root
                'rel_count': '',        # Contains count of how far we are from root, used for eclipse for example
            },
            'target': '',       # target
            'template' : '',    # tool template
            'output_type': 'exe',           # output type, default - exe
            'tools_supported': [self.settings.DEFAULT_TOOL], # Tools which are supported

        }

    def _set_project_attributes(self,project_file_data):
        if 'common' in project_file_data:
            if 'output' in project_file_data['common']:
                if project_file_data['common']['output'][0] not in ['lib','exe']:
                    raise RuntimeError("Invalid Output Type.")

                self.project['output_type'] = project_file_data['common']['output'][0]

            if 'includes' in project_file_data['common']:
                self._process_include_files(project_file_data['common']['includes'])

            if 'sources' in project_file_data['common']:
                if type(project_file_data['common']['sources']) == type(dict()):
                    for group_name, sources in project_file_data['common']['sources'].items():
                        self._process_source_files(sources, group_name)
                else:
                    self._process_source_files(project_file_data['common']['sources'], 'default')
                for source_path in self.project['source_paths']:
                    if os.path.normpath(source_path) not in self.project['includes']:
                        self.project['includes'].extend([source_path])

            if 'macros' in project_file_data['common']:
                self.project['macros'].extend(
                    [x for x in project_file_data['common']['macros'] if x is not None])

            if 'export_dir' in project_file_data['common']:
                self.project['export_dir'] = os.path.normpath(project_file_data['common']['export_dir'][0])

            for key in ['debugger','build_dir','mcu','name','target','core', 'linker_file']:
                if key in project_file_data['common']:
                    self.project[key] = project_file_data['common'][key][0]

            if 'tools_supported' in project_file_data['common']:
                self.project['tools_supported'] = []
                self.project['tools_supported'].extend(
                    [x for x in project_file_data['common']['tools_supported'] if x is not None])

        if 'tool_specific' in project_file_data:
            group_name = 'default'
            for tool_name, tool_settings in project_file_data['tool_specific'].items():
                self.tool_specific[tool_name].add_settings(tool_settings, group_name)

    def _process_include_files(self, files):
        # If it's dic add it , if file, add it to files
        for include_file in files:
            # include might be set to None - empty yaml list
            if include_file:
                if os.path.isfile(include_file):
                    # file, add it to the list (for copying or if tool requires it)
                    if not include_file in self.project['include_files']:
                        self.project['include_files'].append(os.path.normpath(include_file))
                    dir_path = os.path.dirname(include_file)
                else:
                    # its a directory
                    dir_path = include_file
                if not os.path.normpath(dir_path) in self.project['includes']:
                    self.project['includes'].append(os.path.normpath(dir_path))

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
            if os.path.isdir(source_file):
                self.project['source_paths'].append(os.path.normpath(source_file))
                self._process_source_files([os.path.join(os.path.normpath(source_file), f) for f in os.listdir(
                    source_file) if os.path.isfile(os.path.join(os.path.normpath(source_file), f))], group_name)

            extension = source_file.split('.')[-1]
            extension = mappings[extension] or extension

            if extension not in extensions:
                continue

            if extension not in self.source_groups[group_name]:
                self.source_groups[group_name][extension] = []

            self.source_groups[group_name][extension].append(os.path.normpath(source_file))

            if not os.path.dirname(source_file) in self.project['source_paths']:
                self.project['source_paths'].append(os.path.normpath(os.path.dirname(source_file)))

    def export(self, tool, copy):
        """ Exports a project """
        tools = []
        if not tool:
            tools = self.project['tools_supported']
        else:
            tools = [tool]

        generated_files = {}
        for export_tool in tools:
            exporter = ToolsSupported().get_value(export_tool, 'exporter')

            self.customize_project_for_tool(export_tool)
            if copy:
                self.copy_sources_to_generated_destination()

            files = exporter(self.project, self.settings).export_project()
            generated_files[export_tool] = files
        self.generated_files = generated_files

    def build(self, tool):
        """build the project"""
        tools = []
        if not tool:
            tools = self.project['tools_supported']
        else:
            tools = [tool]

        for build_tool in tools:
            builder = self.tools.get_value(build_tool, 'builder')
            logging.debug("Building for tool: %s", build_tool)
            logging.debug(self.generated_files)
            builder(self.generated_files[build_tool], self.settings).build_project()

    def get_generated_project_files(self, tool):
        # returns list of project files which were generated
        exporter = ToolsSupported().get_value(tool, 'exporter')
        return exporter(self.generated_files[tool], self.settings).get_generated_project_files()

    def copy_sources_to_generated_destination(self):
        self.project['copy_sources'] = True
        self.copy_files()

    @staticmethod
    def _generate_output_dir(path):
        """this is a separate function, so that it can be more easily tested."""

        count = path.count(os.sep) + 1

        return (os.sep.join('..' for _ in range(count)) + os.sep), count

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

    def format_source_files(self, ext, tool_specific_settings, toolchain_specific_settings):
        return [merge_recursive(self.source_of_type(ext), {k: v for settings in
                [settings.source_of_type(ext) for settings in tool_specific_settings] for
                k, v in settings.items()},toolchain_specific_settings.source_of_type(ext))]

    def customize_project_for_tool(self, tool):
        toolchain_specific_settings =  self.tool_specific[self.tools.get_value(tool, 'toolchain')]
        tool_specific_settings = []
        toolnames = self.tools.get_value(tool, 'toolnames')
        for tool_spec in toolnames:
            if self.tools.get_value(tool, 'toolchain') != tool_spec:
                tool_specific_settings.append(self.tool_specific[tool_spec])

        self.project['includes'] =  self.project['includes'] + list(flatten([settings.includes for settings in tool_specific_settings]))
        self.project['include_files'] =  self.project['include_files'] + list(flatten([settings.include_files for settings in tool_specific_settings]))
        self.project['source_paths'] =  self.project['source_paths'] + list(flatten([settings.includes for settings in tool_specific_settings]))
        self.project['source_files'] = merge_recursive(self.source_groups,
                                {k: v for settings in tool_specific_settings for k, v in settings.source_groups.items()},
                                toolchain_specific_settings.source_groups)
        for ext in ["c","cpp","s","lib"]:
           key = "source_files_"+ext
           self.project[key] = self.format_source_files(ext, tool_specific_settings, toolchain_specific_settings)

        self.project['source_files_obj']= merge_recursive(self.format_source_files('obj',tool_specific_settings, toolchain_specific_settings),
            self.format_source_files('o',tool_specific_settings, toolchain_specific_settings))

        self.project['linker_file'] =  self.project['linker_file'] or toolchain_specific_settings.linker_file or [
            tool_settings.linker_file for tool_settings in tool_specific_settings if tool_settings.linker_file]

        self.project['macros'] = self.project['macros'] + list(flatten([settings.macros for settings in tool_specific_settings])) \
            + toolchain_specific_settings.macros

        self.project['misc'] =  [merge_recursive({k: v for settings in tool_specific_settings for k, v in settings.misc.items()},
            toolchain_specific_settings.misc)]

        self.project['template'] = toolchain_specific_settings.template or [
                tool_settings.template for tool_settings in tool_specific_settings if tool_settings.template]

        self._set_output_dir_path(tool, '')
        if len(self.project['linker_file']) == 0 and self.project['output_type'] == 'exe':
            raise RuntimeError("Executable - no linker command found.")

    def _set_output_dir_path(self, tool, workspace_path = None):
        if self.settings.export_location_format != self.settings.DEFAULT_EXPORT_LOCATION_FORMAT:
            location_format = self.settings.export_location_format
        else:
            if 'export_dir' in self.project:
                location_format = self.project['export_dir']
            else:
                location_format = self.settings.export_location_format

        # substitute all of the different dynamic values
        location = PartialFormatter().format(location_format, **{
            'project_name': self.name,
            'tool': tool,
            'target': self.project['target']
        })
        # TODO (matthewelse): make this return a value directly
        self.project['output_dir']['path'] = os.path.normpath(location)
        path = self.project['output_dir']['path']
        self.project['output_dir']['rel_path'], self.project['output_dir']['rel_count'] = self._generate_output_dir(path)

    def _copy_files(self, file, output_dir, valid_files_group):
        file = os.path.normpath(file)
        dest_dir = os.path.join(os.getcwd(), output_dir, os.path.dirname(file))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        if file.split('.')[-1] in valid_files_group:
            shutil.copy2(os.path.join(os.getcwd(), file), os.path.join(os.getcwd(), output_dir, file))

    def copy_files(self):
        """" Copies all project files to specified directory - generated dir"""
        for path in self.project['includes']:
            if os.path.isdir(path):
                # directory full of include files
                path = os.path.normpath(path)
                files = os.listdir(path)
            else:
                # includes is a file, make it valid
                files = [os.path.basename(path)]
                path = os.path.dirname(path)
            dest_dir = os.path.join(os.getcwd(), self.project['output_dir']['path'], path)
            if not os.path.exists(dest_dir) and len(files):
                os.makedirs(dest_dir)
            for filename in files:
                if filename.split('.')[-1] in FILES_EXTENSIONS['includes']:
                    shutil.copy2(os.path.join(os.getcwd(), path, filename),
                                 os.path.join(os.getcwd(), self.project['output_dir']['path'], path))

        # all sources are grouped, therefore treat them as dict
        for k, v in self.project['source_files_c'][0].items():
            for file in v:
                self._copy_files(file, self.project['output_dir']['path'], FILES_EXTENSIONS['source_files_c'])

        for k, v in self.project['source_files_cpp'][0].items():
            for file in v:
                self._copy_files(file, self.project['output_dir']['path'], FILES_EXTENSIONS['source_files_cpp'])

        for k, v in self.project['source_files_s'][0].items():
            for file in v:
                self._copy_files(file, self.project['output_dir']['path'], FILES_EXTENSIONS['source_files_s'])

        for k,v in self.project['source_files_obj'][0].items():
            for file in v:
                self._copy_files(file, self.project['output_dir']['path'], FILES_EXTENSIONS['source_files_obj'])

        for k,v in self.project['source_files_lib'][0].items():
            for file in v:
                self._copy_files(file, self.project['output_dir']['path'], FILES_EXTENSIONS['source_files_lib'])

        linker = os.path.normpath(self.project['linker_file'])
        dest_dir = os.path.join(os.getcwd(), self.project['output_dir']['path'], os.path.dirname(linker))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy2(os.path.join(os.getcwd(), linker),
                     os.path.join(os.getcwd(), self.project['output_dir']['path'], linker))
