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

import os
import httpretty
import unittest

from techlag.techlag import (logger,
                             TechLag,
                             RELEASE_MAJOR,
                             RELEASE_MINOR,
                             RELEASE_PATCH)
from techlag.errors import TechLagError


def read_file(filename, mode='r'):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), mode) as f:
        content = f.read()
    return content


class TestTechLag(unittest.TestCase):
    """TechLag tests"""

    def test_init(self):
        """Test whether the attributes are initialized"""

        tl = TechLag(url="https://...")
        self.assertIsNone(tl.package)
        self.assertIsNone(tl.version)
        self.assertEqual(tl.url, "https://...")

        tl = TechLag(package="grunt", version="1.0.0", url="https://...")
        self.assertEqual(tl.package, "grunt")
        self.assertEqual(tl.version, "1.0.0")
        self.assertEqual(tl.url, "https://...")

    def test_analyze(self):
        """Test whether a NotImplementedError is thrown"""

        tl = TechLag(package="grunt", version="1.0.0", url="https://...")
        with self.assertRaises(NotImplementedError):
            tl.analyze()

    def test_semserver(self):
        """Test whether semserver properly works"""

        versions = TechLag.semver(">1.2.3", ["1.1.0", "1.2.0", "1.3.0", "1.4.0"])
        self.assertEqual(["1.3.0", "1.4.0"], versions)

        with self.assertLogs(logger, level='INFO') as cm:
            versions = TechLag.semver(">1.2.3", ["1.1.0", "1.2.0"])
            self.assertEqual([], versions)

            self.assertEqual(cm.output[0], "WARNING:techlag.techlag:No package versions found for constraint "
                                           ">1.2.3 and versions ['1.1.0', '1.2.0']")

        with self.assertRaises(TechLagError):
            _ = TechLag.semver(None, [])

    def test_convert_version(self):
        """Test whether convert_version properly works"""

        value = TechLag.convert_version("1.1.1")
        self.assertEqual(value, 1001001)

        value = TechLag.convert_version("1.1")
        self.assertEqual(value, 1001000)

        value = TechLag.convert_version("1")
        self.assertEqual(value, 1000000)

        with self.assertRaises(TechLagError):
            _ = TechLag.convert_version("")

    def test_release_type(self):
        """Test whether release_type properly works"""

        release = TechLag.release_type("1.1.0", "2.2.1")
        self.assertEqual(release, RELEASE_MAJOR)

        release = TechLag.release_type("1.1.0", "1.2.1")
        self.assertEqual(release, RELEASE_MINOR)

        release = TechLag.release_type("1.1.1", "1.1.2")
        self.assertEqual(release, RELEASE_PATCH)

    @httpretty.activate
    def test_fetch_from_url(self):
        """Test whether fetch_from_url properly works"""

        url = "https://raw.githubusercontent.com/jasmine/jasmine/master/package.json"
        content = read_file('data/package.json', 'rb')
        httpretty.register_uri(httpretty.GET,
                               url,
                               body=content,
                               status=200)

        response = TechLag.fetch_from_url(url)
        self.assertEqual(response['name'], 'jasmine-core')
        self.assertEqual(response['version'], '3.2.1')
        self.assertIn('devDependencies', response)


if __name__ == "__main__":
    unittest.main()
