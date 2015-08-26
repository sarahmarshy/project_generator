# Copyright 2014-2015 0xc0170
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
import locale
import shutil
import string
import operator
import subprocess
from .settings import ProjectSettings
import logging

from functools import reduce

FILES_EXTENSIONS = {
    'includes': ['h', 'hpp', 'inc'],
    'source_files_s': ['s','S','asm'],
    'source_files_c': ['c'],
    'source_files_cpp': ['cpp', 'cc'],
    'source_files_a': ['ar', 'a'],
    'source_files_obj': ['o', 'obj'],
    'linker_file': ['sct', 'ld', 'lin', 'icf'],
}
VALID_EXTENSIONS = FILES_EXTENSIONS['source_files_s'] + FILES_EXTENSIONS['source_files_c'] + FILES_EXTENSIONS['source_files_cpp'] + FILES_EXTENSIONS['source_files_a'] + FILES_EXTENSIONS['source_files_obj']
FILE_MAP = {}
for key,values in FILES_EXTENSIONS.items():
    for value in values:
        FILE_MAP[value] = key
SOURCE_KEYS = ['source_files_c', 'source_files_s', 'source_files_cpp', 'source_files_a', 'source_files_obj']

def rmtree_if_exists(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)

def uniqify(_list):
    # see: http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order/29898968#29898968
    return reduce(lambda r, v: v in r[1] and r or (r[0].append(v) or r[1].add(v)) or r, _list, ([], set()))[0]

def merge_recursive(*args):
    if all(isinstance(x, dict) for x in args):
        output = {}
        keys = reduce(operator.or_, [set(x) for x in args])

        for key in keys:
            # merge all of the ones that have them
            output[key] = merge_recursive(*[x[key] for x in args if key in x])

        return output
    else:
        return reduce(operator.add, args)

def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def unicode_available():
    return locale.getdefaultlocale()[1] == 'UTF-8'

def load_yaml_records(yaml_files):
    dictionaries = []
    for yaml_file in yaml_files:
        if os.path.exists(yaml_file):
            f = open(yaml_file, 'rt')
            dictionaries.append(yaml.load(f))
        else:
            logging.critical("The file %s referenced in main yaml doesn't exist." % yaml_file)
            return None
    return dictionaries

class PartialFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
        except (IndexError, KeyError, AttributeError):
            first, _ = field_name._formatter_field_name_split()
            val = '{' + field_name + '}', first
        return val

def update(force=True, settings=ProjectSettings()):
    defdir_exists = True
    if not os.path.exists(settings.paths['definitions']):
        defdir_exists = False
        os.mkdir(settings.paths['definitions'])

    # For default, use up to date repo from github
    if settings.get_env_settings('definitions') == settings.get_env_settings('definitions_default'):
        if not defdir_exists:
            cmd = ('git', 'clone', '--quiet',
                   'https://github.com/sarahmarshy/pgen_definitions.git', '.')
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
