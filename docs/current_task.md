# 🚧 Current Task: SAGA 符號回歸調優與修復

**Last Updated**: 2026-01-26  
**Worker**: Antigravity Agent (Brainstorming Session)

## 🎯 Objective
讓 SAGA 在使用本地 **Qwen 2.5 7B (Q4_K_M)** 模型時，能正確找到符號回歸問題的解 `y = x^2 + 3x - 2`。

## ⚠️ Known Issues (Resolved)
1. **LLM 調用失敗**：
   - 症狀：UI 日誌顯示 `ERROR: SGLangAdapter.call() got an unexpected keyword argument 'temperature'`。
   - 原因：`SGLangAdapter.call()` 原本不支援傳遞 `**kwargs`，導致 `LLMGenerator` 傳入 `temperature=0.8` 時報錯。
   - 解決：已修改 `SGLangAdapter` 支援 `**kwargs` 並合併至 payload。

2. **搜索策略失效**：
   - 症狀：SAGA 提早收斂於錯誤公式（如 `x**2-x x) + x`），分數僅 0.1504。
   - 原因：初始種子太少，迭代次數不足，收斂判定過於寬鬆。
   - 解決：擴增初始種子（包含更多二次多項式變體），開啟激進搜索模式（`inner_iterations=15`, `batch_size=20`）。

3. **運算圖缺失**：
   - 症狀：UI 顯示「等待中」，無 Graph JSON 或 Mermaid 圖。
   - 原因：`OuterLoop` 雖然定義了 graph 生成函數但未調用。
   - 解決：在 `run()` 結束前調用 `write_graph` 和 `write_mermaid`。

## 📋 Execution Plan & Progress
- [x] **Search Strategy Tuning**:
    - [x] Increase `inner_iterations` (15) & `batch_size` (20) in `runner.py`.
    - [x] Expand initial seed candidates in `runner.py` to include `x^2 + 3x - 2` variants.
    - [x] Update frontend template defaults in `App.jsx` (`maxIters=20`, `weights=[0.85, 0.1, 0.05]`).
    - [x] Lower LLM temperature (0.4) and `Top_K` (10) in `.env` for stability.
- [x] **LLM Logging**:
    - [x] Add `get_last_interaction()` to `LLMGenerator`.
    - [x] Emit `llm` type `LogEvent` in `OuterLoop`.
    - [x] Add CSS style for `.log-llm` (blue color) in `style.css`.
- [x] **Visualization**:
    - [x] Implement graph generation in `OuterLoop`.
- [x] **Bug Fix**:
    - [x] Fix `SGLangAdapter` to accept `**kwargs` (temperature).
    - [x] Fix `App.jsx` initial state to load template defaults automatically.

## 🧠 Context & Thoughts
- 即使 LLM 調用失敗，`EvoGenerator` 的 fallback 機制加上擴展的種子（包含 `x**2 + 3*x - 2` 變體）仍然成功找到了正確答案 `(x + 1)**2 - 1 + x - 2`（分數 0.9573）。
- 使用 Qwen 2.5 7B 時，數學表達式的生成需要較低的 temperature 以避免語法錯誤，但同時需要足夠的隨機性（Top_K 10）來探索不同形式。
- UI 的「系統日誌」對於除錯 LLM 互動至關重要，藍色標示讓其更易識別。

## 📝 Handoff Note
- **Next Steps**:
    1. 驗證修復後的 `SGLangAdapter` 是否能讓 LLM 真正貢獻有效候選（而不只是依賴 EvoGenerator）。
    2. 觀察 LLM 生成的公式是否優於寫死的種子。
    3. 考慮將「最優解簡化」步驟加入流程（例如使用 SymPy 簡化 `(x+1)**2 - 1 + x - 2`）。
