# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import os
import unittest

from db.alchemy.db_utils import get_uiapi_writer_session
from db.alchemy import models
from openquake.output.hazard import *
from openquake.shapes import Site
from openquake.utils import round_float

from db_tests import helpers
from tests.utils import helpers as test_helpers


def HAZARD_MAP_DATA(r1, r2):
    data = []
    poes = imls = [0.1] * 20

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data.append((Site(lon, lat),
                         {'IML': 1.9266716959669603,
                          'IMT': 'PGA',
                          'investigationTimeSpan': '50.0',
                          'poE': 0.01,
                          'statistics': 'mean',
                          'vs30': 760.0}))

    return data


def HAZARD_CURVE_DATA(branches, r1, r2):
    data = []
    poes = imls = [0.1] * 20

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            for branch in branches:
                data.append((Site(lon, lat),
                             {'investigationTimeSpan': '50.0',
                              'IMLValues': imls,
                              'PoEValues': poes,
                              'IMT': 'PGA',
                              'endBranchLabel': branch}))

            data.append((Site(lon, lat),
                         {'investigationTimeSpan': '50.0',
                          'IMLValues': imls,
                          'PoEValues': poes,
                          'IMT': 'PGA',
                          'statistics': 'mean'}))

    return data


def GMF_DATA(r1, r2):
    data = {}

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data[Site(lon, lat)] = {'groundMotion': 0.0}

    return data


class HazardCurveDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @test_helpers.timeit
    def test_serialize_small(self):
        data = HAZARD_CURVE_DATA(['1_1', '1_2', '2_2', '2'], 20, 4)

        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            hcw = HazardCurveDBWriter(session, output_path + str(i),
                                       self.job.id)

            # Call the function under test.
            hcw.serialize(data)

        session.commit()


class HazardMapDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @test_helpers.timeit
    def test_serialize_small(self):
        data = HAZARD_MAP_DATA(20, 4)

        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            hmw = HazardMapDBWriter(session, output_path + str(i),
                                    self.job.id)

            # Call the function under test.
            hmw.serialize(data)

        session.commit()


class GMFDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @test_helpers.timeit
    def test_serialize_small(self):
        data = GMF_DATA(20, 4)

        self.job = self.setup_classic_job()
        session = get_uiapi_writer_session()
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            gmfw = GMFDBWriter(session, output_path + str(i), self.job.id)

            # Call the function under test.
            gmfw.serialize(data)

        session.commit()
