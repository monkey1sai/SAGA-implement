"""
Prompt Router for SAGA Generator.

Decides which prompt strategy to use based on the task context (keywords, data type).
Implements the "Code Review Router" pattern: routing tasks to the most appropriate
reasoning model (e.g. Math/Logic vs. General/Creative).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from saga.search.generators import AnalysisReport

logger = logging.getLogger(__name__)

class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies."""
    
    @abstractmethod
    def build_prompt(self, population: List[str], feedback: AnalysisReport, num: int) -> str:
        """Build the prompt for the specific strategy."""
        pass
    
    @abstractmethod
    def parse_candidates(self, raw_output: str, expected: int) -> List[str]:
        """Parse the LLM output into candidates."""
        pass


class GeneralStrategy(PromptStrategy):
    """Original SAGA prompt strategy with full analysis context."""
    
    def build_prompt(self, population: List[str], feedback: AnalysisReport, num: int) -> str:
        top_candidates = population[:3] if len(population) >= 3 else population
        
        return f"""你是一個科學發現助手。基於以下分析反饋，請生成 {num} 個改進的候選方案。

## 當前最佳候選
{chr(10).join(f'- {c}' for c in top_candidates)}

## 分析反饋
- 瓶頸目標: {feedback.bottleneck}
- 改善趨勢: {feedback.improvement_trend:.2%}
- 建議: {', '.join(feedback.suggested_constraints) if feedback.suggested_constraints else '無'}

## 要求
請生成 {num} 個新候選，每行一個，專注於改善瓶頸目標。
格式：
CANDIDATE: <候選內容>
"""

    def parse_candidates(self, raw_output: str, expected: int) -> List[str]:
        candidates = []
        for line in raw_output.split("\n"):
            if line.strip().startswith("CANDIDATE:"):
                content = line.split("CANDIDATE:", 1)[1].strip()
                if content:
                    candidates.append(content)
        return candidates[:expected]


class MathStrategy(PromptStrategy):
    """Codex-style strategy for Math/Symbolic Regression tasks.
    
    Focuses on raw data patterns and formula simplicity. 
    Removes bureaucratic meta-data.
    """
    
    def build_prompt(self, population: List[str], feedback: AnalysisReport, num: int) -> str:
        top = population[0] if population else "y = x"
        
        # Robust data retrieval from analysis report
        dataset = []
        if feedback.raw_data and "dataset" in feedback.raw_data:
            dataset = feedback.raw_data["dataset"]
        
        # Format dataset for prompt
        if dataset:
            # Show up to 10 points to avoid overflowing context
            dataset_str = f"{dataset[:10]}"
            if len(dataset) > 10:
                dataset_str += f" ... (total {len(dataset)} points)"
        else:
            dataset_str = "[(0,0), (1,1)] # Default (No data found)"

        current_formula = top

        # Construct Feedback Message (Traditional Chinese)
        feedback_msg = "尚無反饋。"
        if feedback:
            feedback_msg = f"""
- 當前分數提升: {feedback.improvement_trend:.2%}
- 瓶頸目標: {feedback.bottleneck}
- 審查員建議: {', '.join(feedback.suggested_constraints)}
"""

        prompt = f"""你是一個參與演化式代碼審查循環的數學推理代理 (Mathematical Reasoning Agent)。

# 專案背景 (PROJECT CONTEXT)
我們正在尋找一個 Python 公式 `y = f(x)` 來擬合以下數據集：
{dataset_str}

# 當前狀態 (CURRENT STATUS)
**當前最佳公式**: `{current_formula}`
**審查員反饋**:
{feedback_msg}

# 你的任務 (YOUR MISSION)
與審查員溝通並提出 {num} 個**更好**的公式。
1. **分析反饋**: 如果之前的公式失敗了（例如誤差太大），請假設原因（例如“需要二次項”，“係數太小”）。
2. **迭代**: 提出變體。
   - 如果當前是 `x`，嘗試 `x**2`。
   - 如果當前是 `x**2`，嘗試 `x**2 + x` 或 `(x-1)**2`。
3. **格式**: 僅輸出有效的 Python 表達式。

# 提案格式 (PROPOSAL FORMAT)
FORMULA: <expression>

# 範例
dataset: [(1,1), (2,4), (3,9)] -> FORMULA: x**2
dataset: [(1,3), (2,5), (3,7)] -> FORMULA: 2*x + 1

# 輪到你了 (請提出 {num} 個公式):
"""
        return prompt

    def parse_candidates(self, raw_output: str, expected: int) -> List[str]:
        import re
        candidates = []
        # Regex to allow standard python math characters
        allowed_pattern = re.compile(r"^[0-9a-zA-Z\.\+\-\*\/\(\)\,\=\s\_]+$")
        
        for line in raw_output.split("\n"):
            clean = line.strip()
            content = ""
            
            if clean.startswith("FORMULA:"):
                content = clean.split("FORMULA:", 1)[1].strip()
            # Handle list style output e.g. "1. x**2" or "2. FORMULA: ..."
            elif re.match(r"^\d+\.\s*", clean):
                parts = re.split(r"^\d+\.\s*", clean)
                if len(parts) > 1:
                    potential = parts[1].strip()
                    # Strip FORMULA: if present in list item
                    if potential.startswith("FORMULA:"):
                        potential = potential.split("FORMULA:", 1)[1].strip()
                        
                    # Basic validation: must look like math
                    if any(op in potential for op in ["+", "-", "*", "/", "**", "x"]):
                        content = potential

            if content:
                # 1. Sanity Check: Length and Garbage
                if content.count(",") > 3 or content.count("(") > 4 or len(content) > 100:
                    continue
                
                # 2. Strict Character Check (Anti-Hallucination Firewall)
                if not allowed_pattern.match(content):
                    logger.warning(f"[MathStrategy] Filtered invalid content: {content}")
                    continue
                
                # 3. Block common non-math words just in case
                if any(word in content.lower() for word in ["improve", "adjust", "formula", "candidate", "改進", "調整", "optimized"]):
                    continue
                    
                candidates.append(content)
        
        logger.info(f"[MathStrategy] Parsed {len(candidates)} valid formulas from LLM response.")
        return candidates[:expected]


class PromptRouter:
    """Routes tasks to the appropriate prompt strategy."""
    
    def __init__(self):
        self._strategies = {
            "general": GeneralStrategy(),
            "math": MathStrategy()
        }
    
    def get_strategy(self, keywords: List[str]) -> PromptStrategy:
        """Select strategy based on keywords."""
        math_keywords = ["formula", "equation", "regression", "symbolic", "math", "擬合", "公式", "回歸", "多項式", "x²"]
        
        if any(k in keywords for k in math_keywords):
            logger.info("[PromptRouter] Selected Strategy: MATH (Codex Mode)")
            return self._strategies["math"]
        
        logger.info("[PromptRouter] Selected Strategy: GENERAL")
        return self._strategies["general"]
