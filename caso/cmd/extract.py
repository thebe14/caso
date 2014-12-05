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

import os
import sys

from oslo.config import cfg

import caso.config
from caso.extract import manager

CONF = cfg.CONF


def main():
    default_config_files = ["/etc/caso.conf",
                            "etc/caso.conf",
                            os.path.expanduser('~/.caso.conf')]
    default_config_files = []
    caso.config.parse_args(sys.argv,
                           default_config_files=default_config_files)
    extractor = manager.ExtractorManager()
    extractor.extract()


if __name__ == "__main__":
    main()
