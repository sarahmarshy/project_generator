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
from project_generator.settings import ProjectSettings
from project_generator.tools.uvision import uVisionDefinitions, Uvision

from simple_project import project_1, projects_yaml, make_files, delete_files

class TestProject(TestCase):

    """test things related to the uvision tool"""

    def setUp(self):
        # write project file
        make_files()

        self.project = next(Generator(projects_yaml).generate('project_1'))

        self.defintions = uVisionDefinitions()
        self.uvision = Uvision(self.project.project, ProjectSettings())

    def tearDown(self):
        # remove created directory
        delete_files()

    def test_export_project(self):
        result = self.project.generate(False, 'uvision')
        # it should get generated files from the last export
        assert result == 0

    def test_export_project_to_diff_directory(self):
        projects_yaml['settings']['export_dir'] = ['create_this_folder']
        with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1, default_flow_style=False))
        for project in Generator(projects_yaml).generate('project_1'):
            result = project.generate(False,"uvision")

        assert result == 0
        assert os.path.isdir('create_this_folder')
        shutil.rmtree('create_this_folder')
