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
import yaml
import shutil

from unittest import TestCase

from project_generator.project import Project
from project_generator.settings import ProjectSettings
from project_generator.tools.sublimetext import SublimeTextMakeGccARM

project_1_yaml = {
    'common': {
        'sources': ['sources/main.cpp'],
        'includes': ['includes/header1.h'],
        'target': ['mbed-lpc1768'],
        'linker_file': ['linker_script'],
    }
}

projects_1_yaml = {
    'projects': {
        'project_1' : ['test_workspace/project_1.yaml']
    },
}

class TestProject(TestCase):

    """test things related to the sublimetext tool"""

    def setUp(self):
        if not os.path.exists('test_workspace'):
            os.makedirs('test_workspace')
        # write project file
        with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1_yaml, default_flow_style=False))
        # write projects file
        with open(os.path.join(os.getcwd(), 'test_workspace/projects.yaml'), 'wt') as f:
            f.write(yaml.dump(projects_1_yaml, default_flow_style=False))
        self.project = Project(projects_1_yaml,'project_1')

        self.sublimetext = SublimeTextMakeGccARM(self.project.project, ProjectSettings())

    def tearDown(self):
        # remove created directory
        shutil.rmtree('test_workspace', ignore_errors=True)
        shutil.rmtree('generated_projects', ignore_errors=True)

    def test_export_project(self):
        self.project.export('sublime_make_gcc_arm', False)
       # it should get generated files from the last export
        projectfiles = self.project.get_generated_project_files('sublime_make_gcc_arm')
        assert projectfiles
        assert os.path.splitext(projectfiles['files'][0])[1] == '.sublime-project'
