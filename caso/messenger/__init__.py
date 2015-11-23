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

from oslo_config import cfg
from oslo_log import log
import six

from caso import loadables

opts = [
    cfg.ListOpt('messengers',
                default=['caso.messenger.noop.NoopMessenger'],
                help='List of messenger that will dispatch records.'),
]

CONF = cfg.CONF

CONF.register_opts(opts)

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseMessenger(object):
    @abc.abstractmethod
    def push(self, records):
        """Push the records."""


class Manager(loadables.BaseLoader):
    def __init__(self):
        super(Manager, self).__init__(BaseMessenger)
        self.messengers = [i()
                           for i in self.get_matching_classes(CONF.messengers)]

    def push_to_all(self, records):
        for m in self.messengers:
            try:
                m.push(records)
            except Exception as e:
                # Capture exception so that we can continue working
                LOG.error(e)
