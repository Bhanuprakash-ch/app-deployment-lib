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
Cloud Foundry REST API client wrapping "cf curl" command.
"""

import json

from app_deployment_helpers import cf_cli

CF_CURL = [cf_cli.CF, 'curl']


def create_service_key(service_guid, key_name):
    """Creates a service key for particular service instance.

    Args:
        service_guid (str): GUID of a service instance (can be user-provided).
        key_name (str): Name of the newly created service key.
    """
    params = {'service_instance_guid': service_guid, 'name': key_name}
    command_suffix = ['/v2/service_keys', '-X', 'POST', '-d', json.dumps(params)]
    cmd_output = cf_cli.get_command_output(CF_CURL + command_suffix)
    response_json = json.loads(cmd_output)
    if 'error_code' not in response_json:
        return response_json
    else:
        raise cf_cli.CommandFailedError(
            'Failed to create a service key {} for service with guid {}.\n'
            'Response body: {}'.format(key_name, service_guid, response_json))


def delete_particular_service_key(key_guid):
    """Deletes a particular service key.

    Args:
        key_guid (str): GUID of a service key
    """
    command_suffix = ['/v2/service_keys/{}'.format(key_guid), '-X', 'DELETE', '-d', '']
    cf_cli.get_command_output(CF_CURL + command_suffix)


def get_temporary_key_data(instance_name, key_name='DummyKey123'):
    """Creates a temporary service key for particular service instance to
    retrieve credentials data from.

    Args:
        service_guid (str): Name of a service instance to retrieve data for
    Returns:
        dict: Service key data for particular service instance.
    """
    service_key_data = \
        create_service_key(get_service_instance_guid(instance_name), key_name)
    delete_particular_service_key(service_key_data['metadata']['guid'])
    return service_key_data


def get_service_instance_guid(instance_name):
    """
    Args:
        instance_name (str): name of a service instance
    Returns:
        str: Guid of a particular service instance.
    """
    instances = get_all_service_instances()
    resources = instances['resources']
    for resource in resources:
        if resource['entity']['name'] == instance_name:
            return resource['metadata']['guid']

    raise cf_cli.CommandFailedError(
        'Failed to get service {} guid.'.format(instance_name))


def get_service_instance(instance_name):
    """
    Args:
        instance_name (str): name of a service instance
    Returns:
        dict: Details of particular service instance.
    """
    return cf_curl_get('/v2/service_instances/{}'.format(get_service_instance_guid(instance_name)))


def get_all_service_instances():
    """
    Returns:
        dict: All existing service instances,
    """
    return cf_curl_get('/v2/service_instances')


def create_service_binding(service_guid, app_guid):
    """Creates a binding between a service and an application.

    Args:
        service_guid (str): GUID of a service instance (can be user-provided).
        app_guid (str): Applications' GUID.
    """
    params = {'service_instance_guid': service_guid, 'app_guid': app_guid}
    command_suffix = ['/v2/service_bindings', '-X', 'POST', '-d', json.dumps(params)]
    cmd_output = cf_cli.get_command_output(CF_CURL + command_suffix)
    response_json = json.loads(cmd_output)
    if 'error_code' not in response_json:
        return response_json
    else:
        raise cf_cli.CommandFailedError(
            'Failed to create a binding between service {} and app {}.\n'
            'Response body: {}'.format(service_guid, app_guid, response_json))


def delete_service_binding(binding):
    """Deletes a service binding.

    Args:
        binding (dict): JSON representing a service binding. Has "metadata" and "entity" keys.
    """
    binding_url = binding['metadata']['url']
    cmd_output = cf_cli.get_command_output(CF_CURL + [binding_url, '-X', 'DELETE'])
    if cmd_output:
        raise cf_cli.CommandFailedError('Failed to delete a service binding. CF response: {}'
                                        .format(cmd_output))


def get_app_name(app_guid):
    """
    Args:
        app_guid (str): Application's GUID.

    Returns:
        str: Application's name,
    """
    app_desctiption = cf_curl_get('/v2/apps/{}'.format(app_guid))
    return app_desctiption['entity']['name']


def get_upsi_credentials(service_guid):
    """Gets the credentials (configuration) of a user-provided service instance.

    Args:
        service_guid (str): Service instance's GUID.

    Returns:
        dict: Content of the instance's "credentials" dictionary.
    """
    api_path = '/v2/user_provided_service_instances/{}'.format(service_guid)
    upsi_description = cf_curl_get(api_path)
    return upsi_description['entity']['credentials']


def get_upsi_bindings(service_guid):
    """Gets the bindings of a given user provided service instance.

    Args:
        service_guid (str): Service instance's GUID.

    Returns:
        list[dict]: List of dictionaries representing a binding.
            Binding has "metadata" and "entity" fields.
    """
    api_path = '/v2/user_provided_service_instances/{}/service_bindings'.format(service_guid)
    bindings_response = cf_curl_get(api_path)
    return bindings_response['resources']


def cf_curl_get(path):
    """Calls "cf curl" with a given path.

    Args:
        path (str): CF API path,
            e.g. /v2/user_provided_service_instances/8b89a54b-b292-49eb-a8c4-2396ec038120

    Returns:
        dict: JSON returned by the endpoint.
    """
    cmd_output = cf_cli.get_command_output(CF_CURL + [path])
    response_json = json.loads(cmd_output)
    if 'error_code' not in response_json:
        return response_json
    else:
        raise cf_cli.CommandFailedError('Failed GET on CF API path {}\n'
                                        'Response body: {}'.format(path, response_json))
