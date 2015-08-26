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

from .uvision import *
import yaml
class Uvision5(Uvision):
    def __init__(self, workspace, env_settings):
        super(Uvision5,self).__init__(workspace, env_settings)

    @staticmethod
    def get_toolnames():
        return ['uvision5','uvision']

    @staticmethod
    def get_toolchain():
        return 'uvision'

    def generate_project(self):
        data = self.workspace.copy()
        self.parse_data('uvision5',data)
        data ['vendor'] = data ['target'].vendor
        # Project file
        self.generate_file('uvision5.uvprojx.tmpl',data,'uvprojx')
        return 0

    def get_mcu_definition(self, project_file, mcu):
        """ Parse project file to get target definition """
        mcu_back = copy.deepcopy(mcu)
        mcu_back = super(Uvision5, self).get_mcu_definition(project_file,mcu_back)
        project_file = join(getcwd(), project_file)
        uvproj_dic = xmltodict.parse(file(project_file), dict_constructor=dict)
        # Generic Target, should get from Target class !
        vendor = uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Vendor']
        mcu['mcu']['vendor'] = vendor
        device = mcu_back['tool_specific']['uvision']['TargetOption']['Device']
        mcu['tool_specific']['uvision5'] = {
            'TargetOption':{'Device':device}
        }

        return mcu