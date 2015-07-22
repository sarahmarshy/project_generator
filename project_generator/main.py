# Copyright 2014-2015 0xc0170
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

import argparse
import os
import logging
import subprocess

from .settings import ProjectSettings

colourful = True

try:
    import chromalog
except ImportError:
    colourful = False

import pkg_resources

from .commands import build, generate, create

subcommands = {
    'create': create,
    'generate': generate,
    'build': build,
}


def main():
    # Parse Options
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', dest='verbosity', action='count', default=0,
                        help='Increase the verbosity of the output (repeat for more verbose output)')
    parser.add_argument('-q', dest='quietness', action='count', default=0,
                        help='Decrease the verbosity of the output (repeat for more verbose output)')

    parser.add_argument("--version", action='version',
                        version=pkg_resources.require("project_generator")[0].version, help="Display version")

    subparsers = parser.add_subparsers(help='commands')

    for name, module in subcommands.items():
        subparser = subparsers.add_parser(name, help=module.help)

        module.setup(subparser)
        subparser.set_defaults(func=module.run)

    args = parser.parse_args()

    # set the verbosity
    verbosity = args.verbosity - args.quietness

    logging_level = max(logging.INFO - (10 * verbosity), 0)

    if colourful:
        chromalog.basicConfig(format="%(levelname)s\t%(message)s", level=logging_level)
    else:
        logging.basicConfig(format="%(levelname)s\t%(message)s", level=logging_level)

    logging.debug('This should be the project root: %s', os.getcwd())

    update()
    args.func(args)

def update(force=True, settings=ProjectSettings()):
    defdir_exists = True
    if not os.path.exists(settings.paths['definitions']):
        defdir_exists = False
        os.mkdir(settings.paths['definitions'])

    # For default, use up to date repo from github
    if settings.get_env_settings('definitions') == settings.get_env_settings('definitions_default'):
        if not defdir_exists:
            cmd = ('git', 'clone', '--quiet',
                   'https://github.com/project-generator/project_generator_definitions.git', '.')
            subprocess.call(cmd, cwd=settings.paths['definitions'])
        elif force:
            # rebase only if force, otherwise use the current version
            cmd = ('git', 'pull', '--rebase', '--quiet', 'origin', 'master')
            subprocess.call(cmd, cwd=settings.paths['definitions'])
        else:
            # check if we are on top of origin/master
            cmd = ('git', 'fetch', 'origin','master', '--quiet')
            subprocess.call(cmd, cwd=settings.paths['definitions'])
            cmd = ('git', 'diff', 'master', 'origin/master', '--quiet')
            p = subprocess.call(cmd, cwd=settings.paths['definitions'])
            # any output means we are behind the master, update
            if p:
                logging.debug("Definitions are behind the origin/master, rebasing.")
                cmd = ('git', 'pull', '--rebase', '--quiet', 'origin', 'master')
                subprocess.call(cmd, cwd=settings.paths['definitions'])

if __name__ == '__main__':
    main()
