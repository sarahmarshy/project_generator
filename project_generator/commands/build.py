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
import generate
import logging

from ..project import Project

help = 'Build a project'


def run(args):
    # Export if we know how, otherwise return
    if os.path.exists(args.file):
        # known project from records
        project = Project(args.file)
        project.export(args.tool, False)
        project.build(args.tool)
    else:
        # not project known by pgen
        logging.warning("%s not found." % args.file)

def setup(subparser):
    subparser.add_argument(
        "-f", "--file", help="YAML projects file", default='projects.yaml')
    subparser.add_argument(
        "-t", "--tool", help="Build a project files for provided tool")
    subparser.add_argument(
        "-dir", "--directory", help="The projects directory")
