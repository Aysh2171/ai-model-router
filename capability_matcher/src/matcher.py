"""
Capability Matcher Core Feasibility Engine.
Executes a 5-stage early-exit evaluation sequence matching model catalog capabilities against request technical requirements.
"""

import uuid
from typing import Dict, Any, Optional, List
from model_registry.src import ModelRegistry, ModelInfo
from .requirements import MatchRequirements, RequirementExtractor
from .candidate import CandidateModel, ExcludedModel, CapabilityMatchResult


class CapabilityMatcher:
    """Core evaluation engine performing deterministic technical feasibility matching."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        """Initialize CapabilityMatcher with a ModelRegistry catalog instance."""
        self.registry = registry or ModelRegistry()

    def match(
        self,
        request_payload: Dict[str, Any],
        complexity_profile: Optional[Dict[str, Any]] = None,
        **options: Any
    ) -> CapabilityMatchResult:
        """
        Evaluate all registered foundation models against requirements extracted from request_payload.
        Returns a CapabilityMatchResult containing eligible candidate models and detailed audit traces for excluded models.
        """
        request_id = request_payload.get("request_id") or str(uuid.uuid4())[:8]

        # 1. Extract Requirements
        requirements = RequirementExtractor.extract(
            request_payload,
            complexity_profile=complexity_profile,
            **options
        )

        all_models = self.registry.get_all_models()
        eligible_candidates: List[CandidateModel] = []
        excluded_models: List[ExcludedModel] = []

        # 2. Execute 5-Stage Feasibility Pipeline for each registered model
        for model in all_models:
            rejection_reasons: List[str] = []
            matched_notes: List[str] = []

            # --- STAGE 1: Status & Lifecycle Check ---
            if model.status == "deprecated" and not requirements.allow_deprecated:
                rejection_reasons.append("Model status is 'deprecated' (allow_deprecated=False)")
            elif model.status == "preview" and not requirements.allow_preview:
                rejection_reasons.append("Model status is 'preview' (allow_preview=False)")
            else:
                matched_notes.append(f"Lifecycle Status: '{model.status}' satisfied")

            # --- STAGE 2: Modality Subset Check ---
            model_mods = {mod.lower() for mod in model.supported_modalities}
            missing_modalities = requirements.required_modalities - model_mods
            if missing_modalities:
                for mod in sorted(list(missing_modalities)):
                    rejection_reasons.append(f"Missing required modality: '{mod}'")
            else:
                matched_notes.append(f"Modalities {sorted(list(requirements.required_modalities))} supported")

            # --- STAGE 3: Boolean Capability Flags Check ---
            for cap_flag, req_value in requirements.required_capabilities.items():
                if req_value:
                    model_has_cap = getattr(model, cap_flag, False)
                    if not model_has_cap:
                        rejection_reasons.append(f"Missing required capability flag: '{cap_flag}'")
                    else:
                        matched_notes.append(f"Capability '{cap_flag}' verified")

            # --- STAGE 4: Context Window & Output Token Capacity Check ---
            if model.context_window < requirements.min_context_window:
                rejection_reasons.append(
                    f"Insufficient context window: Required {requirements.min_context_window:,} tokens > Model capacity {model.context_window:,} tokens"
                )
            else:
                headroom = model.context_window - requirements.min_context_window
                matched_notes.append(f"Context Window {model.context_window:,} tokens >= Required {requirements.min_context_window:,} (Headroom: {headroom:,} tokens)")

            if model.max_output_tokens < requirements.min_max_output_tokens:
                rejection_reasons.append(
                    f"Insufficient max output tokens: Required {requirements.min_max_output_tokens:,} tokens > Model limit {model.max_output_tokens:,} tokens"
                )

            # --- STAGE 5: Use Case Set Subset Check ---
            model_use_cases = {uc.lower() for uc in model.supported_use_cases}
            missing_use_cases = {
                uc for uc in requirements.required_use_cases
                if uc.lower() not in model_use_cases
            }
            if missing_use_cases:
                for uc in sorted(list(missing_use_cases)):
                    rejection_reasons.append(f"Missing required use case: '{uc}'")
            elif requirements.required_use_cases:
                matched_notes.append(f"Use Cases {sorted(list(requirements.required_use_cases))} supported")

            # --- EVALUATION DECISION ---
            if rejection_reasons:
                excluded_models.append(
                    ExcludedModel(
                        model_id=model.model_id,
                        provider=model.provider,
                        exclusion_reasons=rejection_reasons,
                    )
                )
            else:
                headroom = model.context_window - requirements.min_context_window
                eligible_candidates.append(
                    CandidateModel(
                        model_id=model.model_id,
                        provider=model.provider,
                        family=model.family,
                        model_info=model,
                        context_headroom=headroom,
                        matched_constraints=matched_notes,
                        matched_constraint_count=len(matched_notes),
                    )
                )

        is_satisfiable = len(eligible_candidates) > 0
        profile_dict = complexity_profile or {}

        return CapabilityMatchResult(
            request_id=request_id,
            is_satisfiable=is_satisfiable,
            complexity_profile=profile_dict,
            requirements=requirements,
            eligible_candidates=eligible_candidates,
            excluded_models=excluded_models,
            total_registered=len(all_models),
            eligible_count=len(eligible_candidates),
            excluded_count=len(excluded_models),
        )
