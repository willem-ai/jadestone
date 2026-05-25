"""
Model fallback chain: graceful degradation when primary models are unavailable.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class VisionModelTier(Enum):
    QWEN_VL_MAX = "qwen-vl-max"
    QWEN_VL_PLUS = "qwen-vl-plus"
    QWEN_VL_72B_SELFHOST = "qwen2.5-vl-72b-selfhost"
    DEMO = "demo"


class ReasoningModelTier(Enum):
    DEEPSEEK_PRO = "deepseek-reasoner"
    DEEPSEEK_FLASH = "deepseek-chat"
    QWEN_MAX_TEXT = "qwen-max"
    DEMO = "demo"


class FallbackState:
    """Tracks which models are currently healthy."""

    def __init__(self):
        self.vision_tier: VisionModelTier = VisionModelTier.QWEN_VL_MAX
        self.reasoning_tier: ReasoningModelTier = ReasoningModelTier.DEEPSEEK_PRO
        self.vision_failures: dict[str, int] = {}
        self.reasoning_failures: dict[str, int] = {}

    def record_vision_failure(self, model: str):
        self.vision_failures[model] = self.vision_failures.get(model, 0) + 1
        self._update_vision_tier()

    def record_vision_success(self, model: str):
        self.vision_failures[model] = 0
        if model == VisionModelTier.QWEN_VL_MAX.value:
            self.vision_tier = VisionModelTier.QWEN_VL_MAX

    def record_reasoning_failure(self, model: str):
        self.reasoning_failures[model] = self.reasoning_failures.get(model, 0) + 1
        self._update_reasoning_tier()

    def record_reasoning_success(self, model: str):
        self.reasoning_failures[model] = 0
        if model == ReasoningModelTier.DEEPSEEK_PRO.value:
            self.reasoning_tier = ReasoningModelTier.DEEPSEEK_PRO

    def _update_vision_tier(self):
        """Demote vision model tier based on failure counts."""
        max_fail = max(self.vision_failures.values()) if self.vision_failures else 0
        if max_fail >= 5 and self.vision_tier == VisionModelTier.QWEN_VL_MAX:
            self.vision_tier = VisionModelTier.QWEN_VL_PLUS
            logger.warning("Vision model degraded: QWEN_VL_MAX → QWEN_VL_PLUS")
        elif max_fail >= 5 and self.vision_tier == VisionModelTier.QWEN_VL_PLUS:
            self.vision_tier = VisionModelTier.QWEN_VL_72B_SELFHOST
            logger.warning("Vision model degraded: QWEN_VL_PLUS → Self-hosted")
        elif max_fail >= 5:
            self.vision_tier = VisionModelTier.DEMO
            logger.warning("All vision models degraded → DEMO MODE")

    def _update_reasoning_tier(self):
        """Demote reasoning model tier based on failure counts."""
        max_fail = max(self.reasoning_failures.values()) if self.reasoning_failures else 0
        if max_fail >= 5 and self.reasoning_tier == ReasoningModelTier.DEEPSEEK_PRO:
            self.reasoning_tier = ReasoningModelTier.DEEPSEEK_FLASH
            logger.warning("Reasoning model degraded: DEEPSEEK_PRO → DEEPSEEK_FLASH")
        elif max_fail >= 5 and self.reasoning_tier == ReasoningModelTier.DEEPSEEK_FLASH:
            self.reasoning_tier = ReasoningModelTier.QWEN_MAX_TEXT
            logger.warning("Reasoning model degraded: DEEPSEEK_FLASH → QWEN_MAX")
        elif max_fail >= 5:
            self.reasoning_tier = ReasoningModelTier.DEMO
            logger.warning("All reasoning models degraded → DEMO MODE")

    @property
    def is_demo_mode(self) -> bool:
        return (
            self.vision_tier == VisionModelTier.DEMO
            or self.reasoning_tier == ReasoningModelTier.DEMO
        )


# Global fallback state
fallback_state = FallbackState()
