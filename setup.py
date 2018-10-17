#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Ahmed Zerouali <ahmed@bitergia.com>
#     Valerio Cosentino <valcos@bitergia.com>
#

from setuptools import setup

setup(
        name='TechLag',
        version='0.1.0',
        description='TechLag: a tool to calculate the technical lag of your javascript package',
        long_description='TechLag calculates the technical lag of your javascript package by checking its '
                         'dependencies',
        license="GPLv3",
        url='https://github.com/neglectos/TechLag',

        author='Bitergia',
        author_email='ahmed@bitergia.com',

        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering :: Information Analysis',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'License :: OSI Approved :: MIT License'
        ],
        keywords='javascript technical-lag json npm',
        packages=[
            'techlag'
        ],
        install_requires=[
            'pandas>=0.22.0',
            'requests>=2.18.2'
        ],
        scripts=[
            'bin/techlag'
        ],
        zip_safe=False
)
