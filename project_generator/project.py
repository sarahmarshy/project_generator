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


from .tool import ToolsSupported
from .util import *
from .settings import *
import re
from .targets import Targets
import os
from os.path import *

class Project:

    """represents a project, which can be formed of many yaml files"""
    def __init__(self, project_dicts, settings_dict, name, ignore):
        self.settings = ProjectSettings()
        if 'settings' in settings_dict:
            self.settings.update(settings_dict['settings'])

        self.name = name
        self.project = {}
        self.project_dicts = project_dicts
        self.tool = ''
        self.ignore_dirs = ignore
        self._fill_project_defaults()
        self.root = os.getcwd()

    def for_tool(self, tool = "default"):
        if tool != "default":
            # will resolve any alias user writes in command line. IE iar => iar_arm
            self.tool = self._resolve_tool(tool)
            if self.tool is None:
                return None
        self._fill_project_defaults()  # default dictionary needed for project

        self.supported = []  # tools that project's yaml files define
        for dict in self.project_dicts:  # iterates over the dictionaries defined in yaml file
            self._set_project_attributes(dict, "common")  # self.project dict values according to yaml common section

             # _find_tool_settings yields valid tools defined in yaml
            self.supported = reduce(lambda x,y:x+y,
                                    [self._find_supported_tools(t) for t in self._find_tool_settings(dict)])

        #if tool is default, we are just extracting yaml information to see what tools are possible
        if self.tool not in self.supported and tool != "default":
            logging.error("The tool name \"%s\" is not supported in yaml!"%self.tool, exc_info = False)
            return None

        self._set_output_dir_path()  # determines where generated projects will go
        # ignore any path that has the output directory in it
        logging.debug("Ignoring the following directories: %s"%", ".join(self.ignore_dirs))

        self._fix_includes_and_sources()

        if self.project['linker_file'] is None and tool!="default":
            logging.critical("No linker file found")
            return None

        return 1

    def _fill_project_defaults(self):

        self.project = {
            'name': self.name,          # project name
            'linker_file': None,        # linker command file
            'build_dir' : 'build',      # Build output path
            'debugger' : 'cmsis-dap',   # Debugger
            'includes': [],             # include paths
            'copy_sources': False,      # [internal] Copy sources to destination flag
            'sources': [],              # [internal]
            'source_files_c': {},       # c source files
            'source_files_cpp': {},     # c++ source files
            'source_files_s': {},       # assembly source files
            'source_files_obj': {},     # object files
            'source_files_a': {},       #  libraries
            'macros': [],               # macros (defines)
            'mcu'   : {},
            'fpu'   : None,
            'misc': {},                 # misc tools settings, which are parsed by tool
            'output_dir': {             # [internal] The generated path dict
                'path': '',             # path with all name mangling we add to export_dir
                'rel_path': ''         # how far we are from root
            },
            'target': '',       # target
            'template' : '',    # tool template
            'output_type': 'exe',           # output type, default - exe

        }

    def _find_supported_tools(self, toolchain):
        # Iterate over all possible pgen tools, return only the ones where the toolchain is a valid toolname
        supported = ToolsSupported()
        return filter(lambda t:toolchain in supported.get_toolnames(t),supported.get_supported())

    def _resolve_toolchain(self, tool):
        return ToolsSupported().get_toolchain(tool)

    def _find_tool_settings(self, project_file_data):
        """"Looks in yaml file for tool_specific settings"""
        toolchain = self._resolve_toolchain(self.tool)
        if 'tool_specific' in project_file_data:
            for tool, settings in project_file_data['tool_specific'].items():
                # Iterates over tool specific info in yaml. Will set corresponding self.project values
                if tool == self.tool or tool == toolchain:
                    self._set_project_attributes(project_file_data['tool_specific'],tool)
                    if tool != toolchain:
                        # Example case. Tool = Sublime, but yaml defines info for GCC
                        # Pgen should pick up the yaml settings for GCC
                        self._set_project_attributes(project_file_data['tool_specific'],toolchain)

                if 'linker_file' in settings and self.project['output_type'] == 'exe':
                    """ Yield this valid tool so we can determine what tools the project can be
                        succesfully generated for """
                    yield tool
                else:
                    # Output library, linker file not needed
                    yield tool

    def _set_project_attributes(self,project_file_data, section):
        """Set attributes in self.project according to dict and section(key) of that dict"""
        if section in project_file_data:  # make sure the key is valid
             for attribute, data in project_file_data[section].items():  # attribute => key, data => value
                 if attribute in self.project.keys():  # Is this also a key is self.project?
                     if type(self.project[attribute]) is list:
                         if type(data) is list:
                             logging.debug("Setting %s to %s"%(attribute,", ".join(data)))
                             self.project[attribute].extend(data)
                         else:
                            logging.debug("Setting %s to %s"%(attribute,data))
                            self.project[attribute].append(data)
                     else:
                         logging.debug("Setting %s to %s"%(attribute,data[0]))
                         self.project[attribute] = data[0]  # self.project attribute is a string, only room for 1 value

    def _fix_includes_and_sources(self):
        includes = self.project['includes']
        source_files = self.project['sources']

        self.project['includes'] = []
        self.project['sources'] = []

        self._process_include_files(includes)
        for files in source_files:
            """
            Check if user used a group name when defining sources
            Sources:
                group_name:
                    - source_file1
                    - source_file2
                - source_file_no_group
            """
            if type(files) == dict:
                for group_name, sources in files.items():
                    self._process_source_files(sources, group_name)
            else:
                self._process_source_files(source_files, 'default') # no group defined, put it in the default group

    def _process_include_files(self, files):
        # If it's dic add it , if file, add it to files
        for include_file in files:
            # include might be set to None - empty yaml list
            if include_file:
                if isfile(include_file):
                    # file, add it to the list (for copying or if tool requires it)
                    dir_path = dirname(include_file)
                else:
                    # its a directory
                    dir_path = include_file
                if not dir_path in self.project['includes']:
                    self.project['includes'].append(dir_path)

    def _process_source_files(self, files, group_name):
        """Sorts source files into groups in the form of source_groups[group_name][extension]
            extensions will be mapped to 5 main types 'cpp', 'c', 's', 'obj', 'a'"""
        ignore = lambda f: not(any(re.match(ignore,f) for ignore in self.ignore_dirs))
        for source_file in filter(ignore,files):
            if isdir(source_file):
                self._process_source_files([join(normpath(source_file), f) for f in os.listdir(
                    source_file) if isfile(join(normpath(source_file), f))], group_name)

            extension = source_file.split('.')[-1]
            if extension not in VALID_EXTENSIONS:
                continue
            source_group = FILE_MAP[extension]

            if group_name not in self.project[source_group]:
                self.project[source_group][group_name] = []

            self.project[source_group][group_name].append(normpath(source_file))

    def _fix_paths(self):
        norm_func = lambda path : normpath(join(self.project['output_dir']['rel_path'],path))
        for key in FILES_EXTENSIONS.keys():
            if type(self.project[key]) is dict:
                for k,v in self.project[key].items():
                    self.project[key][k] = map(norm_func,v)
            elif type(self.project[key]) is list:
                self.project[key] = map(norm_func,self.project[key])
            else:
                self.project[key] = norm_func(self.project[key])

    def _resolve_tool(self, alias):
        """will resolve any alias user writes in command line. IE iar => iar_arm"""
        tool = ToolsSupported().resolve_alias(alias)
        if tool is None:
            options = ToolsSupported().get_supported() + ToolsSupported().TOOLS_ALIAS.keys()
            options.sort()
            logging.error("The tool name \"%s\" is not valid! \nChoose from: \n%s"% (alias, ", ".join(options)),exc_info= False)
            return None
        else:
            logging.debug("%s resolved to %s"%(alias,tool))
            return tool

    def _try_open_file(self, filename):
        if(exists(filename)):
            with open(filename, 'rt') as f:
                logging.info("Settings captured from %s."%filename)
                return yaml.load(f)
        else:
            logging.critical("The file %s doesn't exist." % filename)
            return None

    def generate(self, copy, tool, target_settings=None, tool_settings=None):
        """ Exports a project """
        target_settings = join(os.getcwd(),target_settings) if target_settings is not None else None
        tool_settings = join(os.getcwd(),tool_settings) if tool_settings is not None else None
        os.chdir(self.settings.project_root)
        if self.for_tool(tool) is None:
            return None
        #Targets object
        targets = Targets(self.settings.get_env_settings('definitions'))
        #Targets keeps a list of available targets in definitions directory
        #We get the target object with the project's target name
        self.project['target'] = targets.get_target(self.project['target'])

        if target_settings is not None:
            target_settings = self._try_open_file(target_settings)
            if target_settings is None:
                return None
            self.project['macros'] = target_settings['macros']
        if tool_settings is not None:
            tool_settings = self._try_open_file(tool_settings)
            if tool_settings is None:
                return None
            self.project['misc'] = tool_settings

        if self.project['target'].fpu:
            self.project['fpu'] = self.project['target'].fpu_convention

        exporter = ToolsSupported().get_tool(self.tool)
        # None is an error
        if exporter is None:
            return None
        if copy:
            self.project['copy_sources'] = True
            logging.info("Copying sources to output directory.")
            self.copy_files()
        self._fix_paths()
        if self.project['target'] is None:
            return None

        logging.info("Project %s being generated for %s."%(self.project['name'],self.tool))
        result = exporter(self.project, self.settings).generate_project()
        return result

    def build(self, tool):
        """build the project"""
        os.chdir(self.settings.project_root)
        if self.for_tool(tool) is None:
            return None
        build_tool = self.tool
        result = 0
        builder = ToolsSupported().get_tool(build_tool)
        # None is an error
        if builder is None:
            return None
        logging.info("Building for tool: %s", build_tool)
        result = builder(self.project, self.settings).build_project()
        return result

    def _generate_output_dir(self, path):
        """this is a separate function, so that it can be more easily tested."""
        rel_path = relpath(os.getcwd(),path)
        return rel_path+sep

    def _set_output_dir_path(self):
        location_format = self.settings.export_location_format

        try:
            target = self.project['target'].name
        except:
            target = self.project['target']
        # substitute all of the different dynamic values
        location = PartialFormatter().format(location_format, **{
            'project_name': self.name,
            'tool': self.tool,
            'target': target
        })

        self.project['output_dir']['path'] = normpath(location)
        path = self.project['output_dir']['path']
        self.project['output_dir']['rel_path'] = self._generate_output_dir(path)
        logging.debug("Output directory: %s"%self.project['output_dir']['rel_path']+self.project['output_dir']['path'])

    def copy_files(self):
        no_ignore = []
        for key in FILES_EXTENSIONS.keys():
            if type(self.project[key]) is dict:
                for k,v in self.project[key].items():
                    no_ignore.extend(v)
            elif type(self.project[key]) is list:
                no_ignore.extend(self.project[key])
            else:
                no_ignore.append(self.project[key])
        dst = join(self.project['output_dir']['path'],'copy')
        if exists(dst):
            shutil.rmtree(dst)
        src = relpath(os.getcwd())
        for item in filter(lambda x: x in no_ignore,os.listdir(src)):
            s = join(src,item)
            d = join(dst,item)
            if isdir(s):
                shutil.copytree(s,d)
            else:
                shutil.copy2(s,d)