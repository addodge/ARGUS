#!/usr/bin/env python3

from distutils.core import setup, Extension
setup(
    name='cpredict',
    version='1.0',
    author="Adam Dodge",
    author_email="adam.dodge@colorado.edu",
    url="https://github.com/addodge/ARGUS",
    ext_modules=[Extension('cpredict', ['predict.c'])]
    )
