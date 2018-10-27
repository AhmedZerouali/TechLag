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
#     Valerio Cosentino <valcos@bitergia.com>
#

import unittest

from techlag.backends.npm import (Npm,
                                  logger,
                                  DEPENDENCIES_KIND,
                                  DEV_DEPENDENCIES_KIND)
from techlag.errors import ParamsError


class TestNpm(unittest.TestCase):
    """Npm backend tests"""

    def test_init(self):
        """Test whether the attributes are initialized"""

        backend = Npm(package="grunt", version="1.0.0", dep_kind=DEPENDENCIES_KIND)
        self.assertEqual(backend.package, "grunt")
        self.assertEqual(backend.version, "1.0.0")
        self.assertEqual(backend.dep_kind, "dependencies")

        backend = Npm(url="https://raw.githubusercontent.com/jasmine/jasmine/master/package.json",
                      dep_kind=DEV_DEPENDENCIES_KIND)
        self.assertEqual(backend.url, "https://raw.githubusercontent.com/jasmine/jasmine/master/package.json")
        self.assertEqual(backend.dep_kind, DEV_DEPENDENCIES_KIND)

        with self.assertRaises(ParamsError):
            Npm(package="grunt", version="1.0.0")

        with self.assertRaises(ParamsError):
            Npm(package="grunt", version="1.0.0", dep_kind=DEV_DEPENDENCIES_KIND, url="https://...")

        with self.assertRaises(ParamsError):
            Npm(package="grunt", dep_kind=DEV_DEPENDENCIES_KIND, url="https://...")

        with self.assertLogs(logger, level='INFO') as cm:
            Npm(dep_kind="unknown_dev", url="https://...")
            self.assertEqual(cm.output[0], "WARNING:techlag.backends.npm:Unknown dependency kind, "
                                           "set it to dependencies")


if __name__ == "__main__":
    unittest.main()
