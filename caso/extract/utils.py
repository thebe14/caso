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


def _inside_interval(start, end, date):
    """Checks if the given date is inside the interval or not"

    :param start: the start date of the interval
    :param end: the end date of the interval
    :param date: the date to check
    :returns: True if it is inside, False otherwise
    """
    return (date >= start and date <= end)


def server_outside_interval(start, end, vm_start, vm_end):
    """Checks if a VM should be included in the record generation or not

    If the VM ended after `end` or it started after `end` and didn't
    finish, it shouldn't be included in the report

    :param start: the start date of the interval
    :param end: the end date of the invertal
    :param vm_start: when the VM started
    :param vm_end: when the VM was terminated
    :returns: True if the VM shouldn't be included, False otherwise
    """
    return (not _inside_interval(start, end, vm_start) or
            (vm_end is not None and not _inside_interval(start, end, vm_end)))
