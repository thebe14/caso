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

import datetime
import json

import ceilometerclient.client
import dateutil.parser
import glanceclient.client
import keystoneclient.v2_0.client
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
CONF.register_opts(opts, group="ceilometer")

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


class CeilometerExtractor(base.BaseExtractor):
    def __init__(self):
        # XXX: enolfc this is copying everything
        #      should be put in a common base class
        self.user = CONF.ceilometer.user
        self.password = CONF.ceilometer.password
        self.endpoint = CONF.ceilometer.endpoint

        try:
            mapping = json.loads(open(CONF.ceilometer.mapping_file).read())
        except ValueError:
            # FIXME(aloga): raise a proper exception here
            raise
        else:
            self.voms_map = {}
            for vo, vomap in mapping.iteritems():
                self.voms_map[vomap["tenant"]] = vo

    def _get_ceilometer_client(self, tenant):
        return ceilometerclient.client.get_client(
            '2',
            os_auth_url=self.endpoint,
            os_username=self.user,
            os_password=self.password,
            os_tenant_name=tenant,
            insecure=CONF.ceilometer.insecure)

    def _get_keystone_client(self, tenant):
        client = keystoneclient.v2_0.client.Client(
            username=CONF.ceilometer.user,
            password=CONF.ceilometer.password,
            tenant_name=tenant,
            auth_url=CONF.ceilometer.endpoint,
            insecure=CONF.ceilometer.insecure)
        client.authenticate()
        return client

    def _get_glance_client(self, ks_client):
        glance_ep = ks_client.service_catalog.get_endpoints(
            service_type='image',
            endpoint_type='public')
        glance_url = glance_ep['image'][0]['publicURL']
        # glance client does not seem to work with user/password
        return glanceclient.client.Client(
            '2',
            glance_url,
            token=ks_client.auth_token,
            insecure=CONF.ceilometer.insecure)

    def _build_query(self, project_id=None, start_date=None, end_date=None):
        q = []
        if project_id:
            q.append({'field': 'project_id', 'value': project_id})
        if start_date:
            q.append({'field': 'timestamp', 'op': 'ge', 'value': start_date})
        if end_date:
            q.append({'field': 'timestamp', 'op': 'le', 'value': end_date})
        return q

    def _fill_metric(self, metric_name, samples, records,
                     get_id=lambda s: s.resource_id,
                     unit_conv=lambda v: v):
        """Fills a given metric in the records

        get_id is a function that gets the instance id from the sample
        conv is a function that converts the metric to the units
             requested by the usage record

        """

        instance_timestamps = {}
        the_past = datetime.datetime(1, 1, 1)
        for sample in samples:
            instance_id = get_id(sample)
            r = records.get(instance_id)
            if not r:
                # XXX: there is a sample for a VM that has no instance sample?
                print("VM with some usage info but no instance metric?!")
                continue
            instance_ts = instance_timestamps.get(instance_id, the_past)
            sample_ts = dateutil.parser.parse(sample.timestamp)
            if sample_ts > instance_ts:
                r.__dict__[metric_name] = unit_conv(sample.counter_volume)
                instance_timestamps[instance_id] = sample_ts

    def _fill_cpu_metric(self, cpu_samples, records):
        self._fill_metric('cpu_duration', cpu_samples, records,
                          # convert ns to s
                          unit_conv=lambda v: int(v / 1e9))

    def _fill_net_metric(self, metric_name, net_samples, records):
        self._fill_metric(metric_name, net_samples, records,
                          lambda s: s.resource_metadata.get('instance_id'),
                          # convert bytes to GB
                          unit_conv=lambda v: int(v / 2 ** 30))

    def _get_time_field(self, metadata, fields=[]):
        for f in fields:
            t = metadata.get(f, None)
            if t:
                dateutil.parser.parse(t).replace(tzinfo=None)
        else:
            return None

    def _build_record(self, instance, users, vo, images, now):
        metadata = instance.resource_metadata
        status = openstack_vm_statuses.get(metadata.get('state',
                                                        '').lower(),
                                           'unknwon')
        instance_image_id = metadata.get('image.id')
        if not instance_image_id:
            instance_image_id = metadata.get('image_meta.base_image_ref')
        image_id = None
        for image in images:
            if instance_image_id == image.id:
                image_id = image.get('vmcatcher_event_ad_mpuri', None)
                break
        else:
            image_id = instance_image_id
        r = record.CloudRecord(instance.resource_id,
                               CONF.site_name,
                               metadata.get('display_name'),
                               instance.user_id,
                               instance.project_id,
                               vo,
                               cpu_count=metadata.get('vcpus'),
                               memory=metadata.get('memory_gb'),
                               disk=metadata.get('disk_gb'),
                               # this should contain "caso ceilometer vX"
                               cloud_type="OpenStack",
                               status=status,
                               image_id=image_id,
                               user_dn=users.get(instance.user_id, None))

        start_time = self._get_time_field(metadata,
                                          ('launched_at', 'created_at'))
        end_time = self._get_time_field(metadata,
                                        ('terminated_at', 'deleted_at'))
        if start_time:
            r.start_time = int(start_time.strftime("%s"))
            if end_time:
                r.end_time = int(end_time.strftime("%s"))
                wall = end_time - start_time
                r.wall_duration = int(wall.total_seconds())
            else:
                wall = now - start_time
                r.wall_duration = int(wall.total_seconds())
        return r

    def extract_for_tenant(self, tenant, lastrun):
        now = datetime.datetime.now().replace(tzinfo=None)

        # Try and except here
        # Getting clients
        ks_client = self._get_keystone_client(tenant)
        client = self._get_ceilometer_client(tenant)
        glance_client = self._get_glance_client(ks_client)

        # users
        tenant_id = ks_client.tenant_id
        users = ks_client.users.list(tenant_id=tenant_id)
        users = {u.id: u.name for u in users}

        search_query = self._build_query(tenant_id, lastrun)
        instances = client.samples.list('instance', search_query)

        # XXX should we query glance for every VM or not?
        images = list(glance_client.images.list())

        records = {}

        vo = self.voms_map.get(tenant)

        for instance in instances:
            # it seems the only event type with relevant metadata is
            # 'compute.instance.exists'
            ev_type = instance.resource_metadata.get('event_type', None)
            if ev_type != 'compute.instance.exists':
                continue
            # this assumes that records are returned with decreasing timestamp
            # so the status and dates are the last ones.
            if instance.resource_id in records:
                continue
            records[instance.resource_id] = self._build_record(instance,
                                                               users,
                                                               vo,
                                                               images,
                                                               now)

        cpu = client.samples.list(meter_name='cpu', q=search_query)
        self._fill_cpu_metric(cpu, records)
        net_in = client.samples.list(meter_name='network.incoming.bytes',
                                     q=search_query)
        self._fill_net_metric('network_in', net_in, records)
        net_out = client.samples.list(meter_name='network.outcoming.bytes',
                                      q=search_query)
        self._fill_net_metric('network_out', net_out, records)

        return records
