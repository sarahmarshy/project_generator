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

from unittest import TestCase

from project_generator.targets import Targets
from project_generator.settings import ProjectSettings

class TestProject(TestCase):

    """test things related to the Project class"""

    def setUp(self):
        settings = ProjectSettings()
        self.targets = Targets(settings.get_env_settings('definitions'))

    def test_target(self):
        target = self.targets.get_target('k64f')
        # it's not empty dictionary and has at least mcu and tool specific
        assert bool(target)
        assert bool(target.config['mcu'])
        assert bool(target.config['tool_specific'])

    def test_core(self):
        core = self.targets.get_target('k64f').core
        assert core == 'cortex-m4f'

    def test_tool_def(self):
        # test k64f for uvision, should not be empty
        tool_def = self.targets.get_target('k64f').get_tool_configuration('uvision')
        assert bool(tool_def)

