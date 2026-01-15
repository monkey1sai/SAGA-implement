"""
Pluggable candidate generators for SAGA inner loop optimization.

This module provides abstract interfaces and implementations for different
candidate generation strategies: LLM-driven, evolutionary, RL, and Bayesian.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Analysis report from the Analyzer module."""
    score_distribution: Dict[str, Dict[str, float]]  # dim -> {min, max, avg, std}
    goal_achievement: Dict[str, float]  # goal_name -> achievement_rate
    pareto_count: int
    improvement_trend: float  # negative = regression, positive = improvement
    bottleneck: str  # most difficult goal
    suggested_constraints: List[str]
    iteration: int
    raw_data: Dict[str, Any] = None


class CandidateGenerator(ABC):
    """Abstract interface for candidate generation strategies.
    
    Implementations can use different algorithms:
    - LLM-driven: Use language models to generate candidates based on feedback
    - Evolutionary: Crossover and mutation on existing population
    - RL: Reinforcement learning policy network
    - Bayesian: Bayesian optimization with surrogate model
    """
    
    @abstractmethod
    def generate(
        self, 
        population: List[str], 
        feedback: AnalysisReport,
        num_candidates: int = 5
    ) -> List[str]:
        """Generate new candidates based on current population and feedback.
        
        Args:
            population: Current candidate population
            feedback: Analysis report from previous iteration
            num_candidates: Number of new candidates to generate
            
        Returns:
            List of newly generated candidates
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this generator strategy."""
        pass


class Selector(ABC):
    """Abstract interface for candidate selection strategies."""
    
    @abstractmethod
    def select(
        self,
        candidates: List[str],
        scores: List[List[float]],
        weights: List[float],
        top_k: int
    ) -> List[tuple[str, List[float]]]:
        """Select top-k candidates based on scores and weights.
        
        Args:
            candidates: List of candidate strings
            scores: Score vectors for each candidate
            weights: Objective weights for weighted scoring
            top_k: Number of candidates to select
            
        Returns:
            List of (candidate, score_vector) tuples, sorted by weighted score
        """
        pass


class Evaluator(Protocol):
    """Protocol for candidate evaluation functions."""
    
    def __call__(self, candidate: str, context: Dict[str, Any]) -> List[float]:
        """Evaluate a candidate and return score vector."""
        ...


# === Implementations ===

