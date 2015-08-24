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
from project_generator.tools.eclipse import EclipseGnuARM

from simple_project import project_1, projects_yaml, make_files, delete_files

class TestProject(TestCase):

    """test things related to the eclipse tool"""

    def setUp(self):
        make_files()

        self.project = next(Generator(projects_yaml).generate('project_1'))

        self.eclipse = EclipseGnuARM(self.project.project, ProjectSettings())

    def tearDown(self):
        # remove created directory
        delete_files()

    def test_export_project(self):
        result = self.project.generate(False,'eclipse_make_gcc_arm')

        assert result == 0
