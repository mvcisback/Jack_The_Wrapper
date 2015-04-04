#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='JackTheWrapper',
    version='0.1.1',
    author='Marcell Vazquez-Chanlatte',
    packages=find_packages(),
    url='',
    license='LICENSE',
    description='',
    long_description=open('README.md').read(),
    install_requires=['py-jack==0.5.2', 'numpy'],
)
