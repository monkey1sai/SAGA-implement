"""
Operation mode controller for SAGA human-AI collaboration.

Implements three operation modes with different levels of human oversight:
- Co-pilot: Human reviews every step
- Semi-pilot: Human reviews only analysis reports (default)
- Autopilot: Fully autonomous until termination
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Set

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Available operation modes for SAGA."""
    CO_PILOT = "co-pilot"       # Human reviews every step
    SEMI_PILOT = "semi-pilot"   # Human reviews only analysis reports
    AUTOPILOT = "autopilot"     # Fully autonomous until termination


# Define which stages require review for each mode
MODE_REVIEW_STAGES: dict[OperationMode, Set[str]] = {
    OperationMode.CO_PILOT: {"analyze", "plan", "implement", "optimize"},
    OperationMode.SEMI_PILOT: {"analyze"},
    OperationMode.AUTOPILOT: set(),
}


class ModeController:
    """Controls operation mode and determines when human review is needed.
    
    Attributes:
        mode: Current operation mode
        review_stages: Set of stages that require human review
    """
    
    def __init__(self, default_mode: OperationMode = OperationMode.SEMI_PILOT):
        """Initialize controller with default mode.
        
        Args:
            default_mode: Initial operation mode (default: Semi-pilot)
        """
        self._mode = default_mode
        self._review_stages = MODE_REVIEW_STAGES[default_mode].copy()
        logger.info(f"[ModeController] Initialized with mode: {self._mode.value}")
    
    @property
    def mode(self) -> OperationMode:
        """Get current operation mode."""
        return self._mode
    
    def switch_mode(self, new_mode: OperationMode) -> None:
        """Switch to a different operation mode.
        
        Args:
            new_mode: Target operation mode to switch to
        """
        old_mode = self._mode
        self._mode = new_mode
        self._review_stages = MODE_REVIEW_STAGES[new_mode].copy()
        logger.info(f"[ModeController] Switching mode: {old_mode.value} -> {new_mode.value}")
    
    def requires_human_review(self, stage: str) -> bool:
        """Check if given stage requires human review under current mode.
        
        Args:
            stage: Name of the stage (analyze, plan, implement, optimize)
            
        Returns:
            True if human review is required, False otherwise
        """
        result = stage.lower() in self._review_stages
        logger.debug(f"[ModeController] Stage '{stage}' requires review: {result} (mode={self._mode.value})")
        return result
    
    def add_review_stage(self, stage: str) -> None:
        """Add a stage to require human review.
        
        Useful for temporarily increasing oversight.
        
        Args:
            stage: Stage name to add to review requirements
        """
        self._review_stages.add(stage.lower())
        logger.info(f"[ModeController] Added review stage: {stage}")
    
    def remove_review_stage(self, stage: str) -> None:
        """Remove a stage from human review requirements.
        
        Args:
            stage: Stage name to remove from review requirements
        """
        self._review_stages.discard(stage.lower())
        logger.info(f"[ModeController] Removed review stage: {stage}")
    
    def get_status(self) -> dict:
        """Get current controller status for UI display.
        
        Returns:
            Dictionary with mode info and review stages
        """
        return {
            "mode": self._mode.value,
            "review_stages": list(self._review_stages),
            "mode_description": self._get_mode_description()
        }
    
    def _get_mode_description(self) -> str:
        """Get human-readable description of current mode."""
        descriptions = {
            OperationMode.CO_PILOT: "科學家深度參與。審核並修改每一由規劃器提出的新目標。適合高風險或探索性任務。",
            OperationMode.SEMI_PILOT: "人類僅對分析報告提供反饋。規劃與實作過程自動化，戰略方向由人引導。",
            OperationMode.AUTOPILOT: "完全自主運行。系統自動迭代直至滿足終止條件。適合大規模搜尋任務。",
        }
        return descriptions.get(self._mode, "")
    
    def to_dict(self) -> dict:
        """Serialize controller state for persistence or transmission."""
        return {
            "mode": self._mode.value,
            "review_stages": list(self._review_stages)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ModeController":
        """Create controller from serialized state.
        
        Args:
            data: Dictionary with mode and review_stages
            
        Returns:
            New ModeController instance
        """
        mode = OperationMode(data.get("mode", "semi-pilot"))
        controller = cls(default_mode=mode)
        if "review_stages" in data:
            controller._review_stages = set(data["review_stages"])
        return controller
