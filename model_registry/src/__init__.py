"""
Model Registry Package Initializer.
Exposes ModelInfo dataclass and ModelRegistry query API.
"""

from .model import ModelInfo
from .model_registry import ModelRegistry

__all__ = ["ModelInfo", "ModelRegistry"]
