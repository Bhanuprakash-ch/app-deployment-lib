#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Helper functions for custom deployment scripts.
"""

import argparse
import json
import os
import getpass
import sys

import requests

from app_deployment_helpers import cf_cli


def upload_to_hdfs(base_url, org_name, local_file_path, title, category='other'):
    """
    Uploads file to HDFS using running uploader application
    (https://github.com/trustedanalytics/uploader)

    Attributes:
        base_url (str): CF API base URL eg. example.com
        org_name (str): GUID of organization in which the file will be uploaded
        local_file_path (str): path to a file which will be uploaded
        title (str): target HDFS file name
    """

    org_guid = cf_cli.get_org_guid(org_name).decode("utf-8")
    uploader_url = "http://hdfs-uploader.{}/rest/upload/{}" \
        .format(base_url, org_guid)

    data = _get_upload_request_body(org_guid, category, title)
    files = {
        'file': open(local_file_path, 'rb')
    }

    response = requests.post(uploader_url, files=files,
                             headers={'Authorization': cf_cli.oauth_token()},
                             data=data)
    response_json = json.loads(response.text)
    return response_json["objectStoreId"] + "/" + response_json[
        "idInObjectStore"]


def get_parser(app_name):
    """
    Creates argument parser for custom deployment scripts

    Attributes:
        app_name (str): name of the application to be deployed
    """
    parser = argparse.ArgumentParser(
        description='Deployment script for {}'.format(app_name))

    parser.add_argument('--base_url', type=str, help='CF API base URL,'
                                                     ' eg. example.com')
    parser.add_argument('--user', type=str, help='CF username')
    parser.add_argument('--password', type=str, help='CF password')
    parser.add_argument('--org', type=str,
                        help='Organization name in which {} will be deployed'
                        .format(app_name))
    parser.add_argument('--space', type=str,
                        help='Space name in which {} will be deployed'.format(
                            app_name))
    parser.add_argument('--app_name', type=str,
                        help='Application name.', const=app_name, nargs="?")
    parser.add_argument('--project_dir', type=str,
                        help='Directory containing application manifest.')
    return parser


def parse_args(app_name):
    """
    Creates basic arguments object for deployment script

    Attributes:
        app_name (str): name of the application to be deployed
    """

    parser = get_parser(app_name)
    return parser.parse_args()


def get_info(args):
    """
    Gets Cloud Foundry target and login information object based on user input

    Attributes:
        args: object with login information which contains following fields:
        base_url, user, password, org, space

    """
    if not args.base_url:
        args.base_url = raw_input('Base URL of TAP domain, eg. example.com: ')
    if not args.user:
        args.user = raw_input('Username: ')
    if not args.password:
        args.password = getpass.unix_getpass()
    if not args.org:
        args.org = raw_input('Organization: ')
    if not args.space:
        args.space = raw_input('Space: ')
    return cf_cli.CfInfo('api.' + args.base_url, args.password, args.user,
                         args.org, args.space)


def prepare_package(work_dir=os.getcwd()):
    """
    Runs Maven command 'mvn clean package' in the provided directory.

    Attributes:
        work_dir (str): directory where 'mvn clean package' will be run,
                        default: current working directory.
    """
    cf_cli.run_command(['mvn', 'clean', 'package'], work_dir=work_dir)


def push(options='', work_dir=os.getcwd()):
    """
    Runs CF CLI command 'cf push' in the provided directory

    Attributes:
        options (str): String with additional options for "cf push" command.
        work_dir (str): directory where 'cf push' command will be run,
                        default: current working directory
    """
    cf_cli.push(work_dir, os.path.join(work_dir, 'manifest.yml'), options)


def get_project_dir():
    """
    Returns directory to application to be deployed
    """
    script_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    return os.path.abspath(os.path.join(script_dir_path, os.path.pardir))


def _get_upload_request_body(org_guid, file_category, file_title, public=False):
    data = {
        'orgUUID': org_guid,
        'category': file_category,
        'title': file_title,
        'publicRequest': public
    }
    return data
