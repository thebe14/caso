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

import operator

import cinderclient.v3.client
import dateutil.parser
from oslo_config import cfg
from oslo_log import log

from caso.extract import openstack
from caso import record

CONF = cfg.CONF

CONF.import_opt("region_name", "caso.extract.openstack")
CONF.import_opt("site_name", "caso.extract.base")

LOG = log.getLogger(__name__)


class CinderExtractor(openstack.BaseOpenStackExtractor):
    def __init__(self, project):
        super(CinderExtractor, self).__init__(project)

        self.cinder = self._get_cinder_client()

    def _get_cinder_client(self):
        session = self._get_keystone_session()
        client = cinderclient.v3.client.Client(session=session)
        return client

    def build_record(self, volume, extract_from, extract_to):
        user = self.users[volume.user_id]

        vol_created = volume.__getattr__('created_at')
        vol_start = None
        if not vol_created:
            vol_start = extract_from
        else:
            vol_start = dateutil.parser.parse(vol_created)
            if (vol_start < extract_from):
                vol_start = extract_from    

        active_duration = (extract_to - vol_start).total_seconds()
        allocated = int(volume.size * 1073741824), # 1 GiB = 2^30

        r = record.StorageRecord(
            uuid = volume.id,
            site_name = CONF.site_name,
            name = volume.name,
            user_id = volume.user_id,
            group_id = self.project_id,
            fqan = self.vo,
            service = CONF.service_name,
            status = volume.status,
            active_duration = int(active_duration),
            measure_time = self._get_measure_time(),
            start_time = vol_start,
            allocated = allocated,
            capacity = allocated,
            user_dn = user,
            storage_media = volume.volume_type
        )

        if r.site_name == r.service:
            r.service += ":Cinder"

        if volume.status == "in-use":
            r.attached_to = volume.attachments[0]["server_id"]
            attached_at = volume.attachments[0]["attached_at"]
            attached_at = dateutil.parser.parse(attached_at)
            if (attached_at < extract_from):
                attached_at = extract_from
            attacht = (extract_to - attached_at).total_seconds()
            r.attached_duration = int(attacht)

        if volume.encrypted:
            r.add_storage_class("encrypted")

        return r

    def _get_volumes(self, extract_from):
        volumes = []
        limit = 200
        marker = None
        # Use a marker and iter over results until we do not have more to get
        while True:
            try:
                aux = self.cinder.volumes.list(
                    limit=limit,
                    marker=marker
                )
                
                count = len(aux)
                if count > 0:
                    volumes.extend(aux)

                if count < limit:
                    break

                last_vol = aux[-1]
                marker = last_vol.id
            except Exception as err:
                print(f"Failed to list volumes: {err}")
                break

        volumes = sorted(volumes, key=operator.attrgetter("created_at"))
        return volumes

    def extract(self, extract_from, extract_to):
        """Extract records for a project from given date querying block store.

        This method will get information from Cinder.

        :param extract_from: datetime.datetime object indicating the date to
                             extract records from
        :param extract_to: datetime.datetime object indicating the date to
                           extract records to
        :returns: A list of storage records
        """
        # Some API calls do not expect a TZ, so we have to remove the timezone
        # from the dates. We assume that all dates coming from upstream are
        # in UTC TZ.
        extract_from = extract_from.replace(tzinfo=None)
        extract_to = extract_to.replace(tzinfo=None)

        # Our storage records
        self.str_records = {}

        volumes = self._get_volumes(extract_from)

        for vol in volumes:
            record = self.build_record(vol, extract_from, extract_to)
            self.str_records[vol.uuid] = record

        return list(self.str_records.values())
