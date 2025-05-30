#!/usr/bin/python

##
## Copyright (c) 2023-2025 rapidPROX contributors
## Copyright (c) 2020 Intel Corporation
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##

import os_client_config
import heatclient
from heatclient.client import Client as Heat_Client
from keystoneclient.v3 import Client as Keystone_Client
from heatclient.common import template_utils
from novaclient import client as NovaClient
import yaml
import os
import time
import sys
from collections import OrderedDict
from rapid_log import RapidLog

class StackDeployment(object):
    """Deployment class to create VMs for test execution in OpenStack
    environment.
    """
    def __init__(self, cloud_name):
#        RapidLog.log_init('CREATEStack.log', 'DEBUG', 'INFO', '2020.05.05')
        self.dp_ips = []
        self.dp_macs = []
        self.mngmt_ips = []
        self.names = []
        self.number_of_servers = 0
        self.cloud_name = cloud_name
        self.heat_template = 'L6_heat_template.yaml'
        self.heat_param = 'params_rapid.yaml'
        self.cloud_config = os_client_config.OpenStackConfig().get_all_clouds()
        ks_client = None
        for cloud in self.cloud_config:
            if cloud.name == self.cloud_name:
                ks_client = Keystone_Client(**cloud.config['auth'])
                break
        if ks_client == None:
            sys.exit()
        heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration',
        endpoint_type='publicURL')
        self.heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token)
        self.nova_client = NovaClient.Client(2, **cloud.config['auth']) 

    def generate_paramDict(self):
        for output in self.stack.output_list()['outputs']:
            output_value = self.stack.output_show(output['output_key'])['output']['output_value']
            for server_group_output in output_value:
                if (output['output_key'] == 'number_of_servers'):
                    self.number_of_servers += int (server_group_output)
                elif (output['output_key'] == 'mngmt_ips'):
                    for ip in server_group_output:
                        self.mngmt_ips.append(ip)
                elif (output['output_key'] == 'data_plane_ips'):
                    for dps in server_group_output:
                        self.dp_ips.append(dps)
                elif (output['output_key'] == 'data_plane_macs'):
                    for mac in server_group_output:
                        self.dp_macs.append(mac)
                elif (output['output_key'] == 'server_name'):
                    for name in server_group_output:
                        self.names.append(name)

    def print_paramDict(self, user, dataplane_subnet_mask):
        if not(len(self.dp_ips) == len(self.dp_macs) == len(self.mngmt_ips)):
            sys.exit()
        _ENV_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
        env_file = os.path.join(_ENV_FILE_DIR, self.stack.stack_name)+ '.env'
        with open(env_file, 'w') as env_file:
            env_file.write('[rapid]\n')
            env_file.write('total_number_of_machines = {}\n'.format(str(self.number_of_servers)))
            env_file.write('\n')
            for count in range(self.number_of_servers):
                env_file.write('[M' + str(count+1) + ']\n')
                env_file.write('name = {}\n'.format(str(self.names[count])))
                env_file.write('admin_ip = {}\n'.format(str(self.mngmt_ips[count])))
                if type(self.dp_ips[count]) == list:
                    for i, dp_ip in enumerate(self.dp_ips[count], start = 1):
                        env_file.write('dp_ip{} = {}/{}\n'.format(i, str(dp_ip),
                            dataplane_subnet_mask))
                else:
                    env_file.write('dp_ip1 = {}/{}\n'.format(str(self.dp_ips[count]),
                        dataplane_subnet_mask))
                if type(self.dp_macs[count]) == list:
                    for i, dp_mac in enumerate(self.dp_macs[count], start = 1):
                        env_file.write('dp_mac{} = {}\n'.format(i, str(dp_mac)))
                else:
                    env_file.write('dp_mac1 = {}\n'.format(str(self.dp_macs[count])))
                env_file.write('\n')
            env_file.write('[ssh]\n')
            env_file.write('key = {}\n'.format(self.key_name))
            env_file.write('user = {}\n'.format(user))
            env_file.write('\n')
            env_file.write('[Varia]\n')
            env_file.write('vim = OpenStack\n')
            env_file.write('stack = {}\n'.format(self.stack.stack_name))

    def create_stack(self, stack_name, stack_file_path, heat_parameters):
        files, template = template_utils.process_template_path(stack_file_path)
        stack_created = self.heatclient.stacks.create(stack_name = stack_name,
                template = template, parameters = heat_parameters,
                files = files)
        stack = self.heatclient.stacks.get(stack_created['stack']['id'],
                resolve_outputs=True)
        # Poll at 5 second intervals, until the status is no longer 'BUILD'
        while stack.stack_status == 'CREATE_IN_PROGRESS':
            print('waiting..')
            time.sleep(5)
            stack = self.heatclient.stacks.get(stack_created['stack']['id'], resolve_outputs=True)
        if stack.stack_status == 'CREATE_COMPLETE':    
            return stack
        else:
            RapidLog.exception('Error in stack deployment')

    def create_key(self):
        if os.path.exists(self.key_name):
            public_key_file = "{}.pub".format(self.key_name)
            if not os.path.exists(public_key_file):
                RapidLog.critical('Keypair {}.pub does not exist'.format(
                    self.key_name))
            with open(public_key_file, mode='rb') as public_file:
                public_key = public_file.read()
        else:
            public_key = None
        keypair = self.nova_client.keypairs.create(name = self.key_name, 
                public_key = public_key)
        # Create a file for writing that can only be read and written by owner
        if not os.path.exists(self.key_name):
            fp = os.open(self.key_name, os.O_WRONLY | os.O_CREAT, 0o600)
            with os.fdopen(fp, 'w') as f:
                    f.write(keypair.private_key)
        RapidLog.info('Keypair {} created'.format(self.key_name))

    def IsDeployed(self, stack_name):
        for stack in self.heatclient.stacks.list():
            if stack.stack_name == stack_name:
                RapidLog.info('Stack already existing: {}'.format(stack_name))
                self.stack = stack
                return True
        return False

    def IsKey(self):
        keypairs = self.nova_client.keypairs.list()
        if next((x for x in keypairs if x.name == self.key_name), None):
            RapidLog.info('Keypair {} already exists'.format(self.key_name))
            return True
        return False

    def deploy(self, stack_name, heat_template, heat_param):
        heat_parameters_file = open(heat_param)
        heat_parameters = yaml.load(heat_parameters_file,
                Loader=yaml.BaseLoader)['parameters']
        heat_parameters_file.close()
        self.key_name = heat_parameters['PROX_key']
        if not self.IsDeployed(stack_name):
            if not self.IsKey():
                self.create_key()
            self.stack = self.create_stack(stack_name, heat_template,
                    heat_parameters)

    def generate_env_file(self, user = 'centos', dataplane_subnet_mask = '24'):
        self.generate_paramDict()
        self.print_paramDict(user, dataplane_subnet_mask)
