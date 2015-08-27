import os
import yaml
from .util import FILES_EXTENSIONS
import logging
import bisect
from collections import defaultdict

def _determine_tool(files):
    """Yields tuples in the form of (linker file, tool the file links for"""
    for file in files:
        linker_ext = file.split('.')[-1]
        if "sct" in linker_ext or "lin" in linker_ext:
            yield (str(file),"uvision")
        elif "ld" in linker_ext:
            yield (str(file),"make_gcc_arm")
        elif "icf" in linker_ext:
            yield (str(file),"iar_arm")


def _scan(section, root, directory, extensions):
    if section == "sources":
        data_dict = defaultdict(list)  # sources can have group names, making them a dict
    else:
        data_dict = []
    for dirpath, dirnames, files in os.walk(directory):
        for filename in files:
            ext = filename.split('.')[-1]
            relpath = os.path.relpath(dirpath, root)
            if ext in extensions: # Check if the files extension is an acceptable one for this section of yaml
                if section == "sources":
                    #get the directory one below root
                    dir = directory.split(os.path.sep)[-1] if dirpath == directory else dirpath.replace(directory,'').split(os.path.sep)[1]
                    if relpath not in data_dict[dir]:
                        # Add the path to the file to this dictionary, with dir as group name
                        bisect.insort(data_dict[dir], os.path.normpath(relpath))
                elif section == 'includes':
                    #get all the folders along the path
                    dirs = relpath.split(os.path.sep)
                    for i in range(1, len(dirs)+1):
                        """ add all combinations of them, because we don't know how they will be referenced in program files
                            Example - there is a .h file in the path Here\is\include\include.h
                            We want to catch any possible combo, so add Here, Here\is, and Here\is\include

                        """
                        data_dict.append(os.path.normpath(os.path.sep.join(dirs[:i])))
                else:
                    data_dict.append(os.path.normpath(os.path.join(relpath, filename)))
    if section == "sources":
        return dict(data_dict)
    l = list(set(data_dict))
    l.sort()
    return l

def _generate_file(filename,root,directory,data):
    logging.debug('Writing the follwoing to %s:\n%s'%(filename,yaml.dump(data)))
    if os.path.isfile(os.path.join(directory, filename)):
        os.remove(os.path.join(directory, filename))
    try:
        with open(os.path.join(directory, filename), 'w+') as f:
            f.write(yaml.dump(data, default_flow_style=False))
    except:
        logging.error("Unable to open %s for writing!"%filename)
        return -1
    logging.info("Wrote to file %s."%filename)
    p = os.popen('attrib +h ' + filename) # make the file hidden
    p.close()
    return 0


def create_yaml(root, directory, project_name, board,output_dir):
    # lay out what the common section a project yaml file will look like
    # The value mapped to by each key are the file extensions that will help us get valid files for each section
    logging.debug("Project name: %s, Target: %s"%(project_name,board))
    common_section = {
        'linker_file': FILES_EXTENSIONS['linker_file'],
        'sources': FILES_EXTENSIONS['source_files_c'] + FILES_EXTENSIONS['source_files_cpp'] +
                   FILES_EXTENSIONS['source_files_s'] + FILES_EXTENSIONS['source_files_obj'],
        'includes': FILES_EXTENSIONS['includes'],
        'target': [],
    }

    # will be written to .projects.yaml
    projects_yaml = {
        'projects': {
            project_name: ['.project.yaml']
        },
        'settings': {'export_dir': [output_dir]}
    }

    # will be written to .project.yaml
    project_yaml = {
        'common': {},
        'tool_specific': {}
    }

    # iterate over the common section defined above
    for section, extensions in common_section.items():
        if len(common_section[section]) > 0:
            # look for files in this directory that have the defined extensions, and add them to our project file
            project_yaml['common'][section] = _scan(section, root, directory,extensions)

    project_yaml['common']['target'] = [board] # user passes target in command line

    """Find what tool the linker works for - if multiple linkers in this dir, project_yaml['common']['linker_file']
        is a list. Tools is an iterator"""
    tools = _determine_tool(project_yaml['common']['linker_file'])

    linkers = {}   # dictionary containing all linker files in the project directory

    # exhaust the iterator and add its yielded values to linkers
    for (file,tool) in tools:
        if tool in linkers:
            linkers[tool].append(file)
        else:
            linkers[tool] = [file]

    for tool, linker in linkers.items():
        if len(linker) > 1:
            # The project directory defined more than one linker for a tool
            print "\nMultipe linkers found for " + tool + "\n"
            for i, file in enumerate(linker):
                print(str(i) + ": " + file)
            answer = raw_input('\nWhich file do you want? ')
            while int(answer) not in range(0,len(linker)):
                answer = raw_input('Answer not in list. Which file do you want? ')
            project_yaml['tool_specific'][tool] = {'linker_file': [linkers[tool][int(answer)]]}
        else:
            project_yaml['tool_specific'][tool] = {'linker_file': linker}

    # linker file is now in tool_specific section
    del project_yaml['common']['linker_file']

    ret = _generate_file(".projects.yaml", root, directory, projects_yaml)
    if ret < 0: # make sure the first file generated correctly
        return -1
    _generate_file(".project.yaml", root, directory, project_yaml)



