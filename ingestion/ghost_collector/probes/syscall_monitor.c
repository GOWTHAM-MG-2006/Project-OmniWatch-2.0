/*
 * OmniWatch 2.0 — GhostCollector
 * Component: Syscall Monitor eBPF Probe
 * Phase: 5
 * Purpose: eBPF program for system call monitoring via kprobes
 * Inputs: Kernel syscall entry/exit events
 * Outputs: Syscall events to ring buffer
 */

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define MAX_ENTRIES 65536
#define TASK_COMM_LEN 16

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u64);
    __type(value, struct syscall_event);
} syscall_map SEC(".maps");

struct syscall_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tid;
    char comm[TASK_COMM_LEN];
    __u64 syscall_nr;
    __u64 latency_ns;
    __s64 ret;
    __u64 fd;
    char filename[256];
};

/* Trace open syscall */
SEC("kprobe/do_sys_openat2")
int BPF_KPROBE(do_sys_openat2, int dfd, const char *filename, int flags) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct syscall_event evt = {
        .timestamp_ns = bpf_ktime_get_ns(),
        .pid = pid_tgid >> 32,
        .tid = (__u32)tid,
        .syscall_nr = 257, /* __NR_openat */
    };
    bpf_get_current_comm(&evt.comm, sizeof(evt.comm));
    bpf_probe_read_user_str(&evt.filename, sizeof(evt.filename), filename);
    bpf_map_update_elem(&syscall_map, &tid, &evt, BPF_ANY);
    return 0;
}

SEC("kretprobe/do_sys_openat2")
int BPF_KRETPROBE(do_sys_openat2_ret, int ret) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct syscall_event *evt = bpf_map_lookup_elem(&syscall_map, &tid);
    if (!evt) return 0;

    evt->ret = ret;
    evt->latency_ns = bpf_ktime_get_ns() - evt->timestamp_ns;

    struct syscall_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (e) {
        __builtin_memcpy(e, evt, sizeof(*e));
        bpf_ringbuf_submit(e, 0);
    }

    bpf_map_delete_elem(&syscall_map, &tid);
    return 0;
}

/* Trace connect syscall */
SEC("kprobe/__x64_sys_connect")
int BPF_KPROBE(sys_connect, int fd, struct sockaddr *uservaddr, int addrlen) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct syscall_event evt = {
        .timestamp_ns = bpf_ktime_get_ns(),
        .pid = pid_tgid >> 32,
        .tid = (__u32)tid,
        .syscall_nr = 42, /* __NR_connect */
        .fd = fd,
    };
    bpf_get_current_comm(&evt.comm, sizeof(evt.comm));
    bpf_map_update_elem(&syscall_map, &tid, &evt, BPF_ANY);
    return 0;
}

SEC("kretprobe/__x64_sys_connect")
int BPF_KRETPROBE(sys_connect_ret, int ret) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct syscall_event *evt = bpf_map_lookup_elem(&syscall_map, &tid);
    if (!evt) return 0;

    evt->ret = ret;
    evt->latency_ns = bpf_ktime_get_ns() - evt->timestamp_ns;

    struct syscall_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (e) {
        __builtin_memcpy(e, evt, sizeof(*e));
        bpf_ringbuf_submit(e, 0);
    }

    bpf_map_delete_elem(&syscall_map, &tid);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
