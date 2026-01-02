# SGLang Production Server

本地部署的 SGLang 推論服務，針對 **RTX 4060 Ti 8GB** 優化，支援多人併發與複雜 Tool Use。

## 📋 系統需求

| 項目 | 需求 |
|-----|------|
| **GPU** | NVIDIA RTX 4060 Ti 8GB |
| **驅動** | NVIDIA Driver 525+ |
| **CUDA** | 12.1+ |
| **Docker** | Docker Desktop with WSL2 |
| **RAM** | 16GB+ (建議 32GB) |

## 🚀 快速開始

### 1. 配置環境

```powershell
# 複製環境變數範本
cp .env.example .env

# 編輯 .env，填入必要配置
# 務必設定 SGLANG_API_KEY
```

### 2. 啟動服務

```powershell
docker compose up -d
```

### 3. 執行壓力測試

```powershell
# 使用專用的基準測試腳本
..\.venv\Scripts\python.exe benchmark_final.py --concurrency 20 --total 50
```

## 📦 推薦模型 (RTX 4060 Ti 8GB)

| 模型 | VRAM 用量 | 說明 |
|-----|----------|------|
| `Qwen/Qwen2.5-3B-Instruct` | ~6GB | 中英文表現佳 |
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3GB | **預設**，輕量且速度極快 |

## 🔧 核心優勢 (SGLang)

1. **RadixAttention**: 自動快取 System Prompt 與 Tool 定義，顯著降低重複請求的延遲。
2. **結構化輸出優化**: 針對 JSON Schema (Function Calling) 有極佳的生成速度。
3. **高效併發**: 連續批次處理 (Continuous Batching) 充分利用 GPU 算力。

## 📁 專案結構

```
sglang-server/
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 環境變數範本
├── benchmark_final.py      # 最終壓力測試與監控腳本
├── benchmark_report.md     # 效能測試報告
├── nginx/                  # Nginx 反向代理配置
└── monitoring/             # Prometheus 監控配置
```