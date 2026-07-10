# OmniWatch 2.0 — eBPF Probe Compilation
# Requires: clang, llvm, libbpf-dev, linux-headers (5.8+)

CC = clang
CFLAGS = -O2 -g -Wall -target bpf
INCLUDES = -I/usr/include/bpf

PROBES = http_trace syscall_monitor network_flow security_hooks

.PHONY: all clean

all: $(PROBES:=.o)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f *.o
