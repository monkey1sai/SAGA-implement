
import logging
from saga.search.routers import MathStrategy
from saga.search.generators import AnalysisReport

# Mock AnalysisReport
dataset = [(0, -2), (1, 2), (2, 8)]
report = AnalysisReport(
    score_distribution={},
    goal_achievement={},
    pareto_count=5,
    improvement_trend=0.15,
    bottleneck="精確度",
    suggested_constraints=["增加二次項權重"],
    iteration=1,
    raw_data={"dataset": dataset}
)

population = ["x + 1"]

strategy = MathStrategy()
prompt = strategy.build_prompt(population, report, 5)

print("=== Generated Prompt ===")
print(prompt)

print("\n=== Testing Parser ===")
llm_output = """
Sure, here are some better formulas:
1. x**2 + 3*x - 2
2. FORMULA: (x+1)**2 + x - 3
3. 2*x**2 - 5
"""
candidates = strategy.parse_candidates(llm_output, 5)
print(f"Parsed Candidates: {candidates}")

assert "[(0, -2), (1, 2), (2, 8)]" in prompt
assert "專案背景" in prompt
assert "x**2 + 3*x - 2" in candidates
assert "(x+1)**2 + x - 3" in candidates

print("\nVerifications Passed!")
