/*
// Copyright (c) 2023-2025 rapidPROX contributors
// Copyright (c) 2010-2020 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
*/

#ifndef _TX_PKT_H_
#define _TX_PKT_H_

#include <inttypes.h>
#include <string.h>
#include <rte_mbuf.h>
#include "ip6_addr.h"

struct task_base;

struct prox_headroom {
	uint64_t command;
	uint64_t data64;
	uint32_t ip;
	uint32_t prefix;
	uint32_t gateway_ip;
	uint16_t vlan;
	struct ipv6_addr ipv6_addr;
} __attribute__((packed));

void flush_queues_hw(struct task_base *tbase);
void flush_queues_sw(struct task_base *tbase);

void flush_queues_no_drop_hw(struct task_base *tbase);
void flush_queues_no_drop_sw(struct task_base *tbase);

/* The following four transmit functions always send packets to the
   single output unless the packet should be dropped. These functions
   are used if (1) the task is only sending to one destination and
   (2), packets can potentially be dropped (as specified by the out
   parameter, which is either NO_PORT_AVAIL or 0). */
int tx_pkt_no_drop_hw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_no_drop_sw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_hw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_sw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);

/* The following four transmit functions are used if (1) the task is
   only sending to one destination and (2), packets are never dropped
   by the task (the out parameter is ignored). */
int tx_pkt_no_drop_never_discard_hw1_lat_opt(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_no_drop_never_discard_hw1_thrpt_opt(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_no_drop_never_discard_hw1_no_pointer(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_no_drop_never_discard_sw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_never_discard_hw1_lat_opt(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_never_discard_hw1_thrpt_opt(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_never_discard_sw1(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);

/* The two "self" transmit functions are used if the task is
   transmitting to another task running on the same core and the
   destination task ID is one higher than the current task. The never_discard
   version of the function ignores the out parameter and should
   therefor only be used if the task never discards packets.*/
int tx_pkt_self(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);
int tx_pkt_never_discard_self(struct task_base *tbase, struct rte_mbuf **mbufs, const uint16_t n_pkts, uint8_t *out);

/* The following four tarnsmit functions are the most general. They
   are used if (1) packets can be dropped and (2) there are multiple
   outputs in the task. */
int tx_pkt_no_drop_hw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_no_drop_sw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_hw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_sw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_ctrlplane_hw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_ctrlplane_sw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);

int tx_pkt_trace(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_dump(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_distr(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_bw(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);

uint16_t tx_try_sw1(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts);
uint16_t tx_try_hw1(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts);
uint16_t tx_try_self(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts);

/* When there are no output ports, this function is configured as the
   tx function. This tx function can be used to make each task a
   sink. */
int tx_pkt_drop_all(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_l3(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);
int tx_pkt_ndp(struct task_base *tbase, struct rte_mbuf **mbufs, uint16_t n_pkts, uint8_t *out);

static inline uint8_t get_command(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->command & 0xFF;
}
static inline uint8_t get_task(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return (prox_headroom->command >> 8) & 0xFF;
}
static inline uint8_t get_core(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return (prox_headroom->command >> 16) & 0xFF;
}
static inline uint32_t get_ip(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return (prox_headroom->command >> 32) & 0xFFFFFFFF;
}

static inline void ctrl_ring_set_command_core_task_ip(struct rte_mbuf *mbuf, uint64_t udata64)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->command = udata64;
}

static inline void ctrl_ring_set_command(struct rte_mbuf *mbuf, uint8_t command)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->command = command;
}

static inline void ctrl_ring_set_ip(struct rte_mbuf *mbuf, uint32_t udata32)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->ip = udata32;
}

static inline uint32_t ctrl_ring_get_ip(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->ip;
}

static inline void ctrl_ring_set_gateway_ip(struct rte_mbuf *mbuf, uint32_t udata32)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->gateway_ip = udata32;
}

static inline uint32_t ctrl_ring_get_gateway_ip(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->gateway_ip;
}

static inline void ctrl_ring_set_prefix(struct rte_mbuf *mbuf, uint32_t udata32)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->prefix = udata32;
}

static inline uint32_t ctrl_ring_get_prefix(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->prefix;
}

static inline void ctrl_ring_set_data(struct rte_mbuf *mbuf, uint64_t data)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->data64 = data;
}

static inline uint64_t ctrl_ring_get_data(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->data64;
}

static inline void ctrl_ring_set_ipv6_addr(struct rte_mbuf *mbuf, struct ipv6_addr *ip)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	memcpy(&prox_headroom->ipv6_addr, ip, sizeof(struct ipv6_addr));
}

static inline struct ipv6_addr *ctrl_ring_get_ipv6_addr(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return &prox_headroom->ipv6_addr;
}

static inline void ctrl_ring_set_vlan(struct rte_mbuf *mbuf, uint32_t udata16)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	prox_headroom->vlan = udata16;
}

static inline uint16_t ctrl_ring_get_vlan(struct rte_mbuf *mbuf)
{
	struct prox_headroom *prox_headroom = (struct prox_headroom *)(rte_pktmbuf_mtod(mbuf, uint8_t*) - sizeof(struct prox_headroom));
	return prox_headroom->vlan;
}

int tx_ring_cti(struct task_base *tbase, struct rte_ring *ring, uint8_t command, struct rte_mbuf *mbuf, uint8_t core_id, uint8_t task_id, uint32_t ip, uint16_t vlan);
void tx_ring_cti6(struct task_base *tbase, struct rte_ring *ring, uint8_t command, struct rte_mbuf *mbuf, uint8_t core_id, uint8_t task_id, struct ipv6_addr *ip, uint16_t vlan);
void tx_ring_ip(struct task_base *tbase, struct rte_ring *ring, uint8_t command, struct rte_mbuf *mbuf, uint32_t ip);
void tx_ring_ip6(struct task_base *tbase, struct rte_ring *ring, uint8_t command,  struct rte_mbuf *mbuf, struct ipv6_addr *ip);
void tx_ring_ip6_data(struct task_base *tbase, struct rte_ring *ring, uint8_t command,  struct rte_mbuf *mbuf, struct ipv6_addr *ip, uint64_t data);
void tx_ring(struct task_base *tbase, struct rte_ring *ring, uint16_t command, struct rte_mbuf *mbuf);
void tx_ring_route(struct task_base *tbase, struct rte_ring *ring, int add, struct rte_mbuf *mbuf, uint32_t ip, uint32_t gateway_ip, uint32_t prefix);
static void store_packet(struct task_base *tbase, struct rte_mbuf *mbufs);

#endif /* _TX_PKT_H_ */
