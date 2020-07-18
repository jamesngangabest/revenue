from setuptools import setup

import revpy

setup(
    name='revpy',
    version=revpy.__version__,
    maintainer='james nyoro@inifinity tech',
    maintainer_email='jamesngangabest@gmil.com',
    packages=['revpy'],
    long_description=open('README.md').read(),
    test_suite='nose.collector',
    tests_require=['nose'],
    url='https://github.com/jamesngangabest/revenue'
)
