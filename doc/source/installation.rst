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


============
Installation
============


Pre-requisites
--------------

If you are planning to use ``cASO`` for generating accounting records for EGI,
you will need a valid APEL/SSM configuration. Follow the documentation
available at the `EGI FedCloud wiki
<https://wiki.egi.eu/wiki/Fedcloud-tf:WorkGroups:Scenario4#Publishing_Records>`_

Installation
------------

The best way to install cASO and have the most up to date version is using the
repositories and packages provided in the EGI AppDB:

    https://appdb.egi.eu/store/software/caso


Manual installation
*******************

At the command line::

    $ pip install caso

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv caso
    $ pip install caso

CentOS 6
^^^^^^^^

On CentOS 6, you can use Software Collections to install Python 2.7::

    $ yum -y install centos-release-SCL
    $ yum -y install python27

There are also some dependencies of the packages used by ``cASO`` that need to
be installed (``gcc``, ``libffi-devel`` and ``openssl-devel``)::

    $ yum -y install gcc libffi-devel openssl-devel

You can then install ``pip`` for that version of Python and use that to install
``cASO``::

    $ scl enable python27 bash
    $ easy_install-2.7 pip
    $ pip install caso
    $ exit    # this terminates bash with the SCL python2.7

In this case you can later on use ``caso-extract`` with the following command
line::

    $ scl enable python27 caso-extract

Alternatively, if you want to use a virtualenv::

    $ scl enable python27 bash
    $ virtualenv caso
    $ . caso/bin/activate
    $ pip install caso
    $ exit    # this terminates bash with the SCL python2.7

Running from the virtualenv::

    $ scl enable python27 caso/bin/caso-extract
