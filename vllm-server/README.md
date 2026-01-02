# vLLM Production Server

本地部署的 vLLM 推論服務，針對 **RTX 4060 Ti 8GB** 優化，支援多人併發使用。

## 📋 系統需求

| 項目 | 需求 |
|-----|------|
| **GPU** | NVIDIA RTX 4060 Ti 8GB |
| **驅動** | NVIDIA Driver 525+ |
| **CUDA** | 12.1+ |
| **Docker** | Docker Desktop with WSL2 |
| **RAM** | 16GB+ (建議 32GB) |

## 🚀 快速開始

### 1. 安裝前置需求 (Windows)

```powershell
# 1. 安裝 Docker Desktop
# 下載: https://www.docker.com/products/docker-desktop/

# 2. 安裝 NVIDIA Container Toolkit
# 參考: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# 3. 驗證 GPU 支援
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### 2. 配置環境

```powershell
# 複製環境變數範本
cp .env.example .env

# 編輯 .env，填入必要配置
notepad .env
```

**必填項目:**
- `VLLM_API_KEY`: API 認證金鑰 (自訂強密碼)
- `HF_TOKEN`: HuggingFace Token (部分模型需要)

### 3. 啟動服務

```powershell
# 使用 PowerShell 腳本
.\scripts\start.ps1

# 或手動啟動
docker compose up -d
```

### 4. 測試 API

```powershell
# 使用測試腳本
.\scripts\test-api.ps1 -SkipSSL

# 或使用 curl
curl -k -X POST https://localhost/v1/chat/completions `
  -H "Authorization: Bearer your-api-key" `
  -H "Content-Type: application/json" `
  -d '{"model": "Qwen/Qwen2.5-3B-Instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## 📦 推薦模型 (RTX 4060 Ti 8GB)

| 模型 | VRAM 用量 | 說明 |
|-----|----------|------|
| `Qwen/Qwen2.5-3B-Instruct` | ~6GB | **預設**，中英文表現佳 |
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3GB | 輕量版，更快回應 |
| `microsoft/Phi-3-mini-4k-instruct` | ~5GB | 微軟出品，英文佳 |
| `TheBloke/Mistral-7B-Instruct-v0.2-GPTQ` | ~5GB | 量化版 Mistral 7B |

> ⚠️ 8GB VRAM 限制下，無法運行完整的 7B+ 非量化模型

## 🔧 配置參數說明

### docker-compose.yml 關鍵參數

```yaml
command: >
  --model Qwen/Qwen2.5-3B-Instruct    # 模型名稱
  --max-model-len 4096                 # 最大上下文長度
  --gpu-memory-utilization 0.85        # GPU 記憶體使用率
  --max-num-seqs 16                    # 最大併發序列數
  --max-num-batched-tokens 4096        # 批次 token 上限
  --enable-prefix-caching              # 前綴快取 (加速重複 prompt)
  --dtype half                         # 使用 FP16 節省記憶體
```

### 性能調優建議

| 場景 | 建議配置 |
|-----|---------|
| **低延遲優先** | `--max-num-seqs 8`, `--max-model-len 2048` |
| **高吞吐量優先** | `--max-num-seqs 32`, `--max-model-len 4096` |
| **記憶體不足** | 使用 1.5B 模型或降低 `gpu-memory-utilization` |

## 📊 監控 (可選)

啟動 Prometheus + Grafana 監控:

```powershell
docker compose --profile monitoring up -d
```

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (預設: admin/admin123)

### 關鍵監控指標

| 指標 | 說明 |
|-----|------|
| `vllm:num_requests_running` | 執行中請求數 |
| `vllm:num_requests_waiting` | 等待中請求數 |
| `vllm:gpu_cache_usage_perc` | GPU KV Cache 使用率 |
| `vllm:avg_generation_throughput` | 平均生成吞吐量 (tokens/s) |

## 🔒 安全性

### API 認證

所有請求需在 Header 中包含:
```
Authorization: Bearer <your-api-key>
```

### HTTPS

- 開發環境使用自簽憑證
- 生產環境請替換為正式 CA 憑證 (如 Let's Encrypt)

### Rate Limiting

Nginx 已配置:
- 每 IP 每秒 10 個請求
- 每 IP 最大 10 個併發連接

## 🛠️ 常用指令

```powershell
# 查看日誌
docker compose logs -f vllm

# 重啟服務
docker compose restart vllm

# 停止服務
docker compose down

# 完全清理 (包含 volumes)
docker compose down -v

# 更新映像
docker compose pull && docker compose up -d
```

## ❓ 常見問題

### Q: CUDA out of memory

**A:** 嘗試以下方案:
1. 使用更小的模型 (如 1.5B)
2. 降低 `--max-model-len` 至 2048
3. 降低 `--gpu-memory-utilization` 至 0.8
4. 減少 `--max-num-seqs` 至 8

### Q: 首次啟動很慢

**A:** 首次啟動需下載模型 (~6GB)，請耐心等待。可透過以下指令觀察進度:
```powershell
docker compose logs -f vllm
```

### Q: API 回應 401 Unauthorized

**A:** 檢查:
1. `.env` 中的 `VLLM_API_KEY` 是否正確設定
2. 請求 Header 中的 `Authorization` 格式是否為 `Bearer <key>`

## 📁 專案結構

```
vllm-server/
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 環境變數範本
├── .env                    # 環境變數 (不納入版控)
├── nginx/
│   ├── nginx.conf          # Nginx 配置
│   └── certs/              # SSL 憑證
├── monitoring/
│   └── prometheus.yml      # Prometheus 配置
├── scripts/
│   ├── start.ps1           # Windows 啟動腳本
│   ├── start.sh            # Linux/Mac 啟動腳本
│   ├── test-api.ps1        # API 測試腳本
│   └── generate-certs.sh   # SSL 憑證生成
└── logs/                   # 日誌目錄
```

## 📄 License

MIT License
