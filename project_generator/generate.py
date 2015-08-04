from project import *

class Generator:
    def __init__(self, projects_file):
        if type(projects_file) is not dict:
            try:
                with open(projects_file, 'rt') as f:
                    self.projects_dict = yaml.load(f)
            except IOError:
               raise IOError("The main pgen projects file %s doesn't exist." % projects_file)
        else:
            self.projects_dict = projects_file

    def generate(self, name = '', ignore = []):
        if 'projects' in self.projects_dict:
            if name != '':
                if name not in self.projects_dict['projects'].keys():
                    raise RuntimeError("You specified an invalid project name.")
                else:
                    records =self.projects_dict['projects'][name]
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
                    yield Project(project_dicts,self.projects_dict, name, ignore)
            else:
                for name, records in self.projects_dict['projects'].items():
                    project_dicts = load_yaml_records(uniqify(flatten(records)))
                    yield Project(project_dicts,self.projects_dict,name, ignore)
        else:
            logging.debug("No projects found in the main record file.")




