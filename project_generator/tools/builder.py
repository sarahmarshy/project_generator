# Copyright 2014 0xc0170
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
import subprocess
import sys

class Builder:
    def build_project(self):
        raise NotImplementedError

    @staticmethod
    def build_command(args, tool, tool_name, proj_name):
        logging.debug("Calling command: " +  " ".join(args))
        sys.stdout.write("\nBuilding %s project %s..." % (tool_name,proj_name))
        try:
            ret_code = None
            ret_code = subprocess.call(args)
        except:
            if tool_name == "Uvision":
                sys.stdout.write(
                    "Error whilst calling UV4: '%s'. \nPlease set uvision path in the projects.yaml file.\n" % tool.env_settings.get_env_settings('uvision'))
            elif tool_name == "GCC":
                sys.stdout.write("Error whilst calling make. \nIs it in your PATH?\n")
            elif tool_name == "IAR":
                sys.stdout.write("Error whilst calling IarBuild. \nPlease check IARBUILD path in the user_settings.py file.\n")
        else:
            if tool_name != "IAR" and ret_code != tool.SUCCESSVALUE:
                # Seems like something went wrong.
                if ret_code == tool.WARNVALUE:
                    sys.stdout.write(" succeeded with %s\n" % tool.ERRORLEVEL[ret_code])
                else:
                    sys.stdout.write(" failed with %s\n" % tool.ERRORLEVEL[ret_code])
                return -1
            else:
                sys.stdout.write(" succeeded with %s\n" % tool.ERRORLEVEL[ret_code])
                return 0
