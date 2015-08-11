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

from project_generator.generate import Generator
from project_generator.project import Project
from project_generator.settings import ProjectSettings
from project_generator.tools.uvision import uVisionDefinitions, Uvision

from test_tools.simple_project import project_1_yaml, projects_yaml

class TestProject(TestCase):

    """test things related to the uvision tool"""

    def setUp(self):
        if not os.path.exists('test_workspace'):
            os.makedirs('test_workspace')
        # write project file
        with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1_yaml, default_flow_style=False))
        # write projects file
        with open(os.path.join(os.getcwd(), 'test_workspace/projects.yaml'), 'wt') as f:
            f.write(yaml.dump(projects_yaml, default_flow_style=False))

        self.project = next(Generator(projects_yaml).generate('project_1'))

        self.defintions = uVisionDefinitions()
        self.uvision = Uvision(self.project.project, ProjectSettings())

    def tearDown(self):
        # remove created directory
        shutil.rmtree('test_workspace', ignore_errors=True)
        shutil.rmtree('generated_projects', ignore_errors=True)

    def test_export_project(self):
        result = self.project.generate(False, 'uvision')
        # it should get generated files from the last export
        projectfiles = self.project.get_generated_project_files()['uvision']
        assert result == 0
        assert projectfiles
        assert os.path.splitext(projectfiles['files']['uvproj'])[1] == '.uvproj'

    def test_export_project_to_diff_directory(self):
        projects_yaml['settings']['export_dir'] = ['create_this_folder']
        with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1_yaml, default_flow_style=False))
        for project in Generator(projects_yaml).generate('project_1'):
            result = project.generate(False,"uvision")

        assert result == 0
        assert os.path.isdir('create_this_folder')
        shutil.rmtree('create_this_folder')

    def test_build_project(self):
        result_export = self.project.generate(False, 'uvision')
        result_build = self.project.build('uvision')

        assert result_export == 0
        assert result_build == 0
