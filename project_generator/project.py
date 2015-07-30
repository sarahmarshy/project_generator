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

from .tool import ToolsSupported
from .util import *
from .settings import *

class Project:

    """represents a project, which can be formed of many yaml files"""
    def __init__(self, project_dicts, settings_dict, name):
        self.settings = ProjectSettings()
        if 'settings' in settings_dict:
            self.settings.update(settings_dict['settings'])

        self.name = name
        self.source_groups = {}
        self.project = {}
        self.project_dicts = project_dicts
        self.tool = ''

    def for_tool(self, tool = "default"):
        if tool != "default":
            self.tool = self._resolve_tool(tool)
        self._fill_project_defaults()
        # process all projects dictionaries

        found = False
        self.supported = []
        for dict in self.project_dicts:
            self._set_project_attributes(dict, "common")
            for t in self._find_tool_settings(dict):
                for tools in self._find_supported_tools(t):
                    self.supported.extend(tools)

        if self.tool not in self.supported and tool != "default":
            raise RuntimeError("The tool name \"%s\" is not supported in yaml!"%self.tool)

        self._fix_includes_and_sources()
        self._set_output_dir_path(self.tool, '')

        if self.project['linker_file'] is None:
            raise RuntimeError("No linker file found")
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
            'sources': [],
            'source_paths': [], # [internal] source paths
            'source_files_c': {},       # [internal] c source files
            'source_files_cpp': {},     # [internal] c++ source files
            'source_files_s': {},       # [internal] assembly source files
            'source_files_obj': {},   # [internal] object files
            'source_files_lib': {},   # [internal] libraries
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

        }

    def _find_supported_tools(self, toolchain):
        for tool in ToolsSupported().get_supported():
            toolnames = ToolsSupported().get_toolnames(tool)
            if toolchain in toolnames:
                yield toolnames

    def _resolve_toolchain(self, tool):
        return ToolsSupported().get_toolchain(tool)

    def _find_tool_settings(self, project_file_data):
        toolchain = self._resolve_toolchain(self.tool)
        if 'tool_specific' in project_file_data:
            for tool, settings in project_file_data['tool_specific'].items():
                if tool == self.tool or tool == toolchain:
                    self._set_project_attributes(project_file_data['tool_specific'],tool)
                    if tool != toolchain:
                        self._set_project_attributes(project_file_data['tool_specific'],toolchain)
                if 'linker_file' in settings:
                    yield tool

    def _set_project_attributes(self,project_file_data, section):
         if section in project_file_data:
             for attribute, data in project_file_data[section].items():
                 if attribute in self.project.keys():
                     if type(self.project[attribute]) is list:
                         if type(data) is list:
                             self.project[attribute].extend(data)
                         else:
                            self.project[attribute].append(data)
                     else:
                         self.project[attribute] = data[0]

    def _fix_includes_and_sources(self):
        includes = self.project['includes']
        source_files = self.project['sources']

        self.project['includes'] = []
        self.project['sources'] = []

        self._process_include_files(includes)
        for files in source_files:
            if type(files) == dict:
                for group_name, sources in files.items():
                    self._process_source_files(sources, group_name)
            else:
                self._process_source_files(files, 'default')

        for group_name in self.source_groups.keys():
            for extension,files in self.source_groups[group_name].items():
                files = self.source_groups[group_name][extension]
                key = 'source_files_'+extension
                if key == 'source_files_a':
                    key = 'source_files_lib'
                if group_name in self.project[key]:
                    self.project[key][group_name].extend(files)
                else:
                     self.project[key][group_name] = files

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
        if group_name not in self.source_groups:
            self.source_groups[group_name] = {}
        for source_file in files:
            if os.path.isdir(source_file):
                self.project['source_paths'].append(os.path.normpath(source_file))
                self._process_source_files([os.path.join(os.path.normpath(source_file), f) for f in os.listdir(
                    source_file) if os.path.isfile(os.path.join(os.path.normpath(source_file), f))], group_name)

            extension = source_file.split('.')[-1]
            extension = FILE_MAP[extension] if extension in FILE_MAP else extension

            if extension not in MAIN_FILES:
                continue

            if extension not in self.source_groups[group_name]:
                self.source_groups[group_name][extension] = []

            self.source_groups[group_name][extension].append(os.path.normpath(source_file))

            if not os.path.dirname(source_file) in self.project['source_paths']:
                self.project['source_paths'].append(os.path.normpath(os.path.dirname(source_file)))

    def _resolve_tool(self, alias):
        tool = ToolsSupported().resolve_alias(alias)
        if tool is None:
            options = ToolsSupported().get_supported() + ToolsSupported().TOOLS_ALIAS.keys()
            options.sort()
            raise RuntimeError("The tool name \"%s\" is not valid! \nChoose from: \n%s"% (alias, ", ".join(options)))
        else:
            return tool

    def generate(self, copy):
        """ Exports a project """
        generated_files = {}
        result = 0
        exporter = ToolsSupported().get_tool(self.tool)

        # None is an error
        if exporter is None:
            result = -1
        if copy:
            self.project['copy_sources'] = True
            self.copy_files()

        files = exporter(self.project, self.settings).export_project()
        generated_files[self.tool] = files
        self.generated_files = generated_files
        return result

    def build(self, tool):
        """build the project"""
        tools = self._resolve_tools(tool)

        result = 0

        for build_tool in tools:
            builder = ToolsSupported().get_tool(build_tool)
            # None is an error
            if builder is None:
                result = -1
                continue

            logging.debug("Building for tool: %s", build_tool)
            logging.debug(self.generated_files)
            builder(self.generated_files[build_tool], self.settings).build_project()
            return result

    def get_generated_project_files(self, tool):
        # returns list of project files which were generated
        exporter = ToolsSupported().get_tool(tool)
        return exporter(self.generated_files[tool], self.settings).get_generated_project_files()

    @staticmethod
    def _generate_output_dir(path):
        """this is a separate function, so that it can be more easily tested."""
        relpath = os.path.relpath(os.getcwd(),path)
        count = relpath.count(os.sep) + 1

        return relpath+os.path.sep, count

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

        # I'm hoping that having the workspace variable will remove the need for workspace_path

        # TODO (matthewelse): make this return a value directly
        self.project['output_dir']['path'] = os.path.normpath(location)
        path = self.project['output_dir']['path']
        self.project['output_dir']['rel_path'], self.project['output_dir']['rel_count'] = self._generate_output_dir(path)

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
