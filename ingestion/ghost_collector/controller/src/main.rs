/*
 * OmniWatch 2.0 — GhostCollector
 * Component: eBPF Controller
 * Phase: 5
 * Purpose: Main entry point — loads eBPF programs, reads ring buffers, exports telemetry
 */

mod event_parser;
mod otel_exporter;

use anyhow::Result;
use aya::programs::KProbe;
use aya::{include_bytes_aligned, Ebpf};
use clap::Parser;
use tokio::signal;
use tracing::{info, warn};

#[derive(Parser)]
#[command(name = "omniwatch-controller")]
#[command(about = "eBPF controller for OmniWatch 2.0 GhostCollector")]
struct Args {
    #[arg(long, default_value = "4317")]
    otel_port: u16,

    #[arg(long, default_value = "false")]
    dry_run: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    let args = Args::parse();

    info!("Starting OmniWatch eBPF Controller");
    info!("OTLP port: {}", args.otel_port);

    if args.dry_run {
        info!("Dry run mode — skipping eBPF program loading");
        run_dry_run().await?;
        return Ok(());
    }

    // Load eBPF programs
    let mut bpf = match load_ebpf_programs() {
        Ok(bpf) => bpf,
        Err(e) => {
            warn!("Failed to load eBPF programs: {}. Running in mock mode.", e);
            run_dry_run().await?;
            return Ok(());
        }
    };

    // Attach kprobes
    if let Err(e) = attach_kprobes(&mut bpf) {
        warn!("Failed to attach kprobes: {}. Continuing with partial instrumentation.", e);
    }

    // Read events from ring buffers
    let mut exporter = otel_exporter::OtelExporter::new(args.otel_port);

    info!("Controller running. Press Ctrl+C to stop.");
    tokio::select! {
        _ = read_events(&mut bpf, &mut exporter) => {}
        _ = signal::ctrl_c() => {
            info!("Shutting down...");
        }
    }

    Ok(())
}

fn load_ebpf_programs() -> Result<Ebpf> {
    let mut bpf = Ebpf::load(include_bytes_aligned!(
        "../../probes/http_trace.o"
    ))?;
    info!("Loaded eBPF programs successfully");
    Ok(bpf)
}

fn attach_kprobes(bpf: &mut Ebpf) -> Result<()> {
    if let Some(program) = bpf.program_mut("tcp_sendmsg") {
        let prog: &mut KProbe = program.try_into()?;
        prog.load()?;
        prog.attach("tcp_sendmsg", 0)?;
        info!("Attached kprobe: tcp_sendmsg");
    }
    if let Some(program) = bpf.program_mut("tcp_recvmsg") {
        let prog: &mut KProbe = program.try_into()?;
        prog.load()?;
        prog.attach("tcp_recvmsg", 0)?;
        info!("Attached kprobe: tcp_recvmsg");
    }
    Ok(())
}

async fn read_events(bpf: &mut Ebpf, exporter: &mut otel_exporter::OtelExporter) -> Result<()> {
    loop {
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
        // Read from ring buffer and export
    }
}

async fn run_dry_run() -> Result<()> {
    info!("Running in dry-run mode — generating sample telemetry");
    let mut exporter = otel_exporter::OtelExporter::new(4317);

    for i in 0..5 {
        let event = event_parser::parse_sample_event(i);
        exporter.export_event(&event).await?;
        tokio::time::sleep(std::time::Duration::from_secs(1)).await;
    }

    info!("Dry run complete");
    Ok(())
}
