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

import abc
import json
import warnings

import dirq.QueueSimple
from oslo_config import cfg
from oslo_log import log
import six
import xml.etree.ElementTree as ET

import caso.exception
import caso.messenger
import caso.record
from caso import utils

LOG = log.getLogger(__name__)

opts = [
    cfg.StrOpt('output_path',
               default='/var/spool/apel/outgoing/openstack',
               help="Directory to put the generated SSM records."),
    cfg.IntOpt('max_size',
               default=100,
               help="Maximum number of records to send per message"),
]

CONF = cfg.CONF

CONF.register_opts(opts, group="ssm")


__all__ = ["SSMMessengerV02", "SSMMessengerV04"]


@six.add_metaclass(abc.ABCMeta)
class _SSMBaseMessenger(caso.messenger.BaseMessenger):

    def __init__(self):
        try:
            utils.makedirs(CONF.ssm.output_path)
        except Exception as err:
            LOG.error(f"Failed to create path {CONF.ssm.output_path} because {err}")
            

    def push_compute_message(self, queue, entries):
        message = f"APEL-cloud-message: v{self.compute_version}\n"
        aux = "%%\n".join(entries)
        message += f"{aux}\n"
        message = message.encode("utf-8")
        queue.add(message)

    def push_json_message(self, queue, entries, msg_type, version):
        message = {
            "Type": msg_type,
            "Version": version,
            "UsageRecords": [json.loads(r) for r in entries],
        }
        queue.add(json.dumps(message))

    def push_ip_message(self, queue, entries):
        self.push_json_message(queue, entries, "APEL Public IP message",
                               self.ip_version)

    def push_acc_message(self, queue, entries):
        self.push_json_message(queue, entries, "APEL-accelerator-message",
                               self.acc_version)

    def push_storage_message(self, queue, entries):
        ns = {
            "xmlns:sr": "http://eu-emi.eu/namespaces/2011/02/storagerecord"
        }
        root = ET.Element("sr:StorageUsageRecords", attrib=ns)
        for record in entries:
            sr = ET.SubElement(root, "sr:StorageUsageRecord")
            ET.SubElement(
                sr,
                "sr:RecordIdentity",
                attrib={
                    "sr:createTime": record.measure_time.isoformat(),
                    "sr:recordId": str(record.uuid),
                },
            )
            ET.SubElement(sr, "sr:StorageSystem").text = record.service
            ET.SubElement(sr, "sr:Site").text = record.site_name

            if any((record.user_id, record.user_dn)):
                subject = ET.SubElement(sr, "sr:SubjectIdentity")
                if record.user_id:
                    ET.SubElement(subject, "sr:LocalUser").text = record.user_id
                if record.group_id:
                    ET.SubElement(subject, "sr:LocalGroup").text = record.group_id
                if record.user_dn:
                    ET.SubElement(subject, "sr:UserIdentity").text = record.user_dn
                if record.fqan:
                    ET.SubElement(subject, "sr:Group").text = record.fqan

            ET.SubElement(sr,
                          "sr:StartTime").text = record.start_time.isoformat()
            ET.SubElement(sr,
                          "sr:EndTime").text = record.measure_time.isoformat()
            if record.storage_media:
                ET.SubElement(sr, "sr:StorageMedia").text = record.storage_media
            if record.storage_class:
                ET.SubElement(sr, "sr:StorageClass").text = record.storage_class
            ET.SubElement(sr, "sr:ResourceCapacityUsed").text = str(record.capacity)
            if record.allocated:
                ET.SubElement(sr, "sr:ResourceCapacityAllocated").text = str(record.allocated)
            if record.objects:
                ET.SubElement(sr, "sr:FileCount").text = str(record.objects)
        queue.add(ET.tostring(root))

    def push(self, records):
        if not records:
            return

        entries_cloud = []
        entries_ip = []
        entries_acc = []
        entries_storage = []
        opts = {
            "by_alias": True,
            "exclude_unset": True,
            "exclude_none": True,
        }
        for record in records:
            if isinstance(record, caso.record.CloudRecord):
                aux = ""
                for k, v in six.iteritems(record.dict(**opts)):
                    if v is not None:
                        aux += f"{k}: {v}\n"
                entries_cloud.append(aux)
            elif isinstance(record, caso.record.IPRecord):
                entries_ip.append(record.json(**opts))
            elif isinstance(record, caso.record.AcceleratorRecord):
                entries_acc.append(record.json(**opts))
            elif isinstance(record, caso.record.StorageRecord):
                entries_storage.append(record)
            else:
                raise caso.exception.CasoException("Unexpected record type!")

        # FIXME(aloga): try except here
        queue = dirq.QueueSimple.QueueSimple(CONF.ssm.output_path)

        # Divide message into smaller chunks as per GGUS #143436
        # https://ggus.eu/index.php?mode=ticket_info&ticket_id=143436
        for i in range(0, len(entries_cloud), CONF.ssm.max_size):
            entries = entries_cloud[i:i + CONF.ssm.max_size]
            self.push_compute_message(queue, entries)

        for i in range(0, len(entries_ip), CONF.ssm.max_size):
            entries = entries_ip[i:i + CONF.ssm.max_size]
            self.push_ip_message(queue, entries)

        for i in range(0, len(entries_acc), CONF.ssm.max_size):
            entries = entries_acc[i:i + CONF.ssm.max_size]
            self.push_acc_message(queue, entries)

        for i in range(0, len(entries_storage), CONF.ssm.max_size):
            entries = entries_storage[i:i + CONF.ssm.max_size]
            self.push_storage_message(queue, entries)


class SSMMessengerV02(_SSMBaseMessenger):
    def __init__(self):
        msg = ("Using deprecated caso.messenger.ssm.SSMMessengerV02, "
               "please use caso.messenger.ssm.SSMMessengerV04 instead.")
        warnings.warn(msg, DeprecationWarning)
        super(SSMMessengerV02, self).__init__()


class SSMMessengerV04(_SSMBaseMessenger):
    def __init__(self):
        super(SSMMessengerV04, self).__init__()
