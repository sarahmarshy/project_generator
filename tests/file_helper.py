import subprocess
import os
import shutil
import stat

#  clone a url into the given folder inside test_workspace
def clone(url, folder):
    cmd = ('git', 'clone', url, '.')
    dir = os.path.join('test_workspace', folder)
    if not os.path.exists(dir):
        os.makedirs(dir)
    subprocess.call(cmd, cwd=dir)

    #  return the path to the created directory
    return dir

#   make a directory inside test_workspace
def make_test_dir(folder):
    folder = os.path.join("test_workspace",folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    #  return the path to the created directory
    return folder

def rm_clone():
    # remove the test_workspace
    shutil.rmtree('test_workspace', onerror=remShut)

def remShut(*args):
    func, path, _ = args  #  onerror returns a tuple containing function, path and     exception info
    os.chmod(path, stat.S_IWRITE)  #  edit permissions
    os.remove(path)   #  remove path that caused exception