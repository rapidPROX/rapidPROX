##
## Copyright (c) 2023-2025 rapidPROX contributors
## Copyright (c) 2019-2020 Intel Corporation
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

import sys, yaml
from os import path
from kubernetes import client, config
try:
    import configparser
except ImportError:
    # Python 2.x fallback
    import ConfigParser as configparser
import logging
from logging import handlers
from uuid import uuid1
from rapid_k8s_pod import Pod

class K8sDeployment:
    """Deployment class to create containers for test execution in Kubernetes
    environment.
    """
    LOG_FILE_NAME = "createrapidk8s.log"
    SSH_PRIVATE_KEY = "./rapid_rsa_key"
    SSH_USER = "rapid"

    POD_YAML_TEMPLATE_FILE_NAME = "pod-rapid.yaml"

    _sriov_spec_filename="sriovnetwork.yaml"
    _log = None
    _create_config = None
    _runtime_config = None
    _total_number_of_pods = 0
    _pods = []
    _push_gw_pod = None
    _gen_push_gw_pod = None
    _generator_pods = []
    _namespace = None
    _createnamespace = False

    def __init__(self, kubeconfig = None, ImageRepository = None):
        # Configure logger
        self._log = logging.getLogger("k8srapid")
        self._log.setLevel(logging.DEBUG)

        console_formatter = logging.Formatter("%(message)s")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)

        file_formatter = logging.Formatter("%(asctime)s - "
                                           "%(levelname)s - "
                                           "%(message)s")
        file_handler = logging.handlers.RotatingFileHandler(self.LOG_FILE_NAME,
                                                            backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        self._log.addHandler(file_handler)
        self._log.addHandler(console_handler)

        # Initialize k8s plugin
        try:
            config.load_kube_config(config_file = kubeconfig)
        except:
            config.load_incluster_config()

        Pod.k8s_CoreV1Api = client.CoreV1Api()
        self._ImageRepository = ImageRepository

    def load_create_config(self, config_file_name):
        """Read and parse configuration file for the test environment.
        """
        self._log.info("Loading configuration file %s", config_file_name)
        self._create_config = configparser.RawConfigParser()
        try:
            self._create_config.read(config_file_name)
        except Exception as e:
            self._log.error("Failed to read config file!\n%s\n" % e)
            return -1

        # Now parse config file content
        generator_pod_index = 0

        if self._create_config.has_option("GENERATOR" ,
                                              "generator-config"):
            try:
                generator_config = configparser.RawConfigParser()
                generator_config.read(self._create_config.get("GENERATOR",
                        "generator-config"))
                number_of_pods = int(generator_config.get(
                    "rapid", "total_number_of_machines"))
                for generator_pod_index in range(1, number_of_pods + 1):
                    section = 'M{}'.format(generator_pod_index)
                    options = generator_config.options(section)
                    pod = Pod("Generator{}".format(generator_pod_index))
                    for option in options:
                        pod.set_id(generator_pod_index)
                        match option:
                            case "admin_ip":
                                pod.set_admin_ip(
                                    generator_config.get(section, option))
                            case "admin_port":
                                pod.set_admin_port(int(
                                    generator_config.get(section, option)))
                            case "socket_port":
                                pod.set_socket_port(int(
                                    generator_config.get(section, option)))
                            case "dp_mac1":
                                pod.set_dp_mac(
                                    generator_config.get(section, option))
                            case "dp_pci_dev":
                                pod.set_dp_pci_dev(
                                    generator_config.get(section, option))
                            case "dp_ip1":
                                pod.set_dp_ip(
                                    generator_config.get(section, option))
                    self._generator_pods.append(pod)
                section = 'pushgateway'
                self._gen_push_gw_pod = Pod(name = section)
                options = generator_config.options(section)
                for option in options:
                    match option:
                        case "push_gw_ip":
                            self._gen_push_gw_pod.set_admin_ip(
                                generator_config.get(section, option))
                        case "push_gw_port":
                            self._gen_push_gw_pod.set_push_gw_port(int(
                                generator_config.get(section, option)))
            except Exception as e:
                self._log.error("generator config file issue: {}".format(e))
        # Parse [DEFAULT] section
        if self._create_config.has_option("DEFAULT", "total_number_of_pods"):
            self._total_number_of_pods = self._create_config.getint(
                "DEFAULT", "total_number_of_pods")
        else:
            self._log.error("No option total_number_of_pods in DEFAULT section")
            return -1

        self._log.debug("Total number of pods %d" % self._total_number_of_pods)

        try:
            self._namespace = self._create_config.get(
                "DEFAULT", "namespace")
        except (configparser.NoSectionError, configparser.NoOptionError):
            id=str(uuid1())
            self._namespace = "rapid-testing-" + id[:-28]
            self._createnamespace = True

        self._log.debug("Using namespace %s" % self._namespace)

        # Parse [PODx] sections
        for i in range(1, int(self._total_number_of_pods) + 1):
            # Search for POD name
            if self._create_config.has_option("POD%d" % i,
                                              "name"):
                pod_name = self._create_config.get(
                    "POD%d" % i, "name")
            else:
                pod_name = "prox-pod-%d" % i

            # Search for POD hostname
            if self._create_config.has_option("POD%d" % i,
                                              "nodeSelector_hostname"):
                pod_nodeselector_hostname = self._create_config.get(
                    "POD%d" % i, "nodeSelector_hostname")
            else:
                pod_nodeselector_hostname = None

            # Search for POD spec
            if self._create_config.has_option("POD%d" % i,
                                              "spec_file_name"):
                pod_spec_file_name = self._create_config.get(
                    "POD%d" % i, "spec_file_name")
            else:
                pod_spec_file_name = K8sDeployment.POD_YAML_TEMPLATE_FILE_NAME

            # Search for POD dataplane static IP
            if self._create_config.has_option("POD%d" % i,
                                              "dp_ip"):
                pod_dp_ip = self._create_config.get(
                    "POD%d" % i, "dp_ip")
            else:
                pod_dp_ip = None

            # Search for POD dataplane subnet
            if self._create_config.has_option("POD%d" % i,
                                              "dp_subnet"):
                pod_dp_subnet = self._create_config.get(
                    "POD%d" % i, "dp_subnet")
            else:
                pod_dp_subnet = "24"

            # Search for POD nodeport service
            if self._create_config.has_option("POD%d" % i,
                                              "nodeport"):
                pod_nodeport = True
            else:
                pod_nodeport = None

            pod = Pod(pod_name, pod_nodeport, self._namespace)
            pod.set_imagerepository(self._ImageRepository)
            pod.set_nodeselector(pod_nodeselector_hostname)
            pod.set_spec_file_name(pod_spec_file_name)
            pod.set_dp_ip(pod_dp_ip)
            pod.set_dp_subnet(pod_dp_subnet)
            pod.set_id(i + generator_pod_index)

            # Add POD to the list of PODs which need to be created
            self._pods.append(pod)
        if self._create_config.has_section("PUSHGW"):
            pod_name = self._create_config.get("PUSHGW", "name")
            if self._create_config.has_option("PUSHGW",
                                              "nodeSelector_hostname"):
                pod_nodeselector_hostname = self._create_config.get(
                    "PUSHGW", "nodeSelector_hostname")
            else:
                pod_nodeselector_hostname = None

            # Search for POD spec
            if self._create_config.has_option("PUSHGW",
                                              "spec_file_name"):
                pod_spec_file_name = self._create_config.get(
                        "PUSHGW", "spec_file_name")
            else:
                pod_spec_file_name = "pushgateway.yaml"

            # Search for POD nodeport service
            if self._create_config.has_option("PUSHGW",
                                              "nodeport"):
                pod_nodeport = True
            else:
                pod_nodeport = None
            pod = Pod(pod_name, pod_nodeport, self._namespace)
            pod.set_imagerepository(self._ImageRepository)
            pod.set_nodeselector(pod_nodeselector_hostname)
            pod.set_spec_file_name(pod_spec_file_name)

            self._push_gw_pod = pod

        return 0

    def create_k8s_resources(self):
        """Create all required k8s resources.
        """
        self.create_namespace()
        self.create_pods()

    def create_namespace(self):
        if self._createnamespace:
            namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self._namespace))
            Pod.k8s_CoreV1Api.create_namespace(namespace)

    def create_sriovnetwork(self):
        """Load sriovnetwork description from yaml file.
        """
        with open(path.join(path.dirname(__file__),
            self._sriov_spec_filename)) as yaml_file:
            sriov_network_body = yaml.safe_load(yaml_file)
        sriov_network_body["spec"]["networkNamespace"] = self._namespace
        api_instance = client.CustomObjectsApi()
        sriov_network_group = "sriovnetwork.openshift.io"
        sriov_network_version = "v1"
        sriov_network_plural = "sriovnetworks"
        try:
            api_response = api_instance.get_namespaced_custom_object(
                name = sriov_network_body["metadata"]["name"],
                group = sriov_network_group,
                version = sriov_network_version,
                namespace = sriov_network_body["metadata"]["namespace"],
                plural = sriov_network_plural,
            )
        except Exception as e:
            if e.status != 404:
                self._log.info("SR-IOV network {} does not exist".
                    format(sriov_network_body["metadata"]["name"]))
            api_response = None
        try:
            if api_response:
                api_response = api_instance.patch_namespaced_custom_object(
                    name = sriov_network_body["metadata"]["name"],
                    group = sriov_network_group,
                    version = sriov_network_version,
                    namespace = sriov_network_body["metadata"]["namespace"],
                    plural = sriov_network_plural,
                    body = sriov_network_body
                )
                self._log.info("SR-IOV Network updated: {}".format(api_response))
            else:
                api_response = api_instance.create_namespaced_custom_object(
                    group = sriov_network_group,
                    version = sriov_network_version,
                    namespace = sriov_network_body["metadata"]["namespace"],
                    plural = sriov_network_plural,
                    body = sriov_network_body
            )
            self._log.info("SR-IOV Network created: {}".format(api_response))
        except Exception as e:
            self._log.error("Error creating or updating SR-IOV Network: {}".format(e))

    def create_pods(self):
        """ Create test PODs and wait for them to start.
        Collect information for tests to run.
        """
        self._log.info("Creating PODs...")

        # Create PODs using template from yaml file
        for pod in self._pods:
            self._log.info("Creating POD %s...", pod.get_name())
            pod.create_from_yaml()
        if self._push_gw_pod:
            self._push_gw_pod.create_from_yaml()

        # Wait for PODs to start
        for pod in self._pods:
            pod.wait_for_start()
        if self._push_gw_pod:
            self._push_gw_pod.wait_for_start()

        # Collect information from started PODs for test execution
        for pod in self._pods:
            pod.set_ssh_credentials(K8sDeployment.SSH_USER, K8sDeployment.SSH_PRIVATE_KEY)
            pod.get_sriov_dev_mac()
            pod.get_qat_dev()

    def save_runtime_config(self, config_file_name):
        self._log.info("Saving config %s for runrapid script...",
                       config_file_name)
        self._runtime_config = configparser.RawConfigParser()

        # Section [ssh]
        self._runtime_config.add_section("ssh")
        self._runtime_config.set("ssh",
                                 "key",
                                 K8sDeployment.SSH_PRIVATE_KEY)
        self._runtime_config.set("ssh",
                                 "user",
                                 K8sDeployment.SSH_USER)

        # Section [rapid]
        self._runtime_config.add_section("rapid")
        self._runtime_config.set("rapid",
                                 "total_number_of_machines",
                                 len(self._generator_pods) +
                                 len(self._pods))

        # Export information about each pod
        # Sections [Mx]
        for pod in self._generator_pods:
            self._runtime_config.add_section("M%d" % pod.get_id())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "admin_ip", pod.get_admin_ip())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "admin_port", pod.get_admin_port())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "socket_port", pod.get_socket_port())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_mac1", pod.get_dp_mac())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_pci_dev", pod.get_dp_pci_dev())
            if (pod.get_qat_pci_dev()):
                for qat_index, qat_device in enumerate(pod.get_qat_pci_dev()):
                    self._runtime_config.set("M%d" % pod.get_id(),
                                           "qat_pci_dev%d" % qat_index, qat_device)
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_ip1", pod.get_dp_ip())
        for pod in self._pods:
            self._runtime_config.add_section("M%d" % pod.get_id())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "admin_ip", pod.get_admin_ip())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "admin_port", pod.get_admin_port())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "socket_port", pod.get_socket_port())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_mac1", pod.get_dp_mac())
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_pci_dev", pod.get_dp_pci_dev())
            if (pod.get_qat_pci_dev()):
                for qat_index, qat_device in enumerate(pod.get_qat_pci_dev()):
                    self._runtime_config.set("M%d" % pod.get_id(),
                                           "qat_pci_dev%d" % qat_index, qat_device)
            self._runtime_config.set("M%d" % pod.get_id(),
                                     "dp_ip1", pod.get_dp_ip() + "/" +
                                     pod.get_dp_subnet())
        # Section [PushGateway]
        if self._gen_push_gw_pod:
            self._runtime_config.add_section(self._gen_push_gw_pod.get_name())
            self._runtime_config.set(self._gen_push_gw_pod.get_name(),
                                     "push_gw_ip", self._gen_push_gw_pod.get_admin_ip())
            self._runtime_config.set(self._gen_push_gw_pod.get_name(),
                                     "push_gw_port", self._gen_push_gw_pod.get_push_gw_port())
        if self._push_gw_pod:
            self._runtime_config.add_section(self._push_gw_pod.get_name())
            self._runtime_config.set(self._push_gw_pod.get_name(),
                                     "push_gw_ip", self._push_gw_pod.get_admin_ip())
            self._runtime_config.set(self._push_gw_pod.get_name(),
                                     "push_gw_port", self._push_gw_pod.get_push_gw_port())

        # Section [Varia]
        self._runtime_config.add_section("Varia")
        self._runtime_config.set("Varia",
                                 "vim",
                                 "kubernetes")

        # Write runtime config file
        with open(config_file_name, "w") as file:
            self._runtime_config.write(file)

    def delete_pods(self):
        for pod in self._pods:
            pod.terminate()
        if self._namespace.startswith('rapid-testing-'):
            Pod.k8s_CoreV1Api.delete_namespace(name = self._namespace)
