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
import shutil

import yaml
from unittest import TestCase

from project_generator.generate import Generator
from project_generator.project import Project
from simple_project import *

def test_output_directory_formatting():
    path, depth = Project._generate_output_dir('aaa/bbb/cccc/ddd/eee/ffff/ggg')

    assert depth == 7
    assert path == '../../../../../../../'

class TestProject(TestCase):

    """test things related to the Project class"""

    def setUp(self):
        if not os.path.exists('test_workspace'):
            os.makedirs('test_workspace')
        # write project file
        with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1_yaml, default_flow_style=False))
        # write projects file
        with open(os.path.join(os.getcwd(), 'test_workspace/projects.yaml'), 'wt') as f:
            f.write(yaml.dump(projects, default_flow_style=False))

        # now that Project and PgenWorkspace accepts dictionaries, we dont need to
        # create yaml files!
        self.project = Generator(projects).generate('project_1').next()

        # create 3 files to test project
        with open(os.path.join(os.getcwd(), 'test_workspace/main.cpp'), 'wt') as f:
            pass
        with open(os.path.join(os.getcwd(), 'test_workspace/header1.h'), 'wt') as f:
            pass
        with open(os.path.join(os.getcwd(), 'test_workspace/linker.ld'), 'wt') as f:
            pass

    def tearDown(self):
        # remove created directory
        shutil.rmtree('test_workspace', ignore_errors=True)
        shutil.rmtree('projects', ignore_errors=True)

    def test_project_yaml(self):
        # test using yaml files and compare basic data
        project = Generator(projects).generate('project_1').next()
        assert self.project.name == project.name
        # fix this one, they should be equal
        #self.assertDictEqual(self.project.project, project.project)

    def test_name(self):
        assert self.project.name == 'project_1'

    def test_set_output_dir_path(self):
        self.project.for_tool('make_gcc')
        self.project._set_output_dir_path()
        assert self.project.project['output_dir']['path'] == os.path.join('projects','make_gcc_arm','project_1')

    def test_supported(self):
        self.project.for_tool('make_gcc')
        supported = ['uvision','sublime_make_gcc_arm', 'make_gcc_arm', 'sublime', 'eclipse_make_gcc_arm']
        for x in supported:
            if x not in self.project.supported:
                assert False
        for x in self.project.supported:
            if x not in supported:
                assert False
        assert True
