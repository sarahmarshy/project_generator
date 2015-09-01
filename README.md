# Project generator
[![Build Status](https://travis-ci.org/project-generator/project_generator.svg?branch=master)](https://travis-ci.org/project-generator/project_generator)

Source code is often times simple but building it is difficult when more than one person is involved.
Developers like what they like: IDE, compiler, debugger and really all we want is to produce an executable.
Sharing project files decoding XML in commit messages because someone was debugging and changed compile options before commiting distracts from doing what you want to do; develop software.

This project allows you to generate IDE project files. Project gene
based on the rules defined in records. No one should ever commit IDE specific project file to a repository again!

All open sourced - licensed under Apache v2.0 license.

### Current Status

The project is in alpha phase. Check issues for the ongoing tasks or todo tasks.

Project generator currently generaters projects for the following tools (IDE, Makefile, etc..):

 - uVision
 - Makefile (GCC ARM)
 - IAR
 - Eclipse (Makefile with GCC ARM)
 - Sublime (Makefile with GCC ARM)

We appreciate any help and you are more than welcome to send a pull request or create a new issue in this repository.
The plan is to support as many IDE as possible , same applies for targets/MCU.

### How to use it

Clone this repository to your project directory.

##### Using package
Once installed, test if project_generator is recognized:

```
pgen --version
```
This should print the current installed version. You can use pgen or project_generator as a command.

##### Using directly the repository
In case of using this repository directly, be aware, the project generator is using relative paths. Run:
```
python setup.py --develop
```

##### Getting started

An example how to use pgen [here](https://github.com/sarahmarshy/pgen_simple_example).

To get familiar with it, read our wiki. Good start is [Getting started guide (wiki)](https://github.com/project-generator/project_generator/wiki/Getting_started). There are other sections which describe the each blocks of the project generator.

Dependencies for Project generator
-------------------------
* Python 2.7
 * [pyYAML](https://github.com/yaml/pyyaml)
 * [Setuptools](https://pypi.python.org/pypi/distribute)
 * [Jinja2](https://pypi.python.org/pypi/Jinja2)
 * [xmltodict](https://pypi.python.org/pypi/xmltodict)
