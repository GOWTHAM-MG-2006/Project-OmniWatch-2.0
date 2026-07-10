# eBPF Probe Programs

**Phase:** 5
**Technology:** C (eBPF), libbpf, CO-RE

## Programs

| File | Purpose |
|------|---------|
| `http_trace.c` | HTTP/gRPC request/response tracing via tcp_sendmsg/tcp_recvmsg kprobes |
| `syscall_monitor.c` | System call monitoring (open, read, write, connect, accept, close) |
| `network_flow.c` | TCP/UDP flow tracking via XDP/TC hooks |
| `security_hooks.c` | Security event detection via LSM hooks |

## Requirements

- Linux 5.8+ with BTF enabled
- clang 12+ and llvm
- libbpf-dev
- linux-headers for running kernel

## Build

```bash
make all
```

## Usage

```bash
# Load and run via Rust controller
cd ../controller
cargo run
```

## CPU Overhead Target

< 0.1% CPU per traced connection
