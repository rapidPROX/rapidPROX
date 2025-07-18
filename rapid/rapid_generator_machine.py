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

from rapid_log import RapidLog 
from rapid_machine import RapidMachine
from math import ceil, log2


class RandomPortBits(object):
    """
    Class to generate PROX bitmaps for random bit generation
    in source & dst UPD ports to emulate mutiple flows
    """
    @staticmethod
    def get_bitmap(flow_number):
        number_of_random_bits = ceil(log2(flow_number))
        if number_of_random_bits > 30:
            raise Exception("Not able to support that many flows")
            # throw exeption since we need the first bit to be 1
            # Otherwise, the randomization could results in all 0's
            # and that might be an invalid UDP port and result in 
            # packets being discarded
        src_number_of_random_bits = number_of_random_bits // 2
        dst_number_of_random_bits = (number_of_random_bits -
                src_number_of_random_bits)
        src_port_bitmap = '1000000000000000'.replace ('0','X',
                src_number_of_random_bits)
        dst_port_bitmap = '1000000000000000'.replace ('0','X',
                dst_number_of_random_bits)
        return [src_port_bitmap, dst_port_bitmap, 1 << number_of_random_bits]

class RapidGeneratorMachine(RapidMachine):
    """
    Class to deal with a generator PROX instance (VM, bare metal, container)
    """
    def __init__(self, key, user, password, vim, rundir, resultsdir,
            machine_params, configonly, ipv6):
        mac_address_size = 6
        ethertype_size = 2
        FCS_size = 4
        if ipv6:
            ip_header_size = 40
            self.ip_length_offset = 18
            # In IPV6, the IP size is the size of the IP content
            self.frame_size_minus_ip_size = (2 * mac_address_size +
                    ethertype_size + ip_header_size + FCS_size)
        else:
            ip_header_size = 20
            self.ip_length_offset = 16
            # In IPV4, the IP size is the size of the IP header + IP content
            self.frame_size_minus_ip_size = (2 * mac_address_size +
                    ethertype_size + FCS_size)
        self.frame_size_minus_udp_header_and_content = (2 * mac_address_size +
                ethertype_size + ip_header_size + FCS_size )
        udp_header_start_offset = (2 * mac_address_size + ethertype_size +
                ip_header_size)
        self.udp_source_port_offset = udp_header_start_offset 
        self.udp_dest_port_offset = udp_header_start_offset + 2
        self.udp_length_offset = udp_header_start_offset + 4
        self.ipv6 = ipv6
        if 'bucket_size_exp' in machine_params.keys():
            self.bucket_size_exp = machine_params['bucket_size_exp']
        else:
            self.bucket_size_exp = 11
        super().__init__(key, user, password, vim, rundir, resultsdir,
                machine_params, configonly)

    def get_cores(self):
        return (self.machine_params['gencores'] +
                self.machine_params['latcores'])

    def generate_lua(self):
        appendix = 'bucket_size_exp="{}"\n'.format(self.bucket_size_exp)
        if 'heartbeat' in self.machine_params.keys():
            appendix = (appendix +
                    'heartbeat="%s"\n'% self.machine_params['heartbeat'])
        else:
            appendix = appendix + 'heartbeat="60"\n'
        super().generate_lua(appendix)

    def start_prox(self):
        # Start the generator with the -e option so that the cores don't
        # start automatically
        super().start_prox('-e')

    def set_generator_speed(self, speed):
        # The assumption is that we only use task 0 for generating
        # We should check the gen.cfg file to make sure there is only task=0
        speed_per_gen_core = speed / len(self.machine_params['gencores']) 
        self.socket.speed(speed_per_gen_core, self.machine_params['gencores'])

    def set_udp_packet_size(self, imix_frame_sizes):
        # We should check the gen.cfg to make sure we only send UDP packets
        # If only 1 packet size, still using the 'old' way of setting the 
        # packet sizes in PROX. Otherwise, using the 'new' way which
        # automatically sets IP and UDP sizes. We should switch to the new way
        # eventually for all cases.
        if len(imix_frame_sizes) == 1:
            # Frame size = PROX pkt size + 4 bytes CRC
            # The set_size function takes the PROX packet size as a parameter
            self.socket.set_size(self.machine_params['gencores'], 0,
                    imix_frame_sizes[0] - 4)
            # Writing length in the ip header
            self.socket.set_value(self.machine_params['gencores'], 0,
                    self.ip_length_offset, imix_frame_sizes[0] - 
                    self.frame_size_minus_ip_size, 2)
            # Writing length in the udp header
            self.socket.set_value(self.machine_params['gencores'], 0,
                    self.udp_length_offset, imix_frame_sizes[0] -
                    self.frame_size_minus_udp_header_and_content, 2)
        else:
            if self.ipv6:
                RapidLog.critical('IMIX not supported for IPV6')
            prox_sizes = [frame_size - 4 for frame_size in imix_frame_sizes]
            self.socket.set_imix(self.machine_params['gencores'], 0,
                    prox_sizes)

    def set_flows(self, number_of_flows):
        source_port, destination_port, actualflows = RandomPortBits.get_bitmap(
                number_of_flows)
        self.socket.set_random(self.machine_params['gencores'],0,
                self.udp_source_port_offset, source_port,2)
        self.socket.set_random(self.machine_params['gencores'],0,
                self.udp_dest_port_offset, destination_port,2)
        return actualflows

    def start_gen_cores(self):
        self.socket.start(self.machine_params['gencores'])

    def stop_gen_cores(self):
        self.socket.stop(self.machine_params['gencores'])

    def start_latency_cores(self):
        self.socket.start(self.machine_params['latcores'])

    def stop_latency_cores(self):
        self.socket.stop(self.machine_params['latcores'])

    def lat_stats(self):
        # Checking all tasks in the cfg file. In this way, we can have more
        # latency tasks on the same core
        return (self.socket.lat_stats(self.machine_params['latcores'],
                self.all_tasks_for_this_cfg))
