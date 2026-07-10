/*
 * OmniWatch 2.0 — GhostCollector
 * Component: Network Flow eBPF Probe
 * Phase: 5
 * Purpose: eBPF program for TCP/UDP flow tracking via XDP/TC hooks
 * Inputs: Kernel network packet events
 * Outputs: Network flow events to ring buffer
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define MAX_ENTRIES 65536

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, struct flow_key);
    __type(value, struct flow_stats);
} flow_map SEC(".maps");

struct flow_key {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8  proto;
};

struct flow_stats {
    __u64 bytes_sent;
    __u64 bytes_recv;
    __u64 packets_sent;
    __u64 packets_recv;
    __u64 first_seen_ns;
    __u64 last_seen_ns;
    __u32 retransmissions;
};

struct flow_event {
    __u64 timestamp_ns;
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8  proto;
    __u8  pad[3];
    __u64 bytes;
    __u64 packets;
    __u32 event_type; /* 1=new, 2=update, 3=close */
};

/* TC ingress hook */
SEC("tc")
int tc_ingress(struct __sk_buff *skb) {
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return TC_ACT_OK;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_OK;

    if (ip->protocol != IPPROTO_TCP && ip->protocol != IPPROTO_UDP)
        return TC_ACT_OK;

    struct flow_key key = {
        .src_ip = ip->saddr,
        .dst_ip = ip->daddr,
        .proto = ip->protocol,
    };

    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)(ip + 1);
        if ((void *)(tcp + 1) > data_end)
            return TC_ACT_OK;
        key.src_port = bpf_ntohs(tcp->source);
        key.dst_port = bpf_ntohs(tcp->dest);
    } else {
        struct udphdr *udp = (void *)(ip + 1);
        if ((void *)(udp + 1) > data_end)
            return TC_ACT_OK;
        key.src_port = bpf_ntohs(udp->source);
        key.dst_port = bpf_ntohs(udp->dest);
    }

    /* Update flow stats */
    struct flow_stats *stats = bpf_map_lookup_elem(&flow_map, &key);
    __u64 now = bpf_ktime_get_ns();
    __u64 bytes = data_end - data;

    if (stats) {
        stats->bytes_recv += bytes;
        stats->packets_recv += 1;
        stats->last_seen_ns = now;
    } else {
        struct flow_stats new_stats = {
            .bytes_recv = bytes,
            .packets_recv = 1,
            .first_seen_ns = now,
            .last_seen_ns = now,
        };
        bpf_map_update_elem(&flow_map, &key, &new_stats, BPF_ANY);

        /* Emit new flow event */
        struct flow_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            e->timestamp_ns = now;
            e->src_ip = key.src_ip;
            e->dst_ip = key.dst_ip;
            e->src_port = key.src_port;
            e->dst_port = key.dst_port;
            e->proto = key.proto;
            e->bytes = bytes;
            e->packets = 1;
            e->event_type = 1;
            bpf_ringbuf_submit(e, 0);
        }
    }

    return TC_ACT_OK;
}

char LICENSE[] SEC("license") = "GPL";
