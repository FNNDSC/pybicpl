from setuptools import setup

setup(
    name='pybicpl',
    version='0.1-1',
    py_modules=['pybicpl'],
    url='https://github.com/FNNDSC/pybicpl',
    license='MIT',
    author='Jennings Zhang',
    author_email='Jennings.Zhang@childrens.harvard.edu',
    description='Python interface for basic MNI .obj file format. '
                'Supports read, write, and calculations on a vertex neighbor graph.',
    install_requires=['numpy~=1.19.0'],
    python_requires='>=3.6',
)
