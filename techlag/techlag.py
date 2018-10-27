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

import argparse
import importlib
import inspect
import logging
import pkgutil
import re
import requests
import subprocess
import warnings

from techlag.errors import TechLagError

warnings.simplefilter(action='ignore', category=Warning)

RELEASE_MINOR = 'minor'
RELEASE_MAJOR = 'major'
RELEASE_PATCH = 'patch'

logger = logging.getLogger(__name__)


class TechLag:
    """Abstract class for technical lag backends.

    :param package: target package name
    :param version: the target package version
    :param url: the URL of the package to analyze
    """

    version = '0.2.0'

    def __init__(self, package=None, version=None, url=None):
        self.package = package
        self.version = version
        self.url = url

    def analyze(self):
        """Calculate the technical lag for the target package"""

        raise NotImplementedError

    @staticmethod
    def semver(constraint, versions):
        """Get the semantic version of a package.

        :param constraint: version constraint
        :param versions: list package versions

        :return: package versions that meet the constraint
        """
        args = ['semver', '-r', constraint] + list(versions)

        try:
            completed = subprocess.run(args, stdout=subprocess.PIPE)
            output = completed.stdout.decode().strip()
        except TypeError as e:
            logger.error(e)
            raise TechLagError(cause=e)

        if completed.returncode == 0:
            return output.split('\n')
        elif completed.returncode == 1 and not output:
            logger.warning("No package versions found for constraint %s and versions %s", constraint, versions)
            return []
        else:
            logger.error(output)
            raise TechLagError(cause=output)

    @staticmethod
    def convert_version(version):
        """Convert version to a numeric value.

        :param version: the version of a package

        :return: a numeric value of the package version
        """
        major = 0
        minor = 0
        patch = 0

        prog = re.compile("^\d+(\.\d+)*$")
        result = prog.match(version)

        if not result:
            msg = "Impossible to convert version %s" % version
            raise TechLagError(cause=msg)

        groups = version.split('.')
        if len(groups) >= 1:
            major = int(groups[0]) * 1000000
        if len(groups) >= 2:
            minor = int(groups[1]) * 1000
        if len(groups) >= 3:
            patch = int(groups[2])

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

    @staticmethod
    def fetch_from_url(url):
        """Fetch package information from a URL and return its content.

        :param url: the target url

        :return: the content of the url
        """
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logger.error(error)

        to_json = response.json()
        return to_json


class TechLagCommand:
    """Abstract class to run backends from the command line.

    When the class is initialized, it parses the given arguments using
    the defined argument parser on `setup_cmd_parser` method. Those
    arguments will be stored in the attribute `parsed_args`.

    The arguments will be used to inizialize and run the `Backend` object
    assigned to this command. The backend used to run the command is stored
    under `BACKEND` class attributed. Any class derived from this and must
    set its own `Backend` class.

    Moreover, the method `setup_cmd_parser` must be implemented to exectute
    the backend.
    """
    BACKEND = None

    def __init__(self, *args):
        parser = self.setup_cmd_parser()
        self.parsed_args = parser.parse(*args)

    def run(self):
        """Run the technical lag assessment.

        This method runs the backend to analyze the technical lag.
        """
        backend_args = vars(self.parsed_args)
        analyze(self.BACKEND, backend_args)

    @staticmethod
    def setup_cmd_parser():
        raise NotImplementedError


class TechLagCommandArgumentParser:
    """Manage and parse backend command arguments.

    This class defines and parses a set of arguments common to
    backends commands.
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        group = self.parser.add_argument_group('general arguments')
        group.add_argument('-p', '--package', dest='package', default=None,
                           help="package name")
        group.add_argument('-v', '--version', dest='version', default=None,
                           help="package version")
        group.add_argument('-u', '--url', dest='url', default=None,
                           help="package URL")

    def parse(self, *args):
        """Parse a list of arguments.

        Parse argument strings needed to run a backend command. The result
        will be a `argparse.Namespace` object populated with the values
        obtained after the validation of the parameters.

        :param args: argument strings

        :result: an object with the parsed values
        """
        parsed_args = self.parser.parse_args(args)

        return parsed_args


def analyze(backend_class, backend_args):
    """RUn the analysis for given TechLag backend.

    The parameters needed to initialize the `backend` class and
    perform the analysis are given using `backend_args` dict parameter.

    :param backend_class: backend class to analyze the technical lag
    :param backend_args: dict of arguments needed to calculate
    the technical lag

    :returns: a panda DataFrame
    """
    init_args = find_signature_parameters(backend_class.__init__,
                                          backend_args)

    backend = backend_class(**init_args)

    try:
        analysis = backend.analyze()
        print(analysis.to_json(orient='records', lines=True))
    except Exception as e:
        raise e

    return analysis


def find_signature_parameters(callable_, candidates,
                              excluded=('self', 'cls')):
    """Find on a set of candidates the parameters needed to execute a callable.

    Returns a dictionary with the `candidates` found on `callable_`.
    When any of the required parameters of a callable is not found,
    it raises a `AttributeError` exception. A signature parameter
    whitout a default value is considered as required.

    :param callable_: callable object
    :param candidates: dict with the possible parameters to use
        with the callable
    :param excluded: tuple with default parameters to exclude

    :result: dict of parameters ready to use with the callable

    :raises AttributeError: when any of the required parameters for
        executing a callable is not found in `candidates`
    """
    signature_params = inspect_signature_parameters(callable_,
                                                    excluded=excluded)
    exec_params = {}

    add_all = False
    for param in signature_params:
        name = param.name

        if str(param).startswith('*'):
            add_all = True
        elif name in candidates:
            exec_params[name] = candidates[name]
        elif param.default == inspect.Parameter.empty:
            msg = "required argument %s not found" % name
            raise AttributeError(msg, name)
        else:
            continue

    if add_all:
        exec_params = candidates

    return exec_params


def inspect_signature_parameters(callable_, excluded=None):
    """Get the parameters of a callable.

    Returns a list with the signature parameters of `callable_`.
    Parameters contained in `excluded` tuple will not be included
    in the result.

    :param callable_: callable object
    :param excluded: tuple with default parameters to exclude

    :result: list of parameters
    """
    if not excluded:
        excluded = ()

    signature = inspect.signature(callable_)
    params = [
        v for p, v in signature.parameters.items()
        if p not in excluded
    ]
    return params


def find_backends(top_package):
    """Find available backends.

    Look for the TechLag backends and commands under `top_package`
    and its sub-packages. When `top_package` defines a namespace,
    backends under that same namespace will be found too.

    :param top_package: package storing backends

    :returns: a tuple with two dicts: one with `Backend` classes and one
        with `BackendCommand` classes
    """
    candidates = pkgutil.walk_packages(top_package.__path__,
                                       prefix=top_package.__name__ + '.')

    modules = [name for _, name, is_pkg in candidates if not is_pkg]

    return _import_backends(modules)


def _import_backends(modules):
    for module in modules:
        importlib.import_module(module)

    bkls = _find_classes(TechLag, modules)
    ckls = _find_classes(TechLagCommand, modules)

    backends = {name: kls for name, kls in bkls}
    commands = {name: klass for name, klass in ckls}

    return backends, commands


def _find_classes(parent, modules):
    parents = parent.__subclasses__()

    while parents:
        kls = parents.pop()

        m = kls.__module__

        if m not in modules:
            continue

        name = m.split('.')[-1]
        parents.extend(kls.__subclasses__())

        yield name, kls
