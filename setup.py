#!/usr/bin/python
# coding: utf-8

from distutils.core import setup

import blogit

setup(
    name='blogit',
    version=blogit.__version__,
    author=blogit.__author__,
    author_email=blogit.__email__,
    url='https://github.com/metaist/blogit',
    download_url='https://github.com/metaist/blogit',
    description=blogit.__doc__.split('\n')[0],
    long_description=blogit.__doc__,
    py_modules=['metautils', 'blogit'],
    keywords='static blog generator',
    license=blogit.__license__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries'
    ]
)
