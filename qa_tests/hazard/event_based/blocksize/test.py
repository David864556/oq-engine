# Copyright (c) 2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
This is a regression test with the goal of avoiding the reintroduction
of a dependence from the configuration parameter concurrent_tasks.
We use a source model with 398 sources and a single SES.
Due to the distance filtering only 7 sources are relevant, but some
of them are area sources generating a lot of point sources.
We test the independence from the parameter concurrent_tasks.
"""

import os
from nose.plugins.attrib import attr
from qa_tests import _utils as qa_utils
from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based.core import \
    EventBasedHazardCalculator


class EventBasedHazardTestCase(qa_utils.BaseQATestCase):
    DEBUG = False
    # if the test fails and you want to debug it, set this flag:
    # then you will see in /tmp a few files which you can diff
    # to see the problem
    expected_tags = [
        'smlt=00|ses=0001|src=1-1051|i=0002-00',
        'smlt=00|ses=0001|src=2-126|i=0000-00',
        'smlt=00|ses=0001|src=3-102|i=0000-00',
        'smlt=00|ses=0001|src=3-221|i=0001-00',
        'smlt=00|ses=0001|src=398-1620|i=0000-00',
        'smlt=00|ses=0001|src=398-32|i=0000-00',
    ]

    expected_gmfs = '''\
GMFsPerSES(investigation_time=5.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=smlt=00|ses=0001|src=1-1051|i=0002-00
<X=131.00000, Y= 40.00000, GMV=0.0271747>
<X=131.00000, Y= 40.10000, GMV=0.0141840>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=smlt=00|ses=0001|src=2-126|i=0000-00
<X=131.00000, Y= 40.00000, GMV=0.0003261>
<X=131.00000, Y= 40.10000, GMV=0.0002576>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=smlt=00|ses=0001|src=3-221|i=0001-00
<X=131.00000, Y= 40.00000, GMV=0.0005457>
<X=131.00000, Y= 40.10000, GMV=0.0002647>))'''

    @attr('qa', 'hazard', 'event_based')
    def test_4(self):
        tags_4, gmfs_4 = self.run_with_concurrent_tasks(4)
        self.assertEqual(tags_4, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/4-got.txt', 'w').write(gmfs_4)
            open('/tmp/4-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_4, self.expected_gmfs)

    @attr('qa', 'hazard', 'event_based')
    def test_8(self):
        tags_8, gmfs_8 = self.run_with_concurrent_tasks(8)
        self.assertEqual(tags_8, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/8-got.txt', 'w').write(gmfs_8)
            open('/tmp/8-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_8, self.expected_gmfs)

    def run_with_concurrent_tasks(self, n):
        orig = EventBasedHazardCalculator.concurrent_tasks.im_func
        EventBasedHazardCalculator.concurrent_tasks = lambda self: n
        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            tags = models.SESRupture.objects.filter(
                ses__ses_collection__output__oq_job=job
                ).values_list('tag', flat=True)
            # gets the GMFs for all the ruptures in the only existing SES
            [gmfs_per_ses] = list(models.Gmf.objects.get(output__oq_job=job))
        finally:
            EventBasedHazardCalculator.concurrent_tasks = orig
        return map(str, tags), str(gmfs_per_ses)
