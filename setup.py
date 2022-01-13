from setuptools import setup
from shutil import which

if not which('depth_potential'):
    raise Exception('depth_potential not found, please install CIVET.')


setup(
    name='pybicpl',
    version='0.2.0',
    py_modules=['pybicpl'],
    url='https://github.com/FNNDSC/pybicpl',
    license='MIT',
    author='Jennings Zhang',
    author_email='Jennings.Zhang@childrens.harvard.edu',
    description='Python interface for basic MNI .obj file format. '
                'Supports read, write, and calculations on a vertex neighbor graph.',
    install_requires=['numpy~=1.22.0'],
    python_requires='>=3.6',
)
