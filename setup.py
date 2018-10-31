#!/usr/bin/python3

from distutils.core import setup, Extension
setup(
    name='ARGUS',
    version='1.0',
    author="Adam Dodge",
    author_email="adam.dodge@colorado.edu",
    url="https://github.com/addodge/ARGUS",
    py_modules=['predict'],
    ext_modules=[Extension('cpredict', ['predict.c'])]
    )
