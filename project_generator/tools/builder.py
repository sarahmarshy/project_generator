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

class Builder:
    def build_project(self):
        raise NotImplementedError

    @staticmethod
    def build_command(args, tool, tool_name, proj_name):
        logging.debug("Calling command: " +  " ".join(args))
        try:
            ret_code = None
            ret_code = subprocess.call(args)
        except:
            if tool_name == "Uvision":
                logging.error(
                    "Error whilst calling UV4: '%s'. Please set uvision path in the projects.yaml file." % tool.env_settings.get_env_settings('uvision'))
            elif tool_name == "GCC":
                logging.error("Error whilst calling make. Is it in your PATH?")
            elif tool_name == "IAR":
                logging.error("Error whilst calling IarBuild. Please check IARBUILD path in the user_settings.py file.")
        else:
            if tool_name != "IAR" and ret_code != tool.SUCCESSVALUE:
                # Seems like something went wrong.
                if ret_code == tool.WARNVALUE:
                    logging.warn("%s building %s succeeded with the status: %s" % (tool_name,proj_name,tool.ERRORLEVEL[ret_code]))
                else:
                    logging.error("%s building %s failed with the status: %s" % (tool_name,proj_name,tool.ERRORLEVEL[ret_code]))
            else:
                logging.info("%s building %s succeeded with the status: %s" % (tool_name,proj_name, tool.ERRORLEVEL[ret_code]))
