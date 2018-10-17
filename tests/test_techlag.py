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

import unittest

from pytechlag.pytechlag import TechLag
from pytechlag.errors import ParamsError


class TestTechLag(unittest.TestCase):
    """TechLag tests"""

    def test_init_params(self):
        """Test whether the attributes are initialized"""

        tl = TechLag(package="grunt", version="1.0.0", kind="dependencies")
        self.assertEqual(tl.package, "grunt")
        self.assertEqual(tl.version, "1.0.0")
        self.assertEqual(tl.kind, "dependencies")

        tl = TechLag(pjson="https://raw.githubusercontent.com/jasmine/jasmine/master/package.json", kind="devDependencies")
        self.assertEqual(tl.pjson, "https://raw.githubusercontent.com/jasmine/jasmine/master/package.json")
        self.assertEqual(tl.kind, "devDependencies")

        with self.assertRaises(ParamsError):
            TechLag(package="grunt", version="1.0.0")

        with self.assertRaises(ParamsError):
            TechLag(package="grunt", version="1.0.0", kind="devDependencies", pjson="https://...")

        with self.assertRaises(ParamsError):
            TechLag(package="grunt", kind="devDependencies", pjson="https://...")


if __name__ == "__main__":
    unittest.main()
