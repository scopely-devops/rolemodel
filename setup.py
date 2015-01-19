#!/usr/bin/env python

from setuptools import setup, find_packages

import os

requires = [
    'botocore==0.82.0',
    'click==3.3',
    'PyYAML>=3.11'
]


setup(
    name='rolemodel',
    version=open(os.path.join('rolemodel', '_version')).read().strip(),
    description='A tool to help manage cross-account roles in AWS',
    long_description=open('README.md').read(),
    author='Mitch Garnaat',
    author_email='mitch@garnaat.com',
    url='https://github.com/scopely-devops/rolemodel',
    packages=find_packages(exclude=['tests*']),
    package_data={'rolemodel': ['_version']},
    package_dir={'rolemodel': 'rolemodel'},
    scripts=['bin/rolemodel'],
    install_requires=requires,
    license=open("LICENSE").read(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ),
)
