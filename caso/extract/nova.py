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

import datetime
import json

import dateutil.parser
import keystoneclient.v2_0.client
import novaclient.client
from oslo.config import cfg

from caso.extract import base
from caso import record

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
    cfg.StrOpt('mapping_file',
               default='/etc/caso/voms.json',
               help='File containing the VO <-> tenant mapping for image '
               'lists private to VOs'),
]

CONF = cfg.CONF
CONF.import_opt("site_name", "caso.extract.manager")
CONF.register_opts(opts, group="nova")

openstack_vm_statuses = {
    'active': 'started',
    'build': 'started',
    'confirming_resize': 'started',
    'deleted': 'completed',
    'error': 'error',
    'hard_reboot': 'started',
    'migrating': 'started',
    'password': 'started',
    'paused': 'paused',
    'reboot': 'started',
    'rebuild': 'started',
    'rescue': 'started',
    'resize': 'started',
    'revert_resize': 'started',
    'verify_resize': 'started',
    'shutoff': 'completed',
    'suspended': 'suspended',
    'terminated': 'completed',
    'stopped': 'stopped',
    'saving': 'started',
    'unknown': 'unknown',
}


class OpenStackExtractor(base.BaseExtractor):
    def __init__(self):
        self.user = CONF.nova.user
        self.password = CONF.nova.password
        self.endpont = CONF.nova.endpoint

        try:
            mapping = json.loads(open(CONF.nova.mapping_file).read())
        except ValueError:
            # FIXME(aloga): raise a proper exception here
            raise
        else:
            self.voms_map = {}
            for vo, vomap in mapping.iteritems():
                self.voms_map[vomap["tenant"]] = vo

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

    def _get_keystone_users(self, tenant):
        conn = keystoneclient.v2_0.client.Client(
            username=CONF.nova.user,
            password=CONF.nova.password,
            tenant_name=tenant,
            auth_url=CONF.nova.endpoint,
            insecure=CONF.nova.insecure)
        conn.authenticate()
        return conn

    def extract_for_tenant(self, tenant, lastrun):
        now = datetime.datetime.now()
        end = now + datetime.timedelta(days=1)

        # Try and except here
        conn = self._get_conn(tenant)
        ks_conn = self._get_keystone_users(tenant)
        tenant_id = conn.client.tenant_id
        users = ks_conn.users.list(tenant_id=tenant_id)
        users = {u.id: u.username for u in users}
        servers = conn.servers.list(search_opts={"changes-since": lastrun})
        usages = conn.usage.get(tenant_id, lastrun, end).server_usages
        images = conn.images.list()
        records = {}

        vo = self.voms_map.get(tenant)

        for server in servers:
            status = openstack_vm_statuses.get(server.status.lower(),
                                               "unknown")
            image_id = None
            for image in images:
                if image.id == server.image['id']:
                    image_id = image.metadata.get("vmcatcher_event_ad_mpuri",
                                                  None)
                    break

            if image_id is None:
                image_id = server.image['id']

            r = record.CloudRecord(server.id,
                                   CONF.site_name,
                                   server.name,
                                   server.user_id,
                                   server.tenant_id,
                                   vo,
                                   cloud_type="OpenStack",
                                   status=status,
                                   image_id=image_id,
                                   user_dn=users.get(server.user_id, None))
            records[server.id] = r

        for usage in usages:
            if usage["instance_id"] in records:
                instance_id = usage["instance_id"]
                records[instance_id].memory = usage["memory_mb"]
                records[instance_id].cpu_count = usage["vcpus"]
                records[instance_id].disk = usage["local_gb"]
                records[instance_id].cpu_duration = int(usage["hours"] * 3600)

                started = dateutil.parser.parse(usage["started_at"])
                records[instance_id].start_time = int(started.strftime("%s"))
                if usage.get("ended_at", None) is not None:
                    ended = dateutil.parser.parse(usage['ended_at'])
                    records[instance_id].end_time = int(ended.strftime("%s"))
                    wall = ended - started
                else:
                    wall = now - started

                records[instance_id].wall_duration = int(wall.total_seconds())
