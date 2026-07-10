/*
 * OmniWatch 2.0 — GhostCollector
 * Component: HTTP Trace eBPF Probe
 * Phase: 5
 * Purpose: eBPF program for HTTP/gRPC request/response tracing via kprobes
 * Inputs: Kernel tcp_sendmsg/tcp_recvmsg events
 * Outputs: Trace events to ring buffer for user-space consumption
 *
 * Target: Linux 5.8+ (BTF + ring buffers)
 * Build: make (requires libbpf, clang, llvm)
 */

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define MAX_ENTRIES 65536
#define TASK_COMM_LEN 16
#define TRUE 1

/* Ring buffer for events */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24); /* 16MB */
} events SEC(".maps");

/* Hash map to track in-flight requests */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u64);   /* tid */
    __type(value, struct http_event);
} request_map SEC(".maps");

/* HTTP event structure */
struct http_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tid;
    char comm[TASK_COMM_LEN];
    __u64 bytes_sent;
    __u64 bytes_received;
    __u32 direction; /* 0 = send, 1 = recv */
    __u32 pad;
};

/* Filter: only trace ports 80, 443, 8080, 9090 */
static __always_inline int is_http_port(__u16 port) {
    return port == 80 || port == 443 || port == 8080 || port == 9090;
}

/* kprobe: tcp_sendmsg — capture outbound HTTP data */
SEC("kprobe/tcp_sendmsg")
int BPF_KPROBE(tcp_sendmsg, struct sock *sk, struct msghdr *msg, size_t size) {
    __u16 family = BPF_CORE_READ(sk, __sk_common.skc_family);
    __u16 sport = BPF_CORE_READ(sk, __sk_common.skc_num);

    /* Filter by port */
    if (!is_http_port(sport) && !is_http_port(BPF_CORE_READ(sk, __sk_common.skc_dport)))
        return 0;

    __u64 tid = bpf_get_current_pid_tgid();
    struct http_event *evt = bpf_map_lookup_elem(&request_map, &tid);
    if (evt) {
        evt->bytes_sent += size;
        return 0;
    }

    /* New request */
    struct http_event new_evt = {
        .timestamp_ns = bpf_ktime_get_ns(),
        .pid = pid_tgid >> 32,
        .tid = (__u32)tid,
        .bytes_sent = size,
        .bytes_received = 0,
        .direction = 0,
    };
    bpf_get_current_comm(&new_evt.comm, sizeof(new_evt.comm));
    bpf_map_update_elem(&request_map, &tid, &new_evt, BPF_ANY);
    return 0;
}

/* kprobe: tcp_recvmsg — capture inbound HTTP data */
SEC("kprobe/tcp_recvmsg")
int BPF_KPROBE(tcp_recvmsg, struct sock *sk, struct msghdr *msg, size_t len) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct http_event *evt = bpf_map_lookup_elem(&request_map, &tid);
    if (evt) {
        evt->bytes_received += len;
        return 0;
    }
    return 0;
}

/* kretprobe: tcp_sendmsg — emit event on send completion */
SEC("kretprobe/tcp_sendmsg")
int BPF_KRETPROBE(tcp_sendmsg_ret, int ret) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct http_event *evt = bpf_map_lookup_elem(&request_map, &tid);
    if (!evt)
        return 0;

    if (ret > 0) {
        /* Submit completed event */
        struct http_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            __builtin_memcpy(e, evt, sizeof(*e));
            bpf_ringbuf_submit(e, 0);
        }
    }

    bpf_map_delete_elem(&request_map, &tid);
    return 0;
}

/* kretprobe: tcp_recvmsg — emit event on recv completion */
SEC("kretprobe/tcp_recvmsg")
int BPF_KRETPROBE(tcp_recvmsg_ret, int ret) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct http_event *evt = bpf_map_lookup_elem(&request_map, &tid);
    if (!evt)
        return 0;

    if (ret > 0) {
        evt->bytes_received = ret;
        evt->direction = 1;
        struct http_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            __builtin_memcpy(e, evt, sizeof(*e));
            bpf_ringbuf_submit(e, 0);
        }
    }

    bpf_map_delete_elem(&request_map, &tid);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
