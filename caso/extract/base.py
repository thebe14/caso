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

"""Module containing the base class and configuration for all cASO extractors."""

import abc
import json
import warnings

from oslo_config import cfg
from oslo_log import log
import six

opts = [
    cfg.StrOpt("site_name", help="Site name as in GOCDB."),
    cfg.StrOpt(
        "service_name", default="$site_name", help="Service name within the site"
    ),
    cfg.ListOpt(
        "projects",
        default=[],
        deprecated_name="tenants",
        help="List of projects to extract accounting records from. You can "
        "use this option, or add 'caso' tag to the project in Keystone. "
        "Please refer to the documentation for more details.",
    ),
    cfg.StrOpt(
        "caso_tag",
        default="caso",
        help="Tag used to mark a project in Keystone to be extracted by cASO",
    ),
    cfg.StrOpt(
        "mapping_file",
        default="/etc/caso/voms.json",
        deprecated_group="extractor",
        deprecated_for_removal=True,
        deprecated_reason="This option is marked for removal in the next release. "
        "Please see the release notes, and migrate your current configuration "
        "to use the project_mapping file as soon as possible.",
        help="File containing the VO <-> project mapping as used in Keystone-VOMS.",
    ),
]

CONF = cfg.CONF
CONF.register_opts(opts)

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseProjectExtractor(object):
    """Abstract base class for all extractors in cASO."""

    def __init__(self, project):
        """Initialize extractor, loading the VO map."""
        self.project = project

    @property
    def voms_map(self):
        """Get the VO map."""
        # FIXME(remove this)
        try:
            mapping = json.loads(open(CONF.mapping_file).read())
        except ValueError:
            # FIXME(aloga): raise a proper exception here
            raise
        else:
            voms_map = {}
            for vo, vomap in six.iteritems(mapping):
                tenant = vomap.get("tenant", None)
                tenants = vomap.get("tenants", [])
                if tenant is not None:
                    warnings.warn(
                        "Using deprecated 'tenant' mapping, please "
                        "use 'projects' instead",
                        DeprecationWarning,
                    )
                if tenants:
                    warnings.warn(
                        "Using deprecated 'tenants' mapping, please "
                        "use 'projects' instead",
                        DeprecationWarning,
                    )
                tenants.append(tenant)
                projects = vomap.get("projects", tenants)
                if not projects:
                    LOG.warning(f"No project mapping found for VO {vo}")
                for project in projects:
                    voms_map[project] = vo
            return voms_map

    @abc.abstractmethod
    def extract(self, extract_from):
        """Extract records for a project from given date.

        :param extract_from: datetime.datetime object indicating the date to
                             extract records from
        :returns: A list of accounting records

        This method should be overriden in a subclass.
        """
