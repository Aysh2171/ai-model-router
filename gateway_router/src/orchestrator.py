"""
End-to-End Pipeline Orchestrator.
Composes Modules 1 through 7 into a single unified routing-and-execution workflow without modifying previous modules.
"""

import sys
from typing import Dict, Any, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COMPLEXITY_DIR = PROJECT_ROOT / "complexity_predictor"
if str(COMPLEXITY_DIR) not in sys.path:
    sys.path.insert(0, str(COMPLEXITY_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from complexity_predictor.src.model import ComplexityPredictorModel
from model_registry.src import ModelRegistry
from capability_matcher.src import CapabilityMatcher
from rule_engine.src import RuleEngine, PolicyContext as RulePolicyContext
from ranking_engine.src import RankingEngine, RankingConfig
from policy_engine.src import PolicyEngine, PolicyContext as RuntimePolicyContext, UsageState

from .gateway import GatewayRouter
from .models import GatewayRequest, GatewayResponse
from .config import GatewayConfig


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "complexity_predictor" / "models" / "predictor_pipeline.joblib"


class PipelineRouter:
    """
    Convenience orchestrator executing the full 7-stage AI Model Router pipeline:
    Request -> M1 Complexity -> M3 Matcher (M2) -> M4 Rules -> M5 Ranking -> M6 Policy -> M7 Gateway.
    """

    def __init__(
        self,
        predictor: Optional[ComplexityPredictorModel] = None,
        registry: Optional[ModelRegistry] = None,
        matcher: Optional[CapabilityMatcher] = None,
        rule_engine: Optional[RuleEngine] = None,
        ranking_engine: Optional[RankingEngine] = None,
        policy_engine: Optional[PolicyEngine] = None,
        gateway: Optional[GatewayRouter] = None,
    ):
        if predictor is not None:
            self.predictor = predictor
        elif DEFAULT_MODEL_PATH.exists():
            self.predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))
        else:
            self.predictor = ComplexityPredictorModel()

        self.registry = registry or ModelRegistry()
        self.matcher = matcher or CapabilityMatcher(registry=self.registry)
        self.rule_engine = rule_engine or RuleEngine()
        self.ranking_engine = ranking_engine or RankingEngine()
        self.policy_engine = policy_engine or PolicyEngine()
        self.gateway = gateway or GatewayRouter()

    def route_and_execute(
        self,
        raw_request: Dict[str, Any],
        rule_context: Optional[RulePolicyContext] = None,
        ranking_config: Optional[RankingConfig] = None,
        runtime_policy_context: Optional[RuntimePolicyContext] = None,
        usage_state: Optional[UsageState] = None,
        simulation_options: Optional[Dict[str, Any]] = None,
    ) -> GatewayResponse:
        """
        Execute full end-to-end routing pipeline for a raw client request.

        Args:
            raw_request: Raw incoming request dictionary.
            rule_context: Optional Module 4 organizational policy context.
            ranking_config: Optional Module 5 ranking weights configuration.
            runtime_policy_context: Optional Module 6 runtime limits context.
            usage_state: Optional Module 6 in-memory tenant usage state.
            simulation_options: Optional Module 7 mock fault injection hooks.

        Returns:
            GatewayResponse containing execution status, generated response, and telemetry.
        """
        request_id = raw_request.get("request_id", "REQ-000")
        prompt = raw_request.get("prompt", "")

        # 1. Module 1 — Complexity Prediction
        complexity_profile = self.predictor.predict_complexity(raw_request)

        # 2. Module 3 — Capability Feasibility Matching (Queries Module 2 Registry)
        capability_match = self.matcher.match(
            request_payload=raw_request,
            complexity_profile=complexity_profile
        )

        # 3. Module 4 — Organizational Rule Evaluation
        rule_eval = self.rule_engine.evaluate(
            capability_match_result=capability_match,
            context=rule_context
        )

        # 4. Module 5 — Multi-Criteria Candidate Ranking
        ranking_result = self.ranking_engine.rank(
            rule_evaluation_result=rule_eval,
            config=ranking_config
        )

        # 5. Module 6 — Runtime Policy Enforcement & Bounded Fallback
        policy_decision = self.policy_engine.evaluate(
            ranking_result=ranking_result,
            context=runtime_policy_context,
            usage_state=usage_state
        )

        # 6. Module 7 — Gateway Provider Execution
        gateway_request = GatewayRequest(
            request_id=request_id,
            prompt=prompt,
            policy_decision=policy_decision,
            simulation_options=simulation_options,
            metadata={
                "complexity_profile": complexity_profile,
                "feasible_candidate_count": capability_match.eligible_count,
                "allowed_candidate_count": rule_eval.allowed_count,
                "ranked_candidate_count": ranking_result.total_candidates,
            }
        )

        return self.gateway.execute(gateway_request)
