from distutils.core import setup, Extension
setup(
    name='ARGUS',
    version='1.0.0',
    author="Adam Dodge",
    author_email="adam.dodge@colorado.edu",
    description='Graphical User Interface and Control Software for ARGUS Ground Station.',
    url="https://github.com/addodge/ARGUS",
    ext_modules=[Extension('cpredict', ['predict.c'])]
)
