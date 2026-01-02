# 人體救助行為偵測系統 (Human Distress Detection System)

此專案旨在利用姿態辨識技術偵測人體在不同情境下的求救行為，並結合高效能 LLM 推論後端進行情境分析與自動化處理，提供即時預警與援助。

---

## 🎯 求救情境偵測

本系統針對以下三種關鍵求救情境進行即時監測：

### 1. 雙手舉起揮手救助 (Waving for Help)
*   **偵測重點**：雙手手腕關節位置高於頭部，且具備規律性的水平位移特徵。

### 2. 行進間或站立跌倒 (Fall Detection)
*   **偵測重點**：身體重心高度在短時間內劇烈下降，且最終呈現水平姿勢。

### 3. 呼吸道阻塞 (Choking Detection)
*   **偵測重點**：雙手靠近頸部區域，且伴隨身體前傾或焦慮不安的姿態特徵。

---

## 🚀 推論核心架構 (Inference Backend)

為了處理複雜的場景邏輯與工具調用 (Tool Use)，我們部署了基於 **SGLang** 優化的推論伺服器，專為 NVIDIA RTX 4060 Ti (8GB) 優化。

### 核心特性
*   **引擎**：SGLang (優化結構化輸出與 Tool Use)。
*   **模型**：Qwen2.5-1.5B-Instruct。
*   **前綴快取 (RadixAttention)**：自動快取重複的工具定義與系統提示詞，將首字延遲 (TTFT) 降低至 **0.2s** 以下。
*   **高併發處理**：支援 20+ 使用者同時連線，展現極高的吞吐能力。

### 效能實測 (RTX 4060 Ti)
經由自研壓力測試腳本 `sglang-server/benchmark_final.py` 實測：
*   **系統總吞吐量 (TPS)**：**~600 tokens/s** 🔥
*   **反應延遲 (TTFT)**：**~0.17s**
*   **成功率**：100% (在高併發壓力測試下穩定運作)

---

## 🛠️ 快速啟動

### 1. 啟動推論伺服器 (SGLang)
```powershell
cd sglang-server
docker compose up -d
```

### 2. 執行效能基準測試
```powershell
# 模擬 20 個併發請求
..\.venv\Scripts\python.exe sglang-server\benchmark_final.py --concurrency 20 --total 50
```

---

## 📁 專案結構
*   `sglang-server/`：高效能推論伺服器配置與部署。
    *   `docker-compose.yml`：SGLang 服務定義。
    *   `benchmark_final.py`：全功能壓力測試與資源監控腳本。
    *   `benchmark_report.md`：詳細效能報告。
*   `README.md`：專案概覽與基礎指南。

---
*本專案推論後端已由 Gemini CLI 代理完成優化。*