# -*- coding: utf-8 -*-

# Copyright 2014 Spanish National Research Council (CSIC)
#
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

from __future__ import print_function

import dateutil.parser
from oslo.config import cfg
from oslo.utils import importutils

SUPPORTED_EXTRACTORS = {
    'nova': 'caso.extract.nova.OpenStackExtractor',
    'ceilometer': 'caso.extract.ceilometer.CeilometerExtractor',
}

opts = [
    cfg.StrOpt('site_name',
               help='Site name as in GOCDB.'),
    cfg.ListOpt('tenants',
                default=[],
                help='List of tenants to extract accounting records from.'),
]

cli_opts = [
    cfg.StrOpt('extract_from',
               help='Extract records from this date. If it is not set, '
               'extract records from last run. If none are set, extract '
               'records from the beginning of time.'),
    cfg.StrOpt('extractor',
               choices=SUPPORTED_EXTRACTORS,
               default='nova',
               help=('Which extractor to use for getting the data. '
                     'Only the following middlewares are supported: %s. '
                     'If you do not specify anything, nova will be '
                     'used.' % SUPPORTED_EXTRACTORS.keys())),
]

CONF = cfg.CONF

CONF.register_opts(opts)
CONF.register_cli_opts(cli_opts)


class Manager(object):
    def __init__(self):
        extractor_class = importutils.import_class(
            SUPPORTED_EXTRACTORS[CONF.extractor])
        self.extractor = extractor_class()
        self.records = None

    def _extract(self, extract_from):
        self.records = {}
        for tenant in CONF.tenants:
            records = self.extractor.extract_for_tenant(tenant,
                                                        extract_from)
            print("Extracted %d records for tenant '%s' from %s to now" %
                  (len(records), tenant, extract_from))
            self.records.update(records)

    def get_records(self, lastrun="1970-01-01"):
        extract_from = CONF.extract_from or lastrun

        extract_from = dateutil.parser.parse(extract_from)
        if self.records is None:
            self._extract(extract_from)
        return self.records
