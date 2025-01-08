# -*- coding: utf-8 -*-

#from distutils.core import setup
from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()


setup(name="dcps", 
      version='0.8.0',
      description='Control of DC Power Supplies/DC Electronic Loads/DMMs/SourceMeters through python',
      long_description_content_type='text/markdown',
      long_description=long_description,
      url='https://github.com/sgoadhouse/dcps',
      author='Stephen Goadhouse', 
      author_email="sgoadhouse@virginia.edu",
      maintainer='Stephen Goadhouse',
      maintainer_email="sgoadhouse@virginia.edu",
      license='MIT',
      keywords=['Rigol', 'DP800', 'DP832A', 'DL3000', 'DL3031A', 'AimTTI', 'BK', '9115', 'Keysight', 'Agilent', 'Keithley', 'ITECH',
                'E3642A', 'E364xA', '6220', '6221', '2182', '2182A', '2400', 'DMM6500', '6500C/D',
                'PyVISA', 'VISA', 'SCPI', 'INSTRUMENT'],
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'], 
     install_requires=[
         'pyvisa>=1.9.0,!=1.11.0',
         'pyvisa-py>=0.4.1'
     ],
     packages=["dcps"],
     include_package_data=True,
     zip_safe=False
)
