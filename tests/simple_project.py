project_1_yaml = {
    'common': {
        'sources': ['test_workspace/main.cpp'],
        'includes': ['test_workspace/header1.h'],
        'macros': ['MACRO1', 'MACRO2'],
        'target': ['mbed-lpc1768'],
        'core': ['core1'],
        'tools_supported': ['iar_arm', 'uvision', 'coide', 'unknown'],
        'output_type': ['exe'],
        'debugger': ['j-link'],
    },
    'tool_specific':{
        'make_gcc_arm':{
            'linker_file': ['test_workspace/linker.ld']
        },
        'uvision':{
            'linker_file': ['test_workspace/linker.sct']
        }
    }
}

project_2_yaml = {
    'common': {
        'sources': ['test_workspace/main.cpp'],
        'includes': ['test_workspace/header1.h'],
        'macros': ['MACRO1', 'MACRO2'],
        'target': ['mbed-lpc1768'],
        'core': ['core2'],
        'tools_supported': ['iar_arm', 'uvision', 'coide', 'unknown'],
        'output_type': ['exe'],
        'debugger': ['j-link'],
    },
    'tool_specific':{
        'uvision':{
            'linker_file': ['test_workspace/linker.sct']
        }
    }
}

projects = {
    'projects': {
        'project_1': ['test_workspace/project_1.yaml'],
        'project_2': ['test_workspace/project_2.yaml']
    },
    'settings':{
        'export_dir': ['projects\{tool}\{project_name}']
    }
}
