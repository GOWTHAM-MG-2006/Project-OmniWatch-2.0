/*
 * OmniWatch 2.0 — GhostCollector
 * Component: Security Hooks eBPF Probe
 * Phase: 5
 * Purpose: eBPF program for security event detection via LSM hooks
 * Inputs: Kernel LSM security hook events
 * Outputs: Security events to ring buffer
 */

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define MAX_ENTRIES 4096
#define TASK_COMM_LEN 16

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} events SEC(".maps");

struct security_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 uid;
    char comm[TASK_COMM_LEN];
    __u32 event_type; /* 1=priv_esc, 2=container_escape, 3=unexpected_spawn, 4=unusual_conn */
    __u32 severity;   /* 1=low, 2=medium, 3=high, 4=critical */
    char detail[128];
};

/* LSM hook: file_open — detect setuid execution */
SEC("lsm/file_open")
int BPF_LSM(file_open, struct file *file) {
    /* Check if file has setuid bit */
    __u64 mode = BPF_CORE_READ(file, f_mode);
    if (!(mode & 0o4000)) /* FMODE_SETUID */
        return 0;

    __u64 tid = bpf_get_current_pid_tgid();
    struct security_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (e) {
        e->timestamp_ns = bpf_ktime_get_ns();
        e->pid = pid_tgid >> 32;
        e->uid = (__u32)(tid >> 32);
        e->event_type = 1; /* privilege escalation */
        e->severity = 3;   /* high */
        bpf_get_current_comm(&e->comm, sizeof(e->comm));
        bpf_ringbuf_submit(e, 0);
    }
    return 0;
}

/* LSM hook: bprm_check_security — detect unusual process spawning */
SEC("lsm/bprm_check_security")
int BPF_LSM(bprm_check_security, struct linux_binprm *bprm) {
    char comm[TASK_COMM_LEN];
    bpf_get_current_comm(&comm, sizeof(comm));

    /* Detect web servers spawning shells */
    if (__builtin_strcmp(comm, "nginx") == 0 ||
        __builtin_strcmp(comm, "apache2") == 0 ||
        __builtin_strcmp(comm, "node") == 0 ||
        __builtin_strcmp(comm, "java") == 0) {

        char file_comm[TASK_COMM_LEN];
        BPF_CORE_READ_STR_INTO(&file_comm, bprm->filename, 128);

        if (__builtin_strncmp(file_comm, "/bin/", 5) == 0 ||
            __builtin_strncmp(file_comm, "/usr/bin/", 9) == 0) {

            __u64 tid = bpf_get_current_pid_tgid();
            struct security_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
            if (e) {
                e->timestamp_ns = bpf_ktime_get_ns();
                e->pid = pid_tgid >> 32;
                e->uid = (__u32)(tid >> 32);
                e->event_type = 3; /* unexpected spawn */
                e->severity = 4;   /* critical */
                bpf_get_current_comm(&e->comm, sizeof(e->comm));
                bpf_ringbuf_submit(e, 0);
            }
        }
    }
    return 0;
}

/* LSM hook: socket_connect — detect unusual outbound connections */
SEC("lsm/socket_connect")
int BPF_LSM(socket_connect, struct socket *sock, struct sockaddr *address) {
    __u64 tid = bpf_get_current_pid_tgid();
    struct security_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (e) {
        e->timestamp_ns = bpf_ktime_get_ns();
        e->pid = pid_tgid >> 32;
        e->uid = (__u32)(tid >> 32);
        e->event_type = 4; /* unusual connection */
        e->severity = 2;   /* medium */
        bpf_get_current_comm(&e->comm, sizeof(e->comm));
        bpf_ringbuf_submit(e, 0);
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
