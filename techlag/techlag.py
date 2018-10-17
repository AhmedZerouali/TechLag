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

import logging
import pandas as pd
import requests
import subprocess
import warnings

from .errors import ParamsError

warnings.simplefilter(action='ignore', category=Warning)

RELEASE_MINOR = 'minor'
RELEASE_MAJOR = 'major'
RELEASE_PATCH = 'patch'

DEPENDENCIES_KIND = "dependencies"
DEV_DEPENDENCIES_KIND = "devDependencies"

DEPENDENCIES = [DEPENDENCIES_KIND, DEV_DEPENDENCIES_KIND]


class TechLag:
    """Techlag, a tool to calculate the technical lag of your javascript package.

    The tool can be executed in two ways, either:
        - the package name, version and kind of dependencies to analyze
        - the URI of a package.json plus the kind of dependencies to analyze

    Possible examples of executions are:
        - TechLag(pjson=https://raw.githubusercontent.com/jasmine/jasmine/master/package.json,
                  kind='devDependencies")
        - TechLag(package="grunt", version="1.0.0", kind="dependencies")

    :param package: target package name
    :param version: the target package version
    :param kind: kind of dependencies to analyze
    :param pjson: valid package.json URI
    """

    version = '0.1.0'

    def __init__(self, package=None, version=None, kind=None, pjson=None):
        if not kind:
            raise ParamsError(cause="kind of dependencies cannot be null")

        if package and version and kind:
            if pjson:
                raise ParamsError(cause="too many parameters passed")

        if pjson and kind:
            if package or version:
                raise ParamsError(cause="too many parameters passed")

        if kind not in DEPENDENCIES:
            logging.warning("Unknown kind dep ..., set it to %s", DEPENDENCIES_KIND)
            kind = DEPENDENCIES_KIND

        self.package = package
        self.version = version
        self.kind = kind
        self.pjson = pjson

    def analyze(self):
        """Calculate the technical lag for the target package"""

        if self.pjson:
            json = TechLag.parse_url(self.pjson)
            dependencies = (pd.DataFrame({'dependency': list(json[self.kind].keys()),
                                          'constraint': list(json[self.kind].values()),
                                          'kind': self.kind})
                            )
        else:
            version = self.semver(self.version, self.get_versions(self.package).version.tolist())
            dependencies = self.get_dependencies(self.package, version, self.kind)

        result = self.calculate_lags(dependencies)
        return result

    @staticmethod
    def get_dependencies(package, version, kind):
        """Fetch the dependencies of a given type for a target version of a package.

        :param package: target package name
        :param version: the target package version
        :param kind: kind of dependencies to analyze

        :return: a pandas data frame with the dependencies
        """

        json = TechLag.parse_url('http://registry.npmjs.org/' + package + '/' + version)
        dependencies = (pd.DataFrame({'dependency': list(json[kind].keys()),
                                      'constraint': list(json[kind].values()),
                                      'kind': kind}))

        return dependencies

    def semver(self, constraint, versions):
        """Get the semantic version of a package.

        :param constraint: version constraint
        :param versions: list package versions

        :return: the semantic version of the package
        """

        args = ['semver', '-r', constraint] + list(versions)

        completed = subprocess.run(args, stdout=subprocess.PIPE)
        if completed.returncode == 0:
            return completed.stdout.decode().strip().split('\n')[-1]
        else:
            return ''

    @staticmethod
    def get_versions(package):
        """Get the version of a given package.

        :param package: target package name

        :return: pandas data frame of package versions
        """

        versions = TechLag.parse_url('http://registry.npmjs.org/' + package)['time']
        versions.pop('modified')
        versions.pop('created')
        versions = (pd.DataFrame({'version': list(versions.keys()),
                                  'date': list(versions.values()),
                                  'package': package}))

        return versions

    def calculate_lags(self, dependencies):
        """Calculate technical lag for a list of dependencies.

        :param dependencies: pandas data frame of package dependencies

        :return: the dependencies with the corresponding technical lag
        """

        dependencies['used_version'] = ''
        dependencies['latest_version'] = ''
        dependencies[RELEASE_MAJOR + '_lag'] = ''
        dependencies[RELEASE_MINOR + '_lag'] = ''
        dependencies[RELEASE_PATCH + '_lag'] = ''

        for row in range(0, len(dependencies)):
            list_versions = self.get_versions(dependencies.iloc[row].dependency)

            latest = self.semver('*', list_versions.version.tolist())
            used = self.semver(dependencies.iloc[row].constraint, list_versions.version.tolist())

            lag = self.compute_lag(list_versions, used, latest)

            dependencies.latest_version.iloc[row] = latest
            dependencies.used_version.iloc[row] = used
            dependencies.major_lag.iloc[row] = lag[RELEASE_MAJOR]
            dependencies.minor_lag.iloc[row] = lag[RELEASE_MINOR]
            dependencies.patch_lag.iloc[row] = lag[RELEASE_PATCH]

        return dependencies

    @staticmethod
    def compute_lag(versions, used, latest):
        """Compute the technical lag for the set of versions of a given package.

        :param versions: pandas data frame of the package versions
        :param used: version in use of the package
        :param latest: latest version available of the package

        :return: the technical lag
        """
        used = TechLag.convert_version(used.split('-')[0])
        latest = TechLag.convert_version(latest.split('-')[0])

        if used == latest:
            return {RELEASE_MAJOR: 0, RELEASE_MINOR: 0, RELEASE_PATCH: 0}

        versions['version'] = versions['version'].apply(lambda x: x.split('-')[0])
        versions = versions.drop_duplicates()

        versions['version_count'] = versions['version'].apply(lambda x: TechLag.convert_version(x))
        versions.sort_values('version_count', ascending=True, inplace=True)

        versions['version_old'] = versions['version'].shift(1)
        versions['release_type'] = versions.apply(lambda d: TechLag.release_type(d['version_old'],
                                                                                 d['version']),
                                                  axis=1)
        versions = versions.query('version_count>' + str(used) + ' and version_count <= ' + str(latest))

        lag = versions.groupby('release_type').count()[['version']].to_dict()['version']

        if RELEASE_MAJOR not in lag.keys():
            lag[RELEASE_MAJOR] = 0
        if RELEASE_MINOR not in lag.keys():
            lag[RELEASE_MINOR] = 0
        if RELEASE_PATCH not in lag.keys():
            lag[RELEASE_PATCH] = 0

        return lag

    @staticmethod
    def parse_url(url):
        """Parse the URL of a remote package.json and return its content.

        :param url: the url of a package.json

        :return: the content of the package.json
        """
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logging.error(error)

        to_json = response.json()
        return to_json

    @staticmethod
    def convert_version(version):
        """Convert version to a numeric value.

        :param version: the version of a package

        :return: a numeric value of the package version
        """
        version = version.split('.')
        major = int(version[0]) * 1000000
        minor = int(version[1]) * 1000
        patch = int(version[2])

        return major + minor + patch

    @staticmethod
    def release_type(old_version, new_version):
        """Determine the type of a release by comparing two versions. The
        outcome can be: major, minor or patch.


        :param old_version: The source version of a package
        :param new_version: The target version of a package

        :return: the type of the release
        """
        old_version = str(old_version).split('.')
        new_version = str(new_version).split('.')

        release = RELEASE_PATCH
        if new_version[0] != old_version[0]:
            release = RELEASE_MAJOR
        elif new_version[1] != old_version[1]:
            release = RELEASE_MINOR

        return release
