
projects_1_yaml = {
    'projects': {
        'project_1' : ['test_workspace/project_1.yaml']
    },
}
project_1_yaml = {
    'common': {
        'sources': ['sources/main.cpp'],
        'includes': ['includes/header1.h'],
        'target': ['mbed-lpc1768'],
        'macros': ['MACRO1', 'MACRO2'],
        'core': ['core1'],
        'output_type': ['exe'],
        'linker_file': ['test_workspace/linker.ld'],
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
