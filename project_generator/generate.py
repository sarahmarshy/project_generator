from project import *
import logging
class Generator:
    def __init__(self, projects_file):
        if type(projects_file) is not dict:
            with open(projects_file, 'rt') as f:
                self.projects_dict = yaml.load(f)
        else:
            self.projects_dict = projects_file

    def generate(self, name = '', ignore = []):
        if 'projects' in self.projects_dict:
            # User has chosen to generate a project based on specifically named project
            if name != '':
                # Check if the name they specified is even in the yaml ile
                if name not in self.projects_dict['projects'].keys():
                    logging.critical("You specified an invalid project name.")
                else:
                    # Get the portion of the yaml that is just the project specified
                    records = self.projects_dict['projects'][name]
                    # Load the yamls defined in that section
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
                    if project_dicts is not None:
                        # Yield this generated project to be dealt with in command scripts
                        yield Project(project_dicts,self.projects_dict, name, ignore)
                    else:
                        yield None
            else:  # user hasn't specified, generate all possible projects
                for name, records in self.projects_dict['projects'].items():
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
                    if project_dicts is not None:
                        yield Project(project_dicts,self.projects_dict,name, ignore)
                    else:
                        yield None
        else:
            logging.debug("No projects found in the main record file.")




