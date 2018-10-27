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
#     Valerio Cosentino <valcos@bitergia.com>
#

import logging
import pandas as pd
from urllib.parse import urljoin

from techlag.errors import (ParamsError,
                            TechLagError)
from techlag.techlag import (TechLag,
                             TechLagCommand,
                             TechLagCommandArgumentParser,
                             RELEASE_PATCH,
                             RELEASE_MINOR,
                             RELEASE_MAJOR)

DEPENDENCIES_KIND = "dependencies"
DEV_DEPENDENCIES_KIND = "devDependencies"
DEPENDENCIES = [DEPENDENCIES_KIND, DEV_DEPENDENCIES_KIND]

NPM_URL = 'http://registry.npmjs.org'

logger = logging.getLogger(__name__)


class Npm(TechLag):
    """Npm backend.

    This class allows to calculate the technical lag for Npm packages. It can be
    executed in two ways, either:
        - the package name, version and kind of dependencies to analyze
        - the URI of a package.json plus the kind of dependencies to analyze
    Possible examples of executions are:
        - Npm(pjson=https://raw.githubusercontent.com/jasmine/jasmine/master/package.json,
                  kind='devDependencies")
        - Npm(package="grunt", version="1.0.0", kind="dependencies")

    :param package: target package name
    :param version: the target package version
    :param url: the URL of the package.json
    :param dep_kind: kind of dependencies to analyze
    """

    version = '0.1.0'

    def __init__(self, package=None, version=None, url=None, dep_kind=None):
        super().__init__(package, version, url)

        if not dep_kind and not url:
            raise ParamsError(cause="kind of dependencies cannot be null")

        if package and version and dep_kind:
            if url:
                raise ParamsError(cause="too many parameters passed, "
                                        "set <package, version, dep_kind> or <url>")

        if url:
            if package or version:
                raise ParamsError(cause="too many parameters passed, "
                                        "set <package, version, dep_kind> or <url>")

        if dep_kind not in DEPENDENCIES:
            logger.warning("Unknown dependency kind, set it to %s", DEPENDENCIES_KIND)
            dep_kind = DEPENDENCIES_KIND

        self.dep_kind = dep_kind

    def analyze(self):
        """Calculate the technical lag for the target package"""

        if self.url:
            json = TechLag.fetch_from_url(self.url)
        else:
            version = self.semver(self.version, self.get_versions(self.package).version.tolist())[-1]
            url = urljoin(NPM_URL, self.package + '/' + version)
            json = TechLag.fetch_from_url(url)

        if self.dep_kind not in json:
            msg = "%s package.json doesn't contain information about %s" % (json['name'], self.dep_kind)
            logger.error(msg)
            raise TechLagError(cause=msg)

        dependencies = self.get_dependencies(json, self.dep_kind)
        result = self.calculate_lags(dependencies)

        return result

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

            latest = self.semver('*', list_versions.version.tolist())[-1]
            used = self.semver(dependencies.iloc[row].constraint, list_versions.version.tolist())[-1]

            lag = self.compute_lag(list_versions, used, latest)

            dependencies.latest_version.iloc[row] = latest
            dependencies.used_version.iloc[row] = used
            dependencies.major_lag.iloc[row] = lag[RELEASE_MAJOR]
            dependencies.minor_lag.iloc[row] = lag[RELEASE_MINOR]
            dependencies.patch_lag.iloc[row] = lag[RELEASE_PATCH]

        return dependencies

    @staticmethod
    def get_dependencies(package, kind):
        """Get the dependencies of a given kind for a target package.json.

        :param package: package information in JSON format
        :param kind: kind of dependencies to analyze

        :return: a pandas data frame with the dependencies
        """
        dependencies = (pd.DataFrame({'dependency': list(package[kind].keys()),
                                      'constraint': list(package[kind].values()),
                                      'kind': kind}))

        return dependencies

    @staticmethod
    def get_versions(package):
        """Get the version of a given package.

        :param package: target package name

        :return: pandas data frame of package versions
        """
        url = urljoin(NPM_URL, package)
        versions = TechLag.fetch_from_url(url)['time']
        versions.pop('modified')
        versions.pop('created')
        versions = (pd.DataFrame({'version': list(versions.keys()),
                                  'date': list(versions.values()),
                                  'package': package}))

        return versions

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


class NpmCommand(TechLagCommand):
    """Class to run Npm backend from the command line."""

    BACKEND = Npm

    @staticmethod
    def setup_cmd_parser():
        """Returns the GitLab argument parser."""

        parser = TechLagCommandArgumentParser()

        # Npm options
        group = parser.parser.add_argument_group('Npm arguments')
        group.add_argument('-k', '--dependencies-kind', dest='dep_kind',
                           help="Kind of dependencies to analyze: devDependencies or dependencies")

        return parser
