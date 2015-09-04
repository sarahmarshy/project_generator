import logging
import yaml
import os

from project import Project
from.util import load_yaml_records

class Generator:
    def __init__(self, pgen_data):
        logging.debug("Reading from %s"%pgen_data)
        with open(pgen_data, 'rt') as f:
            self.projects_dict = yaml.load(f)

    def generate(self, name = '', ignore = []):
        if 'projects' in self.projects_dict:
            # User has chosen to generate a project based on specifically named project
            if name != '':
                # Check if the name they specified is even in the yaml ile
                if name not in self.projects_dict['projects'].keys():
                    logging.critical("You specified an invalid project name.")
                    yield None
                else:
                    # Get the portion of the yaml that is just the project specified
                    records = self.projects_dict['projects'][name]
                    # Load the yamls defined in that section
                    settings = self.format_settings(self.projects_dict)
                    yaml_file = self.parse_project(records, settings)
                    project_dicts = load_yaml_records([yaml_file])
                    if project_dicts is not None:
                        # Yield this generated project to be dealt with in command scripts
                        yield Project(project_dicts,settings, name, ignore)
                    else:
                        yield None
            else:  # user hasn't specified, generate all possible projects
                for name, records in self.projects_dict['projects'].items():
                    settings = self.format_settings(self.projects_dict)
                    yaml_file = self.parse_project(records, settings)
                    project_dicts = load_yaml_records([yaml_file])
                    if project_dicts is not None:
                        yield Project(project_dicts, settings, name, ignore)
                    else:
                        yield None
        else:
            logging.warning("No projects found in the main record file.")

    def parse_project(self, project_settings, settings):
        if 'export_dir' in project_settings:
            settings['settings']['export_dir'] = project_settings['export_dir']
        if 'root' in project_settings:
            settings['settings']['root'] = project_settings['root']

        settings['settings']['export_dir'] = os.path.relpath(settings['settings']['export_dir'], settings['settings']['root'])
        return project_settings['config']

    def format_settings(self, projects_dict):
        settings = {'settings':{}}
        if 'settings' in projects_dict:
            if 'export_dir' in projects_dict['settings']:
                settings['settings']['export_dir'] = projects_dict['settings']['export_dir']
        else:
            settings['settings']['export_dir'] = ''

        settings['settings']['root'] = os.getcwd()
        return settings







