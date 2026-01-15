"""
Unit tests for advanced SAGA modules.
"""
import pytest
from saga.mode_controller import ModeController, OperationMode
from saga.termination import TerminationChecker, TerminationConfig
from saga.search.generators import (
    AnalysisReport, 
    EvoGenerator, 
    ParetoSelector,
)
from saga.modules.advanced_analyzer import AdvancedAnalyzer
from saga.modules.advanced_planner import AdvancedPlanner
from saga.modules.advanced_implementer import AdvancedImplementer


class TestModeController:
    """Tests for ModeController."""
    
    def test_default_mode_is_semi_pilot(self):
        controller = ModeController()
        assert controller.mode == OperationMode.SEMI_PILOT
    
    def test_switch_mode(self):
        controller = ModeController()
        controller.switch_mode(OperationMode.AUTOPILOT)
        assert controller.mode == OperationMode.AUTOPILOT
    
    def test_requires_human_review_copilot_always_true(self):
        controller = ModeController(OperationMode.CO_PILOT)
        assert controller.requires_human_review("analyze") is True
        assert controller.requires_human_review("plan") is True
        assert controller.requires_human_review("implement") is True
    
    def test_requires_human_review_autopilot_always_false(self):
        controller = ModeController(OperationMode.AUTOPILOT)
        assert controller.requires_human_review("analyze") is False
        assert controller.requires_human_review("plan") is False
    
    def test_requires_human_review_semipilot_only_analyze(self):
        controller = ModeController(OperationMode.SEMI_PILOT)
        assert controller.requires_human_review("analyze") is True
        assert controller.requires_human_review("plan") is False
    
    def test_get_status(self):
        controller = ModeController()
        status = controller.get_status()
        assert "mode" in status
        assert "review_stages" in status
        assert status["mode"] == "semi-pilot"


class TestTerminationChecker:
    """Tests for TerminationChecker."""
    
    def test_max_iterations_reached(self):
        config = TerminationConfig(max_iters=5)
        checker = TerminationChecker(config)
        
        class MockState:
            iteration = 5
            score_history = [0.5, 0.6, 0.7, 0.8, 0.9]
            pareto_history = []
            analysis_reports = []
        
        assert checker.should_stop(MockState()) is True
        assert "max iterations" in checker.get_termination_reason(MockState()).lower()
    
    def test_not_terminated_below_max(self):
        config = TerminationConfig(max_iters=10)
        checker = TerminationChecker(config)
        
        class MockState:
            iteration = 3
            score_history = [0.5, 0.6, 0.7]
            pareto_history = []
            analysis_reports = []
            best_score = 0.7
        
        assert checker.should_stop(MockState()) is False
    
    def test_convergence_detection(self):
        config = TerminationConfig(max_iters=100, convergence_eps=0.01, convergence_patience=3)
        checker = TerminationChecker(config)
        
        class MockState:
            iteration = 5
            score_history = [0.5, 0.6, 0.7, 0.7, 0.7, 0.7]  # Last 3 are same
            pareto_history = []
            analysis_reports = []
        
        # Should detect convergence
        assert checker._is_converged(MockState().score_history) is True


class TestEvoGenerator:
    """Tests for EvoGenerator."""
    
    def test_generate_candidates(self):
        generator = EvoGenerator(mutation_rate=0.5, crossover_rate=0.7)
        population = ["candidate A", "candidate B", "candidate C"]
        feedback = AnalysisReport(
            score_distribution={},
            goal_achievement={},
            pareto_count=0,
            improvement_trend=0.0,
            bottleneck="unknown",
            suggested_constraints=[],
            iteration=1
        )
        
        new_candidates = generator.generate(population, feedback, num_candidates=5)
        assert len(new_candidates) == 5
        assert generator.get_name() == "EvoGenerator"


class TestParetoSelector:
    """Tests for ParetoSelector."""
    
    def test_select_top_k(self):
        selector = ParetoSelector()
        candidates = ["A", "B", "C", "D"]
        scores = [
            [0.8, 0.6, 0.7],
            [0.5, 0.9, 0.4],
            [0.9, 0.9, 0.9],  # Best
            [0.3, 0.3, 0.3],
        ]
        weights = [0.33, 0.34, 0.33]
        
        selected = selector.select(candidates, scores, weights, top_k=2)
        assert len(selected) == 2
        assert selected[0][0] == "C"  # Highest weighted score


class TestAdvancedAnalyzer:
    """Tests for AdvancedAnalyzer."""
    
    def test_run_basic(self):
        analyzer = AdvancedAnalyzer()
        state = {
            "candidates": ["test1", "test2"],
            "scores": [[0.8, 0.6], [0.5, 0.9]],
            "weights": [0.5, 0.5],
            "iteration": 1
        }
        
        result = analyzer.run(state)
        assert "score_distribution" in result
        assert "goal_achievement" in result
        assert "pareto_count" in result
        assert "bottleneck" in result


class TestAdvancedPlanner:
    """Tests for AdvancedPlanner."""
    
    def test_run_basic(self):
        planner = AdvancedPlanner()
        state = {
            "analysis": {
                "bottleneck": "goal_0",
                "goal_achievement": {"goal_0": 0.3, "goal_1": 0.8},
                "improvement_trend": 0.02
            },
            "constraints": [],
            "iteration": 3,
            "weights": [0.5, 0.5]
        }
        
        result = planner.run(state)
        assert "weights" in result
        assert "new_constraints" in result
        assert "strategy" in result


class TestAdvancedImplementer:
    """Tests for AdvancedImplementer."""
    
    def test_run_basic(self):
        implementer = AdvancedImplementer()
        state = {
            "plan": {"strategy": "exploration"},
            "constraints": [],
            "objectives": ["length", "keyword"]
        }
        
        result = implementer.run(state)
        assert "scoring_code" in result
        assert "is_valid" in result
        assert result["is_valid"] is True
    
    def test_generated_code_is_valid_python(self):
        implementer = AdvancedImplementer()
        state = {
            "plan": {},
            "constraints": [],
            "objectives": ["length", "keyword", "diversity"]
        }
        
        result = implementer.run(state)
        # Should be able to compile the code
        compile(result["scoring_code"], "<test>", "exec")
