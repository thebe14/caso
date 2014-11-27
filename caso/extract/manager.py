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

import os.path

import dateutil.parser
from oslo.config import cfg

opts = [
    cfg.StrOpt('site_name',
               help='Site name as in GOCDB.'),
    cfg.ListOpt('tenants',
                default=[],
                help='List of tenants to extract accounting records from.'),
    cfg.StrOpt('spooldir',
               default='/var/spool/caso',
               help='Spool directory.'),
]

cli_opts = [
    cfg.StrOpt('extract_from',
               help='Extract records from this date. If it is not set, '
               'extract records from last run. If none are set, extract '
               'records from the beginning of time.')
]

CONF = cfg.CONF

CONF.register_opts(opts)
CONF.register_cli_opts(cli_opts)

# NOTE(aloga): this needs to be after the CONF part
from caso.extract import nova
from caso import utils


class ExtractorManager(object):
    def __init__(self):
        self.extractor = nova.OpenStackExtractor()
        utils.makedirs(CONF.spooldir)
        self.last_run_file = os.path.join(CONF.spooldir, "lastrun")

    @property
    def lastrun(self):
        if CONF.extract_from is not None:
            date = CONF.extract_from
        elif os.path.exists(self.last_run_file):
            with open(self.last_run_file, "r") as fd:
                date = fd.read()
        else:
            date = "1970-01-01"

        try:
            date = dateutil.parser.parse(date)
        except Exception:
            # FIXME(aloga): raise a proper exception here
            raise
        return date

    def extract(self):
        # FIXME(aloga): we should lock here
        lastrun = self.lastrun
        for tenant in CONF.tenants:
            self.extractor.extract_for_tenant(tenant, lastrun)
        # FIXME(aloga): save last run
