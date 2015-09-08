#  Refer to command help sections for determining command usage


#  Keys are the same as the verbose names for create command's arguments
#  These are 'project', 'mcu', 'dir', 'output'
def format_create(**kwargs):
    args = ['pgen','create']
    if 'project' in kwargs:
        args.extend(['-p',kwargs['project']])
    if 'mcu' in kwargs:
        args.extend(['-m',kwargs['mcu']])
    if 'dir' in kwargs:
        args.extend(['-d',kwargs['dir']])
    if 'output' in kwargs:
        args.extend(['-o',kwargs['output']])
    return args

#  Keys are the same as the verbose names for generate command's arguments
#  These are 'file', 'project', 'dev', 'ignore', 'target', 'settings', 'copy'
def format_generate(**kwargs):
    args = ['pgen','generate']
    if 'file' in kwargs:
        args.extend(['-f',kwargs['file']])
    if 'project' in kwargs:
        args.extend(['-p',kwargs['project']])
    if 'dev' in kwargs:
        args.extend(['-d',kwargs['dev']])
    if 'ignore' in kwargs:
        args.extend(['-i',kwargs['ignore']])
    if 'target' in kwargs:
        args.extend(['-t',kwargs['target']])
    if 'settings' in kwargs:
        args.extend(['-s',kwargs['settings']])
    if 'copy' in kwargs: #boolean value
        args.extend(['-c'])
    return args

#  Keys are the same as the verbose names for build command's arguments
#  These are 'file', 'project', 'dev', 'exe'
def format_build(**kwargs):
    args = ['pgen','build']
    if 'file' in kwargs:
        args.extend(['-f',kwargs['file']])
    if 'project' in kwargs:
        args.extend(['-p',kwargs['project']])
    if 'dev' in kwargs:
        args.extend(['-d',kwargs['dev']])
    if 'exe' in kwargs:
        args.extend(['-e',kwargs['exe']])
    return args