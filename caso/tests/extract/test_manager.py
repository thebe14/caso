# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Tests for `caso.extract.manager` module.
"""

import uuid

import dateutil.parser
import mock

from caso.extract import manager
from caso.tests import base


class TestCasoManager(base.TestCase):
    def setUp(self):
        super(TestCasoManager, self).setUp()
        manager.SUPPORTED_EXTRACTORS = {"foo": "foo.Bar"}
        self.flags(extractor="foo")
        self.p_extractor = mock.patch.dict('sys.modules',
                                           {'foo': mock.MagicMock()})
        self.p_extractor.start()
        self.manager = manager.Manager()

    def tearDown(self):
        self.p_extractor.stop()

        super(TestCasoManager, self).tearDown()

    def test_extract_empty_tenants(self):
        self.flags(tenants=[])

        with mock.patch.object(self.manager.extractor,
                               "extract_for_tenant") as m:
            self.manager._extract("1999-12-19")
            self.assertFalse(m.called)
        self.assertEqual({}, self.manager.records)

    def test_extract(self):
        records = {uuid.uuid4().hex: None}
        self.flags(tenants=["bazonk"])

        with mock.patch.object(self.manager.extractor,
                               "extract_for_tenant") as m:
            m.return_value = records
            self.manager._extract("1999-12-19")
            m.assert_called_once_with("bazonk", "1999-12-19")
        self.assertEqual(records, self.manager.records)

    def test_get_records_wrong_extract_from(self):
        self.flags(extract_from="1999-12-99")
        self.assertRaises(ValueError,
                          self.manager.get_records)

    def test_get_records_wrong_lastrun(self):
        self.assertRaises(ValueError,
                          self.manager.get_records,
                          lastrun="1999-12-99")

    def test_get_records_with_extract_from(self):
        date = "1999-12-11"
        dt = dateutil.parser.parse(date)
        self.flags(extract_from=date)
        with mock.patch.object(self.manager, "_extract") as m:
            self.manager.get_records()
            m.assert_called_with(dt)

    def test_get_records_with_lastrun(self):
        date = "1999-12-11"
        dt = dateutil.parser.parse(date)
        with mock.patch.object(self.manager, "_extract") as m:
            self.manager.get_records(lastrun=date)
            m.assert_called_with(dt)
