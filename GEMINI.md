# Human Distress Detection System (sglang Server Focus)

## Project Overview
This project aims to develop a **Human Distress Detection System** capable of identifying critical situations such as waving for help, falling, and choking using pose estimation.

Currently, the repository focuses on the **sglang Inference Server** (`sglang-server/`), a production-ready local LLM deployment optimized for **NVIDIA RTX 4060 Ti (8GB)**. It provides a reliable backend for natural language processing tasks, supporting complex agentic workflows.

## Key Components

### 1. sglang Server (SGLang Backend)
We have transitioned to **SGLang** (via `docker-compose.sglang.yml`) for superior performance in Tool Use and Agentic scenarios.
- **Port**: 8082 (Mapped to container 30000)
- **Engine**: SGLang (Optimized for structured output & RadixAttention)
- **Model**: Qwen/Qwen2.5-1.5B-Instruct
- **Features**:
    - **RadixAttention**: Caches common system prompts and tool schemas, drastically reducing latency for complex agents.
    - **Continuous Batching**: Handles high concurrency (20+ users) efficiently.

## Getting Started

### Prerequisites
- **OS**: Windows (with WSL2) or Linux.
- **GPU**: NVIDIA GPU with drivers installed.
- **Software**: Docker Desktop, NVIDIA Container Toolkit.

### Setup
1.  **Configure Environment**:
    Navigate to `sglang-server/` and create your environment file.
    ```powershell
    cd sglang-server
    cp .env.example .env
    # Edit .env to set SGLANG_API_KEY and HF_TOKEN
    ```

2.  **Start Services (SGLang)**:
    Use Docker Compose to start the optimized SGLang server.
    ```powershell
    docker compose up -d
    ```

3.  **Verify Deployment**:
    Wait for the model to load (check logs: `docker logs -f sglang-server`), then run the benchmark.

## Performance & Benchmarking

We provide a comprehensive stress-test script to validate the server's capability under complex agentic loads.

### Running the Benchmark
The `benchmark_final.py` script simulates a realistic high-load environment:
- **Complex Tool Schemas**: Nested objects, arrays, and enums.
- **Randomized Inputs**: Simulates diverse user intents.
- **Resource Monitoring**: Tracks GPU Utilization and VRAM usage.

```bash
# Run a stress test with 20 concurrent users and 50 total requests
python sglang-server/benchmark_final.py --concurrency 20 --total 50
```

### Performance Insights (RTX 4060 Ti)
- **High Concurrency**: Capable of handling ~20 concurrent complex requests with stable latency.
- **Throughput**: Achieves **600+ Tokens/s** system-wide throughput.
- **Latency (TTFT)**: **~0.2s** for cached prompts (thanks to RadixAttention), making it ideal for real-time agents.

## Project Structure

```
D:\._vscode2\detection_pose\
├── sglang-server/           # Main LLM service directory
│   ├── docker-compose.yml # Recommended SGLang orchestration
│   ├── benchmark_final.py # Ultimate stress test script
│   ├── benchmark_report.md# Detailed performance report
│   ├── .env.example       # Configuration template
│   ├── nginx/             # Proxy configuration & SSL
│   └── monitoring/        # Prometheus & Grafana config
├── AGENTS.md              # Existing agent context & guidelines
└── README.md              # Project vision (Distress Detection)
```

## Resources
- **Project Vision**: See [README.md](./README.md)
- **Server Documentation**: See [sglang-server/README.md](./sglang-server/README.md)