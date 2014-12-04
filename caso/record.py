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

import json
import pprint


class CloudRecord(object):
    def __init__(self, uuid, site, name, user_id, group_id, fqan,
                 status=None,
                 start_time=None, end_time=None,
                 suspend_duration=None, wall_duration=None, cpu_duration=None,
                 network_type=None, network_in=None, network_out=None,
                 cpu_count=None, memory=None, disk=None,
                 image_id=None, cloud_type=None,
                 storage_record_id=None,
                 vo=None, vo_group=None, vo_role=None,
                 user_dn=None):
        self.uuid = uuid
        self.site = site
        self.name = name
        self.user_id = user_id
        self.group_id = group_id
        self.fqan = fqan
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.suspend_duration = suspend_duration
        self.wall_duration = wall_duration
        self.cpu_duration = cpu_duration
        self.network_type = network_type
        self.network_in = network_in
        self.network_out = network_out
        self.cpu_count = cpu_count
        self.memory = memory
        self.disk = disk
        self.image_id = image_id
        self.cloud_type = cloud_type
        self.storage_record_id = storage_record_id
        self.user_dn = user_dn

    def __repr__(self):
        return pprint.pformat(self.as_dict())

    def as_dict(self):
        d = {'VMUUID': self.uuid,
             'SiteName': self.site,
             'MachineName': self.name,
             'LocalUserId': self.user_id,
             'LocalGroupId': self.group_id,
             'FQAN': self.fqan,
             'Status': self.status,
             'StartTime': self.start_time,
             'EndTime': self.end_time,
             'SuspendDuration': self.suspend_duration,
             'WallDuration': self.wall_duration,
             'CpuDuration': self.cpu_duration,
             'CpuCount': self.cpu_count,
             'NetworkType': self.network_type,
             'NetworkInbound': self.network_in,
             'NetworkOutbound': self.network_out,
             'Memory': self.memory,
             'Disk': self.disk,
             'StorageRecordId': self.storage_record_id,
             'ImageId': self.image_id,
             'CloudType': self.cloud_type,
             'GlobalUserName': self.user_dn, }
        return d

    def as_json(self):
        return json.dumps(self.as_dict())
