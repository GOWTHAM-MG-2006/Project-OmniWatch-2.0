"""Centralized configuration for OmniWatch 2.0.
All values read from environment variables with sensible defaults."""
import os


class Config:
    # --- Service URLs ---
    CORS_ALLOWED_ORIGINS = os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    SSO_REDIRECT_URI = os.environ.get("SSO_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")
    DASHBOARD_BACKEND_URL = os.environ.get("DASHBOARD_BACKEND_URL", "http://localhost:8000/health")
    MINIO_HEALTH_URL = os.environ.get("MINIO_HEALTH_URL", "http://localhost:9002/minio/health/live")
    OPA_HEALTH_URL = os.environ.get("OPA_HEALTH_URL", "http://localhost:8181/health")
    OLLAMA_HEALTH_URL = os.environ.get("OLLAMA_HEALTH_URL", "http://localhost:11434/api/tags")

    # --- Database Connections ---
    CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    OPA_URL = os.environ.get("OPA_URL", "http://localhost:8181")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ARGOCD_URL = os.environ.get("ARGOCD_URL", "http://localhost:8080")

    # --- Timeouts (seconds) ---
    OPA_HTTP_TIMEOUT = float(os.environ.get("OPA_HTTP_TIMEOUT", "5.0"))
    SCANNER_TIMEOUT = float(os.environ.get("SCANNER_TIMEOUT", "5.0"))
    SCANNER_SCAN_TIMEOUT = float(os.environ.get("SCANNER_SCAN_TIMEOUT", "300.0"))
    KAFKA_ADMIN_TIMEOUT = float(os.environ.get("KAFKA_ADMIN_TIMEOUT", "10.0"))
    TERRAFORM_TIMEOUT = float(os.environ.get("TERRAFORM_TIMEOUT", "120.0"))
    TERRAFORM_APPLY_TIMEOUT = float(os.environ.get("TERRAFORM_APPLY_TIMEOUT", "300.0"))
    ANSIBLE_TIMEOUT = float(os.environ.get("ANSIBLE_TIMEOUT", "120.0"))
    ARGOCD_HTTP_TIMEOUT = float(os.environ.get("ARGOCD_HTTP_TIMEOUT", "30.0"))
    KUBECTL_TIMEOUT = float(os.environ.get("KUBECTL_TIMEOUT", "30.0"))
    K8S_ACTION_TIMEOUT = float(os.environ.get("K8S_ACTION_TIMEOUT", "60.0"))
    DOCKER_TIMEOUT = float(os.environ.get("DOCKER_TIMEOUT", "5.0"))
    HEALTH_CHECK_TIMEOUT = float(os.environ.get("HEALTH_CHECK_TIMEOUT", "3.0"))
    LOAD_TEST_HTTP_TIMEOUT = float(os.environ.get("LOAD_TEST_HTTP_TIMEOUT", "5.0"))
    LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "30.0"))
    LLM_HTTP_TIMEOUT = float(os.environ.get("LLM_HTTP_TIMEOUT", "60.0"))
    TASK_FUTURE_TIMEOUT = float(os.environ.get("TASK_FUTURE_TIMEOUT", "30.0"))
    SHUTDOWN_TIMEOUT = float(os.environ.get("SHUTDOWN_TIMEOUT", "30.0"))

    # --- Redis Cache ---
    L1_CACHE_MAX_SIZE = int(os.environ.get("L1_CACHE_MAX_SIZE", "1024"))
    L1_CACHE_TTL = int(os.environ.get("L1_CACHE_TTL", "60"))
    L2_CACHE_TTL = int(os.environ.get("L2_CACHE_TTL", "120"))
    REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", "3.0"))
    REDIS_SOCKET_TIMEOUT = float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5.0"))
    REDIS_HEALTH_TIMEOUT = float(os.environ.get("REDIS_HEALTH_TIMEOUT", "2.0"))
    REDIS_IDLE_TIMEOUT = int(os.environ.get("REDIS_IDLE_TIMEOUT", "300"))

    # --- ClickHouse ---
    CH_IDLE_TIMEOUT = int(os.environ.get("CH_IDLE_TIMEOUT", "300"))
    CH_SEND_RECEIVE_TIMEOUT = int(os.environ.get("CH_SEND_RECEIVE_TIMEOUT", "10"))

    # --- Kafka Tuning ---
    KAFKA_BATCH_SIZE = int(os.environ.get("KAFKA_BATCH_SIZE", "16384"))
    KAFKA_LINGER_MS = int(os.environ.get("KAFKA_LINGER_MS", "10"))
    KAFKA_RETRIES = int(os.environ.get("KAFKA_RETRIES", "3"))
    KAFKA_RETRY_BACKOFF_MS = int(os.environ.get("KAFKA_RETRY_BACKOFF_MS", "100"))
    KAFKA_BUFFER_MEMORY = int(os.environ.get("KAFKA_BUFFER_MEMORY", "33554432"))
    KAFKA_MAX_IN_FLIGHT = int(os.environ.get("KAFKA_MAX_IN_FLIGHT", "5"))
    KAFKA_MAX_POLL_RECORDS = int(os.environ.get("KAFKA_MAX_POLL_RECORDS", "500"))
    KAFKA_SESSION_TIMEOUT = int(os.environ.get("KAFKA_SESSION_TIMEOUT", "30000"))
    KAFKA_HEARTBEAT_INTERVAL = int(os.environ.get("KAFKA_HEARTBEAT_INTERVAL", "10000"))
    KAFKA_AUTO_COMMIT_INTERVAL = int(os.environ.get("KAFKA_AUTO_COMMIT_INTERVAL", "5000"))

    # --- TTL / Intervals ---
    ENTITY_CACHE_TTL = int(os.environ.get("ENTITY_CACHE_TTL", "300"))
    ENTITY_REGISTRY_TTL = int(os.environ.get("ENTITY_REGISTRY_TTL", "86400"))
    ENTITY_RESOLUTION_TTL = int(os.environ.get("ENTITY_RESOLUTION_TTL", "604800"))
    BASELINE_CACHE_TTL = int(os.environ.get("BASELINE_CACHE_TTL", "3600"))
    WATCHDOG_CHECK_INTERVAL = float(os.environ.get("WATCHDOG_CHECK_INTERVAL", "10.0"))
    WATCHDOG_MAX_BACKOFF = float(os.environ.get("WATCHDOG_MAX_BACKOFF", "60.0"))
    WATCHDOG_CPU_BUDGET = float(os.environ.get("WATCHDOG_CPU_BUDGET", "1.0"))
    WATCHDOG_MEMORY_LIMIT_MB = int(os.environ.get("WATCHDOG_MEMORY_LIMIT_MB", "512"))
    ASYNC_MAX_WORKERS = int(os.environ.get("ASYNC_MAX_WORKERS", "8"))
    ASYNC_MAX_HISTORY = int(os.environ.get("ASYNC_MAX_HISTORY", "500"))
    API_CACHE_TTL = int(os.environ.get("API_CACHE_TTL", "30"))
    DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "50"))

    # --- NQL ---
    NQL_HOT_MAX_HOURS = int(os.environ.get("NQL_HOT_MAX_HOURS", "1"))
    NQL_WARM_MAX_DAYS = int(os.environ.get("NQL_WARM_MAX_DAYS", "90"))
    NQL_COLD_STORE_PATH = os.environ.get("NQL_COLD_STORE_PATH", "/tmp/omniwatch-cold")

    # --- Topology ---
    TOPOLOGY_QUERY_LIMIT = int(os.environ.get("TOPOLOGY_QUERY_LIMIT", "500"))
    TOPOLOGY_EDGES_LIMIT = int(os.environ.get("TOPOLOGY_EDGES_LIMIT", "1000"))
    TOPOLOGY_NEIGHBORS_LIMIT = int(os.environ.get("TOPOLOGY_NEIGHBORS_LIMIT", "50"))
    TOPOLOGY_BLAST_RADIUS_LIMIT = int(os.environ.get("TOPOLOGY_BLAST_RADIUS_LIMIT", "100"))
    GRAPH_QUERY_LIMIT = int(os.environ.get("GRAPH_QUERY_LIMIT", "1000"))
    BLAST_RADIUS_MAX_DEPTH = int(os.environ.get("BLAST_RADIUS_MAX_DEPTH", "5"))
    CAUSAL_MAX_DEPTH = int(os.environ.get("CAUSAL_MAX_DEPTH", "5"))
    GRANGER_MIN_P = float(os.environ.get("GRANGER_MIN_P", "0.05"))

    # --- AI/ML ---
    LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2048"))
    ANOMALY_Z_THRESHOLD = float(os.environ.get("ANOMALY_Z_THRESHOLD", "3.0"))
    EWMA_ALPHA = float(os.environ.get("EWMA_ALPHA", "0.3"))
    EWMA_THRESHOLD = float(os.environ.get("EWMA_THRESHOLD", "3.0"))
    IQR_MULTIPLIER = float(os.environ.get("IQR_MULTIPLIER", "1.5"))
    BOCPD_THRESHOLD = float(os.environ.get("BOCPD_THRESHOLD", "0.95"))
    MIN_ANOMALY_SCORE = float(os.environ.get("MIN_ANOMALY_SCORE", "0.25"))
    LSTM_LOOKBACK = int(os.environ.get("LSTM_LOOKBACK", "24"))
    LSTM_EPOCHS = int(os.environ.get("LSTM_EPOCHS", "50"))
    LSTM_HIDDEN_SIZE = int(os.environ.get("LSTM_HIDDEN_SIZE", "32"))
    LSTM_MIN_PER_STEP = float(os.environ.get("LSTM_MIN_PER_STEP", "5.0"))
    FORECAST_MIN_PER_STEP = float(os.environ.get("FORECAST_MIN_PER_STEP", "5.0"))

    # --- OTLP ---
    OTLP_GRPC_PORT = int(os.environ.get("OTLP_GRPC_PORT", "4317"))
    OTLP_HTTP_PORT = int(os.environ.get("OTLP_HTTP_PORT", "4318"))

    # --- Federation ---
    FEDERATION_HEALTH_TIMEOUT = int(os.environ.get("FEDERATION_HEALTH_TIMEOUT", "10"))

    # --- Business/Cost ---
    COST_PER_KWH = float(os.environ.get("COST_PER_KWH", "0.10"))
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")

    # --- Benchmark/Testing ---
    BENCHMARK_API_TIMEOUT = float(os.environ.get("BENCHMARK_API_TIMEOUT", "5.0"))
    LOAD_TEST_TIMEOUT = float(os.environ.get("LOAD_TEST_TIMEOUT", "30.0"))
    PATTERN_MINER_CONFIDENCE = float(os.environ.get("PATTERN_MINER_CONFIDENCE", "0.7"))

    # --- Policy ---
    POLICY_SEVERITY_CUTOFF = os.environ.get("POLICY_SEVERITY_CUTOFF", "P2")
    POLICY_CONFIDENCE_CUTOFF = float(os.environ.get("POLICY_CONFIDENCE_CUTOFF", "0.7"))
    POLICY_MAX_BLAST_RADIUS = int(os.environ.get("POLICY_MAX_BLAST_RADIUS", "5"))


config = Config()
