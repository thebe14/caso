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

import novaclient.client
from oslo.config import cfg

from caso.extract import base

opts = [
    cfg.StrOpt('user',
               default='accounting',
               help='User to authenticate as.'),
    cfg.StrOpt('password',
               default='',
               help='Password to authenticate with.'),
    cfg.StrOpt('endpoint',
               default='',
               help='Keystone endpoint to autenticate with.'),
    cfg.BoolOpt('insecure',
                default=False,
                help='Perform an insecure connection (i.e. do '
                'not verify the server\'s certificate. DO NOT USE '
                'IN PRODUCTION'),
]

CONF = cfg.CONF

CONF.register_opts(opts, group="nova")


class OpenStackExtractor(base.BaseExtractor):
    def __init__(self):
        self.user = CONF.nova.user
        self.password = CONF.nova.password
        self.endpont = CONF.nova.endpoint

    def _get_conn(self, tenant):
        client = novaclient.client.get_client_class("2")
        conn = client(
            CONF.nova.user,
            CONF.nova.password,
            tenant,
            CONF.nova.endpoint,
            insecure=CONF.nova.insecure,
            service_type="compute")
        conn.authenticate()
        return conn

    def extract_for_tenant(self, tenant, lastrun):
        # Try and except here
        conn = self._get_conn(tenant)
        servers = conn.servers.list(search_opts={"changes-since": lastrun})
        images = conn.images.list()
