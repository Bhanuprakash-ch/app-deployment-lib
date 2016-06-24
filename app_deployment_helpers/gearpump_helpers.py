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
Helper functions for deploying apps to Gearpunp instance.
"""
import os
import pickle
import json
import requests
import yaml
from app_deployment_helpers import cf_api

GEARPUMP_COOKIE_NAME = 'gpcookie'
REQUEST_BODY_FILE = 'request_body'

def prepare_deploy_req_data(service_instances, users_args):
    """
    Prepares data for <gearpump_instance>/api/v1.0/master/submitapp REST
    request basing on data retrieved from CF API

    Attributes:
        service_instances (list): list of service instances which should be
        bound with deployed app
        users_args (dict): argument-value pairs to be added in user arguments'
        request body section
    """
    json_data = {}
    for instance in service_instances:
        instance_properties, instance_credentials = \
            get_service_instance_data(instance)
        instance_body = [{
            "label" : instance_properties['label'],
            "name" : instance,
            "plan" : instance_properties['plan'],
            "tags" : instance_properties['tags'],
            "credentials" : instance_credentials
        }]
        json_data[instance_properties['label']] = instance_body

    json_data = _encode_json_to_utf8(_add_user_args_section(json_data, users_args))
    return json_data

def _add_user_args_section(body_data_json, users_args):
    body_data_json['usersArgs'] = users_args
    return body_data_json

def get_service_instance_data(instance_name):
    """
    Gets data (including credentials) for particular service instance

    Attributes:
        instance_name (str): service-instance name
    """
    instance_data_for_req = {}
    instance_data = cf_api.get_service_instance(instance_name)['entity']
    service_plan_data = cf_api.cf_curl_get(instance_data['service_plan_url'])['entity']
    service_url = service_plan_data['service_url']
    service_data = cf_api.cf_curl_get(service_url)['entity']
    instance_data_for_req['plan'] = service_plan_data['name']
    instance_data_for_req['tags'] = instance_data['tags']
    instance_data_for_req['label'] = service_data['label']
    instance_key_data = cf_api.get_temporary_key_data(instance_name)['entity']['credentials']
    return instance_data_for_req, instance_key_data


def get_jar_file_name():
    """
    Gets file name of the jar to be deployed.

    """
    for dir_file in os.listdir("../target"):
        if dir_file.endswith("-with-dependencies.jar"):
            return dir_file

def gearpump_login(gearpump_url, username, password):
    """
    Logs-in to Gearpump using its REST API and saves login cookie to allow
    sending next API requests

    Attributes:
        gearpump_url (str): url of gearpump service instance
        username: Gearpump service admin
        password: Gearpump service admin's password
    """
    body = {
        'username': username,
        'password': password
    }
    gearpump_login_url = "http://" + gearpump_url + "/login"
    response = requests.post(gearpump_login_url, data=body)
    save_to_file(response.cookies, GEARPUMP_COOKIE_NAME)
    return response.text

def save_to_file(data, filename):
    """
    Serializes data

    Attributes:
        data (obj): data to serialize
        filename (str): name of the file to store data
    """
    with open(filename, 'wb') as tmp_file:
        pickle.dump(data, tmp_file)

def load_file(filename):
    """
    Loads file from disk

    Attributes:
        filename (str): name of the file to load
    """
    with open(filename, 'rb') as tmp_file:
        return pickle.load(tmp_file)

def delete_file(filename):
    """
    Deletes file from disk

    Attributes:
        filename (str): name of the file to be deleted
    """
    os.remove(filename)

def deploy_to_gearpump(gearpump_url, local_file_path, users_args, bound_instances):
    """
    Uploads file to Gearpump using its REST API

    Attributes:
        gearpump_url (str): url of gearpump service instance
        local_file_path (str): path to a jar file to be deployed
    """
    gearpump_deploy_url = "http://" + gearpump_url + "/api/v1.0/master/submitapp"
    deploy_request_data = prepare_deploy_req_data(bound_instances, users_args)

    with open(REQUEST_BODY_FILE, "w") as text_file:
        text_file.write("tap=" + str(deploy_request_data).replace("'", "\""))

    files = {
        'jar': open(local_file_path, 'rb')
    }
    data = {
        'configstring': open(REQUEST_BODY_FILE, 'rb')
    }

    response = requests.post(gearpump_deploy_url, data=data, files=files,
                             verify=False, cookies=load_file(GEARPUMP_COOKIE_NAME))
    delete_file(GEARPUMP_COOKIE_NAME)
    delete_file(REQUEST_BODY_FILE)
    return response.text

def _encode_json_to_utf8(json_input):
    return yaml.safe_load(json.dumps(json_input))