class LLMGenerator(CandidateGenerator):
    """LLM-driven candidate generator using SGLang.
    
    Uses the language model to generate new candidates based on:
    - Current best candidates
    - Analysis feedback (bottlenecks, suggested constraints)
    - Improvement trends
    """
    
    def __init__(self, client: Any):
        """Initialize with SGLang adapter client."""
        self.client = client
        logger.info("[LLMGenerator] Initialized with SGLang client")
    
    def generate(
        self, 
        population: List[str], 
        feedback: AnalysisReport,
        num_candidates: int = 5
    ) -> List[str]:
        logger.info(f"[LLMGenerator] Generating {num_candidates} candidates")
        logger.debug(f"[LLMGenerator] Population size: {len(population)}, Iteration: {feedback.iteration}")
        
        # Build prompt with feedback context
        prompt = self._build_prompt(population, feedback, num_candidates)
        
        try:
            response = self.client.call(prompt)
            raw_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            candidates = self._parse_candidates(raw_content, num_candidates)
            logger.info(f"[LLMGenerator] Generated {len(candidates)} candidates successfully")
            return candidates
        except Exception as e:
            logger.error(f"[LLMGenerator] Generation failed: {e}")
            # Fallback: return mutations of existing population
            return self._fallback_generate(population, num_candidates)
    
    def get_name(self) -> str:
        return "LLMGenerator"
    
    def _build_prompt(self, population: List[str], feedback: AnalysisReport, num: int) -> str:
        top_candidates = population[:3] if len(population) >= 3 else population
        
        prompt = f"""你是一個科學發現助手。基於以下分析反饋，請生成 {num} 個改進的候選方案。

## 當前最佳候選
{chr(10).join(f'- {c}' for c in top_candidates)}

## 分析反饋
- 瓶頸目標: {feedback.bottleneck}
- 改善趨勢: {feedback.improvement_trend:.2%}
- Pareto 前沿數量: {feedback.pareto_count}
- 建議約束: {', '.join(feedback.suggested_constraints) if feedback.suggested_constraints else '無'}

## 要求
請生成 {num} 個新候選，每行一個，格式：
CANDIDATE: <候選內容>

專注於改善瓶頸目標，同時維持其他目標的表現。"""
        
        return prompt
    
    def _parse_candidates(self, raw: str, expected: int) -> List[str]:
        candidates = []
        for line in raw.split("\n"):
            if line.strip().startswith("CANDIDATE:"):
                content = line.split("CANDIDATE:", 1)[1].strip()
                if content:
                    candidates.append(content)
        return candidates[:expected]
    
    def _fallback_generate(self, population: List[str], num: int) -> List[str]:
        """Fallback generation using simple string manipulation."""
        logger.warning("[LLMGenerator] Using fallback generation")
        results = []
        for i, p in enumerate(population[:num]):
            # Simple mutation: truncate or extend
            if i % 2 == 0 and len(p) > 10:
                results.append(p[:len(p)//2])
            else:
                results.append(p + "（改進版）")
        return results


class EvoGenerator(CandidateGenerator):
    """Evolutionary algorithm generator using crossover and mutation.
    
    Implements genetic algorithm operations for candidate evolution.
    """
    
    def __init__(self, mutation_rate: float = 0.1, crossover_rate: float = 0.7):
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        logger.info(f"[EvoGenerator] Initialized with mutation_rate={mutation_rate}, crossover_rate={crossover_rate}")
    
    def generate(
        self, 
        population: List[str], 
        feedback: AnalysisReport,
        num_candidates: int = 5
    ) -> List[str]:
        import random
        
        logger.info(f"[EvoGenerator] Generating {num_candidates} candidates via evolution")
        
        if len(population) < 2:
            logger.warning("[EvoGenerator] Population too small for crossover, using mutation only")
            return [self._mutate(population[0]) for _ in range(num_candidates)]
        
        new_candidates = []
        for _ in range(num_candidates):
            if random.random() < self.crossover_rate:
                parent1, parent2 = random.sample(population, 2)
                child = self._crossover(parent1, parent2)
            else:
                child = random.choice(population)
            
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
            
            new_candidates.append(child)
        
        logger.info(f"[EvoGenerator] Generated {len(new_candidates)} candidates")
        return new_candidates
    
    def get_name(self) -> str:
        return "EvoGenerator"
    
    def _crossover(self, parent1: str, parent2: str) -> str:
        """Single-point crossover."""
        mid1 = len(parent1) // 2
        mid2 = len(parent2) // 2
        return parent1[:mid1] + parent2[mid2:]
    
    def _mutate(self, candidate: str) -> str:
        """Simple mutation by character replacement or insertion."""
        import random
        if not candidate:
            return candidate
        
        pos = random.randint(0, len(candidate) - 1)
        mutations = ["優化", "改進", "增強", "調整"]
        mutation = random.choice(mutations)
        return candidate[:pos] + mutation + candidate[pos:]


class ParetoSelector(Selector):
    """Selector using Pareto dominance and weighted scoring."""
    
    def select(
        self,
        candidates: List[str],
        scores: List[List[float]],
        weights: List[float],
        top_k: int
    ) -> List[tuple[str, List[float]]]:
        logger.info(f"[ParetoSelector] Selecting top {top_k} from {len(candidates)} candidates")
        
        if not candidates or not scores:
            return []
        
        # Calculate weighted scores
        scored = []
        for i, (cand, score_vec) in enumerate(zip(candidates, scores)):
            if len(weights) == len(score_vec):
                weighted = sum(w * s for w, s in zip(weights, score_vec))
            else:
                weighted = sum(score_vec)
            scored.append((cand, score_vec, weighted))
        
        # Sort by weighted score descending
        scored.sort(key=lambda x: x[2], reverse=True)
        
        # Return top-k
        result = [(c, s) for c, s, _ in scored[:top_k]]
        logger.debug(f"[ParetoSelector] Selected candidates with scores: {[s for _, s in result]}")
        return result


class BeamSelector(Selector):
    """Simple beam search selector (wrapper for existing beam_search)."""
    
    def select(
        self,
        candidates: List[str],
        scores: List[List[float]],
        weights: List[float],
        top_k: int
    ) -> List[tuple[str, List[float]]]:
        from saga.search.beam import beam_search
        
        logger.info(f"[BeamSelector] Using beam search with width={top_k}")
        
        # Create scorer that returns pre-computed scores
        score_map = dict(zip(candidates, scores))
        
        def scorer(c: str) -> List[float]:
            return score_map.get(c, [0.0] * len(weights))
        
        return beam_search(candidates, scorer, top_k, weights)
