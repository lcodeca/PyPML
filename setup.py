#!/usr/bin/env python3

""" PYTHON3 - Setup for pypml. """

from setuptools import setup

def readme():
    """ README """
    with open('README.rst') as freader:
        return freader.read()

setup(name='pypml',
      version='0.2',
      description='Parking Monitor Library for SUMO via TraCI.',
      url='http://github.com/lcodeca/pypml',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)',
          'Programming Language :: Python :: 3 :: Only',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
      ],
      author='Lara Codeca',
      author_email='lara.codeca@gmail.com',
      license='EPL-2.0',
      packages=['pypml'],
      install_requires=[],
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'])
