from unittest import TestCase
import subprocess
import os

from file_helper import clone, rm_clone, make_test_dir
from format_commands import format_build, format_create, format_generate

class Test_Workflow(TestCase):

    def setUp(self):
        self.proj_name = 'project_1'

        #   create a directory test_workspace/self.proj_name and clone this project into it
        self.project_location = clone('https://github.com/sarahmarshy/pgen_simple_example.git',self.proj_name)

        #  path from project_location to the yaml option files
        self.target_settings = 'target_uvision.yaml'
        self.tool_settings = 'uvision_options.yaml'

        #  defined tool
        self.tool = "uvision"

        #  where the tools build command is located
        self.build_path = os.path.normpath("C:\\Keil\\UV4\UV4.exe")

    def tearDown(self):
        # remove created directory
        rm_clone()

    #  test generating a project in the root of the source directory
    def test_create_generate_build_cwd(self):
        #  create
        args = format_create(mcu='k64f')

        #  execute the create command inside the project's root
        subprocess.call(args, cwd = self.project_location)
        assert os.path.isfile(os.path.join(self.project_location,'.projects.yaml'))
        assert os.path.isfile(os.path.join(self.project_location,'.project.yaml'))

        #  generate
        args = format_generate(dev=self.tool,target=self.target_settings, settings = self.tool_settings)
        subprocess.call(args, cwd = self.project_location)

        #  since we generated in the project's root, there should be a project file there
        file_path = os.path.join(self.project_location, self.proj_name +'.uvproj')
        assert os.path.isfile(file_path)

        #  build
        args = format_build(dev=self.tool,exe=self.build_path)
        subprocess.call(args, cwd = self.project_location)

        #  since our project file was in the project root, the build directory should also be there
        #  a successful uvision build will generate a .axf
        build = os.path.join(self.project_location, 'build', self.proj_name + '.axf')
        assert os.path.isfile(build)

    def test_create_generate_build_other_dir(self):
        #  create

        #  Let's generate a project file named something other than the root of source dir name (which is default)
        self.proj_name = "test_diff_name"

        #  Make an output_dir inside test_workspace, since we will be executing our commands in 'test_workspace',
        #  get the rel path
        output_dir = os.path.relpath(make_test_dir("output"),"test_workspace")

        #  Again, since we will execute our commands outside of the source and inside test_workspace, we need a relpath
        proj_loc = os.path.relpath(self.project_location,"test_workspace")

        args = format_create(project=self.proj_name,mcu="k64f",dir=proj_loc, output= output_dir)
        subprocess.call(args, cwd = 'test_workspace')
        assert os.path.isfile(os.path.join('test_workspace','.projects.yaml'))
        assert os.path.isfile(os.path.join('test_workspace','.project.yaml'))

        #  generate
        target_settings = os.path.join(proj_loc,self.target_settings)
        tool_settings = os.path.join(proj_loc,self.tool_settings)
        args = format_generate(dev=self.tool,target=target_settings, settings = tool_settings)
        subprocess.call(args, cwd = 'test_workspace')

        #  The project file should be in our specified output_dir
        file_path = os.path.join('test_workspace',output_dir, self.proj_name+'.uvproj')
        assert os.path.isfile(file_path)

        #  build
        args = format_build(dev=self.tool,exe=self.build_path)
        subprocess.call(args, cwd = 'test_workspace')

        #  the build directory should also be in the new output_dir
        build = os.path.join('test_workspace',output_dir, 'build',  self.proj_name+'.axf')
        assert os.path.isfile(build)






