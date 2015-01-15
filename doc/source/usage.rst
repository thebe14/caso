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

========
Usage
========

command line
------------

caso provides the ``caso-extract`` command to generate new records from your OpenStack deployment.
``caso-extract -h`` will show a complete list of available arguments.

Use the ``--extract_from`` argument to specify the date from when the records should be extracted. If no
value is set, then caso will extract the records from the last run. If equal to "None", then extract
records from the beggining of time.  If not time zone is specified, UTC will be used.

..
   TODO: add comment on extracting records from the beggining of time.

Running as a cron job
---------------------

..
   TODO: add cron info
