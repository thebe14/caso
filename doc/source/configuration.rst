..
      Copyright 2015 Spanish National Research Council

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Configuration
*************

Caso configuration
==================

caso uses a config file (default at ``/etc/caso/caso.conf``) with several
sections. A sample file is available at ``etc/caso/caso.conf.sample``.

``[DEFAULT]`` section
---------------------

The ``[DEFAULT]`` section configures the basic behavior of caso. The sample
config file (``/etc/caso/caso.conf.sample``) includes a description
of every option. You should check at least the following options:

* ``extractor`` (default value: ``nova``), specifies which extractor to use for
  getting the data. The following APIs are supported: ``ceilomenter`` and
  ``nova``. Both should generate equivalent information.
* ``site_name`` (default value: ``<None>``). Name of the site as defined in
  GOCDB.
* ``tenants`` (list value, default empty). List of the tenants to extract
  records from.
* ``messengers`` (list, default: ``caso.messenger.noop.NoopMessenger``). List
  of the messengers to publish data to. APEL messenger is:
  ``caso.messenger.ssm.SsmMessager``, LogStash is
  ``caso.messenger.logstash.LogstashMessenger``

``[extractor]`` section
-----------------------

This section specifies the configuration of the extractor (mainly the
credentials to connect to the API. Check the following:

* ``user`` (default: ``accounting``), name of the user. This user needs proper
  permission to query the API for the tenant usages.
* ``password`` (default: None), password of the user.
* ``endpoint`` (default: None), keystone endpoint to authenticate with.
* ``mapping_file`` (default: ``/etc/caso/voms.json``). File containing the
  mapping from VOs to local tenants as configured in Keystone-VOMS. If
  you are running caso on keystone host, it likely
  is ``/etc/keystone/voms.json``. Otherwise, you have to sync this file.

``[ssm]`` section
-----------------

Options defined here configure the SSM messenger. There is only one option
at the moment:

* ``output_path`` (default: ``/var/spool/apel/outgoing/openstack``), directory
  to put the generated SSM records. APEL/SSM should be configured to take
  records from that directory.

``[logstash]`` section
----------------------

Options defined here configure the logstash messenger. Available options:

* ``host`` (default: ``localhost``), host of Logstash server.
* ``port`` (default: ``5000``), Logstash server port.


OpenStack Configuration
=======================

The user configured in the previous section has to be a member of each of the
tenants (another option is to convert that user in an administrator, but the
former option is a safer approach) for which it is extracting the accounting.
Otherwise, ``caso`` will not be able to get the usages and will fail::

    keystone role-create --name accounting
    keystone user-create --name accounting --pass <password>
    # For each of the tenants, add the user with the accounting role
    keystone user-role-add --user accounting --role accounting --tenant <tenant>

Also, this user needs access to Keystone so as to extract the users
information.

* If you are using the V2 identity API, you have to give admin rights to the
  ``accounting`` user, editing the ``/etc/keystone/policy.json`` file and
  replacing the line::

      "admin_required": "role:admin or is_admin:1 or",

  with::

      "admin_required": "role:admin or is_admin:1 or role:accounting",

* If you are using the V3 identity API you can grant the user just the rights
  for listing the users adding the appropriate rules in the
  ``/etc/keystone/policy.json``.
