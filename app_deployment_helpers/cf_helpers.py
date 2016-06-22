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


def upload_to_hdfs(api_url, org_name, local_file_path, title, category='other'):
    """
    Uploads file to HDFS using running uploader application
    (https://github.com/trustedanalytics/uploader)

    Attributes:
        api_url (str): CF API URL, e.g. http://api.example.com
        org_name (str): GUID of organization in which the file will be uploaded
        local_file_path (str): path to a file which will be uploaded
        title (str): target HDFS file name
    """

    org_guid = cf_cli.get_org_guid(org_name).decode("utf-8")
    uploader_url = "http://hdfs-uploader.{}/rest/upload/{}" \
        .format(_get_base_url(api_url), org_guid)

    data = _get_upload_request_body(org_guid, category, title)
    files = {
        'file': open(local_file_path, 'rb')
    }

    response = requests.post(uploader_url, files=files,
                             headers={'Authorization': cf_cli.oauth_token()},
                             data=data)
    response_json = json.loads(response.text)

    if response.status_code == 201:
        return response_json["objectStoreId"] + "/" \
               + response_json["idInObjectStore"]
    else:
        raise Exception(response_json["message"])


def get_parser(app_name):
    """
    Creates argument parser for custom deployment scripts

    Attributes:
        app_name (str): name of the application to be deployed
    """
    parser = argparse.ArgumentParser(
        description='Deployment script for {}'.format(app_name))

    parser.add_argument('--api_url', type=str, help='CF API URL,'
                        ' e.g. http://api.example.com')
    parser.add_argument('--user', type=str, help='CF username')
    parser.add_argument('--password', type=str, help='CF password')
    parser.add_argument('--org', type=str,
                        help='Organization name in which {} will be deployed'
                        .format(app_name))
    parser.add_argument('--space', type=str,
                        help='Space name in which {} will be deployed'.format(
                            app_name))
    parser.add_argument('--app_name', type=str,
                        help='Application name.', default=app_name)
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
    and information returned by "cf target" command.

    Attributes:
        args: object with login information which contains following fields:
        api_url, user, password, org, space

    """

    current_target = cf_cli.get_current_cli_target()
    arg_info = cf_cli.CfInfo(args.api_url, args.password, args.user, args.org,
                             args.space)
    arg_provided_target = arg_info.get_target_dict(include_password=True)
    new_target = _extract_new_target(current_target, arg_provided_target)
    login_required = _is_login_required(new_target, current_target)
    target_required = _is_target_required(login_required,
                                          new_target, current_target)

    return cf_cli.CfInfo.from_target_dict(new_target, login_required,
                                          target_required)


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


def _get_base_url(api_url):
    base_url = api_url.partition('.')[2]
    if not base_url:
        raise ValueError('API URL format is invalid')
    return base_url


def _extract_new_target(current_target, arg_provided_target):
    new_target = cf_cli.CfInfo.get_empty().get_target_dict()

    for target_param in new_target:
        current = current_target[target_param]
        arg_provided = arg_provided_target[target_param]
        new_target[target_param] = arg_provided if arg_provided else \
            _raw_input_default(target_param, current)

    if not arg_provided_target[cf_cli.CfInfo.PASSWORD_KEY]:
        new_target[cf_cli.CfInfo.PASSWORD_KEY] = getpass.unix_getpass()
    return new_target


def _raw_input_default(message, default_value):
    if default_value:
        message = str.format('{} [{}]', message, default_value)
    message = str.format('{}: ', message)
    input_value = raw_input(message)
    return input_value if input_value else default_value


def _is_login_required(new_target, current_target):
    if new_target[cf_cli.CfInfo.PASSWORD_KEY]:
        return True
    for key in cf_cli.CfInfo.get_login_keys():
        if new_target[key] != current_target[key]:
            return True
    return False


def _is_target_required(login_required, new_target, current_target):
    if login_required:
        return True
    for key in cf_cli.CfInfo.get_org_space_keys():
        if new_target[key] != current_target[key]:
            return True
    return False

