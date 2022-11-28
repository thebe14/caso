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
import os

from openstackclient.api import object_store_v1
import dateutil.parser
from oslo_config import cfg
from oslo_log import log

from caso.extract import openstack
from caso import record

CONF = cfg.CONF

CONF.import_opt("region_name", "caso.extract.openstack")
CONF.import_opt("site_name", "caso.extract.base")

LOG = log.getLogger(__name__)


class SwiftExtractor(openstack.BaseOpenStackExtractor):
    def __init__(self, project):
        super(SwiftExtractor, self).__init__(project)

        self.swift = self._get_swift_client()


    def _get_swift_client(self):
        session = self._get_keystone_session()
        auth_ref = session.auth.get_auth_ref(session)
        self.endpoint = auth_ref.service_catalog.url_for(
            service_type = "object-store"
        )

        client = object_store_v1.APIv1(
                    session=session,
                    service_type="object-store",
                    endpoint=self.endpoint)

        return client

    def build_record(self, container, extract_from, extract_to):
        user = self.users[container["account"]]

        cont_start = extract_from
        active_duration = (extract_to - cont_start).total_seconds()

        r = record.StorageRecord(
            uuid = os.path.join(self.project_id, container["container"]),
            site_name = CONF.site_name,
            name = container["container"],
            #user_dn=user,
            #user_id=volume.user_id,
            group_id = self.project_id,
            fqan = self.vo,
            compute_service = CONF.service_name,
            #status=volume.status,
            active_duration=active_duration,
            measure_time = self._get_measure_time(),
            start_time = cont_start,
            capacity = container["bytes_used"],
            objects = container["object_count"]
        )

        if container["storage_policy"]:
            r.add_storage_class(container["storage_policy"])

        return r

    def _get_containers(self, extract_from):
        containers = []
        limit = 2
        marker = None

        # Use a marker and iter over results until we do not have more to get
        while True:
            try:
                cont_list = self.swift.container_list(
                    limit=limit,
                    marker=marker)
                
                for cont in cont_list:
                    container = self.swift.container_show(container=cont["name"])
                    containers.append(container)

                if len(cont_list) < limit:
                    break

                marker = cont_list[-1]["name"]
            except Exception as err:
                print(f"Failed to list containers: {err}")
                break

        return containers

    def extract(self, extract_from, extract_to):
        """Extract records for a project from given date querying object store.

        This method will get information from Swift.

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

        containers = self._get_containers(extract_from)

        for cont in containers:
            record = self.build_record(cont, extract_from, extract_to)
            self.str_records[record.uuid] = record

        return list(self.str_records.values())
