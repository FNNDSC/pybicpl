from setuptools import setup
import os
import shutil

if not os.getenv('GITHUB_WORKFLOW') == 'Publish' \
        and not shutil.which('depth_potential'):
    raise Exception('depth_potential not found, please install CIVET.')

setup(
    name='pybicpl',
    version='0.5.1',
    packages=['bicpl'],
    url='https://github.com/FNNDSC/pybicpl',
    license='MIT',
    author='Jennings Zhang',
    author_email='Jennings.Zhang@childrens.harvard.edu',
    description='Python interface for basic MNI .obj file format. '
                'Supports read, write, and calculations on a vertex neighbor graph.',
    install_requires=['numpy~=1.22'],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'obj_wf2mni = bicpl.wavefront:wavefront2mni',
            'obj_mni2wf = bicpl.wavefront:mni2wavefront',
            'obj_wf2asc = bicpl.wavefront:wavefront2asc'
        ]
    }
)
