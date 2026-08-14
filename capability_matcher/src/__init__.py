"""
Capability Matcher Package Initializer.
Exposes CapabilityMatcher, RequirementExtractor, MatchRequirements, CandidateModel, ExcludedModel, and CapabilityMatchResult.
"""

from .requirements import MatchRequirements, RequirementExtractor, TASK_CATEGORY_ALIAS_MAP
from .candidate import CandidateModel, ExcludedModel, CapabilityMatchResult
from .matcher import CapabilityMatcher

__all__ = [
    "MatchRequirements",
    "RequirementExtractor",
    "TASK_CATEGORY_ALIAS_MAP",
    "CandidateModel",
    "ExcludedModel",
    "CapabilityMatchResult",
    "CapabilityMatcher",
]
