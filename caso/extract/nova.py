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

import dateutil.parser
from dateutil import tz
import novaclient.client
from oslo.config import cfg

from caso.extract import base
from caso import record

CONF = cfg.CONF
CONF.import_opt("site_name", "caso.extract.manager")
CONF.import_opt("user", "caso.extract.base", "extractor")
CONF.import_opt("password", "caso.extract.base", "extractor")
CONF.import_opt("endpoint", "caso.extract.base", "extractor")
CONF.import_opt("insecure", "caso.extract.base", "extractor")


class OpenStackExtractor(base.BaseExtractor):
    def _get_conn(self, tenant):
        client = novaclient.client.get_client_class("2")
        conn = client(
            CONF.extractor.user,
            CONF.extractor.password,
            tenant,
            CONF.extractor.endpoint,
            insecure=CONF.extractor.insecure,
            service_type="compute")
        conn.authenticate()
        return conn

    def extract_for_tenant(self, tenant, lastrun):
        # Some API calls do not expect a TZ, so we have to remove the timezone
        # from the dates. We assume that all dates coming from upstream are
        # in UTC TZ.
        lastrun = lastrun.replace(tzinfo=None)
        now = datetime.datetime.now(tz.tzutc()).replace(tzinfo=None)
        end = now + datetime.timedelta(days=1)

        # Try and except here
        conn = self._get_conn(tenant)
        ks_conn = self._get_keystone_client(tenant)
        users = self._get_keystone_users(ks_conn)
        tenant_id = conn.client.tenant_id
        servers = conn.servers.list(search_opts={"changes-since": lastrun})

        # FIXME(aloga): use start and end from the retreived servers
        aux = conn.usage.get(tenant_id, lastrun, end)
        usages = getattr(aux, "server_usages", [])

        images = conn.images.list()
        records = {}

        vo = self.voms_map.get(tenant)

        for server in servers:
            status = self.vm_status(server.status)
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
            if usage["instance_id"] not in records:
                continue
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
        return records
