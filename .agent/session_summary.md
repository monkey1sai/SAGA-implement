# SGLang 遷移與優化工作總結 (2026-01-02)

本文件紀錄了從 vLLM 遷移至 **SGLang** 的完整過程與最終技術架構。

## 1. 核心變更 (Core Changes)
*   **引擎遷移**: 全面捨棄 vLLM，改用 **SGLang** 作為推論後端，以獲得更好的 Tool Use 效能。
*   **目錄重命名**: `vllm-server/` -> `sglang-server/`。
*   **配置優化**: 統一使用 `docker-compose.yml` 部署 SGLang，優化了 8GB VRAM 環境下的 Cache 策略。
*   **環境變數**: `VLLM_API_KEY` 統一更名為 `SGLANG_API_KEY`。

## 2. 測試工具升級
*   **建立 `benchmark_final.py`**:
    *   支援複雜的巢狀工具 (Nested Tool Schemas) 測試。
    *   內建 GPU (Utilization & VRAM) 與 CPU 背景監控。
    *   自動生成詳細的 TPS 與 RPS 效能報告。
*   **環境清理**: 刪除了所有舊版的基準測試腳本與不相容的 Shell Scripts。

## 3. 效能表現 (@ RTX 4060 Ti 8GB)
*   **首字延遲 (TTFT)**: **~0.17s** (RadixAttention 發揮極大作用)。
*   **系統吞吐量**: **600+ tokens/s** (20 併發下)。
*   **穩定性**: 在高壓測試下 100% 成功率。

## 4. 檔案與目錄結構
*   `sglang-server/`:
    *   `docker-compose.yml`: SGLang 核心服務。
    *   `benchmark_final.py`: 推薦的效能測試入口。
    *   `benchmark_report.md`: 測試數據存檔。
    *   `nginx/`, `monitoring/`: 代理與監控。

## 5. 重啟後的操作
1.  進入 `sglang-server/`。
2.  執行 `docker compose up -d`。
3.  使用 `python benchmark_final.py` 驗證效能。

---
**備註**: 專案中已完全移除所有 vLLM 相關程式碼與文字引用。
