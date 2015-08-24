import os
import yaml
import shutil
project_1 = {
    'common': {
        'sources': ['sources/main.cpp'],
        'includes': ['includes/header1.h'],
        'target': ['lpc1768'],
        'macros': ['MACRO1', 'MACRO2'],
        'core': ['core1'],
        'output_type': ['exe'],
    },
    'tool_specific' : {
        'make_gcc_arm':{
            'linker_file' : ['test_workspace/linker.ld']
        },
        'iar_arm':{
            'linker_file' : ['test_workspace/linker.ld']
        },
        'uvision':{
            'linker_file' : ['test_workspace/linker.ld']
        },
        'coide':{
            'linker_file' : ['test_workspace/linker.ld']
        }
    }
}

projects_yaml = {
    'projects': {
        'project_1' : ['test_workspace/project_1.yaml']
    },
    'settings' : {
        'export_dir': ['projects/{tool}_{target}/{project_name}']
    }
}

def make_files():
    if not os.path.exists('test_workspace'):
            os.makedirs('test_workspace')
    if not os.path.exists('sources'):
            os.makedirs('sources')
    if not os.path.exists('includes'):
            os.makedirs('includes')

    with open(os.path.join(os.getcwd(), 'test_workspace/project_1.yaml'), 'wt') as f:
            f.write(yaml.dump(project_1, default_flow_style=False))
        # write projects file
    with open(os.path.join(os.getcwd(), 'test_workspace/projects.yaml'), 'wt') as f:
        f.write(yaml.dump(projects_yaml, default_flow_style=False))
        # create 3 files to test project
    with open(os.path.join(os.getcwd(), 'sources/main.cpp'), 'wt') as f:
        pass
    with open(os.path.join(os.getcwd(), 'includes/header1.h'), 'wt') as f:
        pass

def delete_files():
    shutil.rmtree('test_workspace', ignore_errors=True)
    shutil.rmtree('includes', ignore_errors=True)
    shutil.rmtree('sources', ignore_errors=True)
    shutil.rmtree('projects', ignore_errors=True)