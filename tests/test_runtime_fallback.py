import pytest
from unittest.mock import MagicMock
from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.models import GatewayRequest, GatewayResponse, ExecutionStatus, ExecutionMode
from policy_engine.src import PolicyDecision, DecisionState
from ranking_engine.src import RankingResult, RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo
from policy_engine.src.context import PolicyContext as RuntimePolicyContext

def create_mock_ranked_model(rank, model_id, provider):
    info = ModelInfo(
        provider=provider, family=provider, model_id=model_id, display_name=model_id,
        description="mock", status="available", is_default=False, tags=[],
        context_window=1000, max_output_tokens=100, cost_tier="low",
        latency_tier="fast", supported_modalities=["text"], supported_use_cases=[]
    )
    cand = CandidateModel(model_id=model_id, provider=provider, family=provider, model_info=info, context_headroom=1000)
    return RankedModel(model_id=model_id, provider=provider, family=provider, candidate=cand, overall_score=10.0/rank, rank_position=rank)

@pytest.fixture
def mock_pipeline():
    router = PipelineRouter()
    
    # Mock predictor, matcher, rule_engine, ranking_engine to return a stable result
    router.predictor.predict_complexity = MagicMock(return_value={"complexity": "low"})
    router.matcher.match = MagicMock(return_value=MagicMock(eligible_count=3))
    router.rule_engine.evaluate = MagicMock(return_value=MagicMock(allowed_count=3))
    
    return router

def test_a_single_fallback(mock_pipeline):
    """Test A: Provider A timeout -> Provider B success -> B response returned"""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    
    ranking_result = RankingResult("R1", True, 2, [model_a, model_b])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    # Policy Engine behavior: return the FIRST item in the ranked_candidates list that is evaluated.
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    # Gateway Router behavior
    def mock_gateway_exec(req):
        if req.policy_decision.selected_model.model_id == "model_a":
            return GatewayResponse("R1", ExecutionStatus.TIMEOUT, error_message="Timeout!", execution_mode=ExecutionMode.MOCK.value)
        elif req.policy_decision.selected_model.model_id == "model_b":
            return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success from B", execution_mode=ExecutionMode.MOCK.value)
            
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp = mock_pipeline.route_and_execute({"request_id": "R1"})
    assert resp.status == ExecutionStatus.SUCCESS
    assert resp.content == "Success from B"
    assert mock_pipeline.gateway.execute.call_count == 2

def test_b_multiple_fallbacks(mock_pipeline):
    """Test B: Provider A failure -> Provider B failure -> Provider C success -> C response returned"""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    model_c = create_mock_ranked_model(3, "model_c", "ProviderC")
    
    ranking_result = RankingResult("R1", True, 3, [model_a, model_b, model_c])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    def mock_gateway_exec(req):
        mid = req.policy_decision.selected_model.model_id
        if mid == "model_a":
            return GatewayResponse("R1", ExecutionStatus.RETRY_EXHAUSTED, error_message="Exhausted", execution_mode=ExecutionMode.MOCK.value)
        elif mid == "model_b":
            return GatewayResponse("R1", ExecutionStatus.FAILED, error_message="Connection error", execution_mode=ExecutionMode.MOCK.value)
        elif mid == "model_c":
            return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success from C", execution_mode=ExecutionMode.MOCK.value)
            
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp = mock_pipeline.route_and_execute({"request_id": "R1"})
    assert resp.status == ExecutionStatus.SUCCESS
    assert resp.content == "Success from C"
    assert mock_pipeline.gateway.execute.call_count == 3

def test_c_all_fail(mock_pipeline):
    """Test C: All candidates fail -> Final failure response"""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    ranking_result = RankingResult("R1", True, 1, [model_a])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    def mock_gateway_exec(req):
        return GatewayResponse("R1", ExecutionStatus.TIMEOUT, error_message="Timeout!", execution_mode=ExecutionMode.MOCK.value)
        
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp = mock_pipeline.route_and_execute({"request_id": "R1"})
    assert resp.status == ExecutionStatus.TIMEOUT
    assert mock_pipeline.gateway.execute.call_count == 1

def test_d_no_fallback_needed(mock_pipeline):
    """Test D: First candidate succeeds -> no fallback attempted"""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    
    ranking_result = RankingResult("R1", True, 2, [model_a, model_b])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    def mock_gateway_exec(req):
        return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success from A", execution_mode=ExecutionMode.MOCK.value)
        
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp = mock_pipeline.route_and_execute({"request_id": "R1"})
    assert resp.status == ExecutionStatus.SUCCESS
    assert resp.content == "Success from A"
    assert mock_pipeline.gateway.execute.call_count == 1

def test_e_fallback_is_request_scoped(mock_pipeline):
    """Test E: Failed candidate is excluded only for current request -> future requests unaffected"""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    
    # Store original candidates list to check if it gets permanently mutated
    original_candidates = [model_a, model_b]
    
    # We must construct a new RankingResult each time to simulate a new request
    mock_pipeline.ranking_engine.rank = MagicMock(side_effect=lambda *args, **kwargs: RankingResult("R1", True, 2, list(original_candidates)))
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    # Request 1 fails on A, succeeds on B
    # Request 2 succeeds on A
    execution_state = {"req_count": 0}
    def mock_gateway_exec(req):
        mid = req.policy_decision.selected_model.model_id
        if execution_state["req_count"] == 0:
            if mid == "model_a":
                return GatewayResponse("R1", ExecutionStatus.FAILED, error_message="Server error", execution_mode=ExecutionMode.MOCK.value)
            return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success from B", execution_mode=ExecutionMode.MOCK.value)
        else:
            if mid == "model_a":
                return GatewayResponse("R2", ExecutionStatus.SUCCESS, content="Success from A", execution_mode=ExecutionMode.MOCK.value)
    
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp1 = mock_pipeline.route_and_execute({"request_id": "R1"})
    assert resp1.content == "Success from B"
    
    execution_state["req_count"] += 1
    resp2 = mock_pipeline.route_and_execute({"request_id": "R2"})
    assert resp2.content == "Success from A"

def test_f_fallback_preserves_order(mock_pipeline):
    """Test F: Original ranking order is preserved for fallback."""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    model_c = create_mock_ranked_model(3, "model_c", "ProviderC")
    
    ranking_result = RankingResult("R1", True, 3, [model_a, model_b, model_c])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    # We will track the sequence of models requested
    requested_sequence = []
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    def mock_gateway_exec(req):
        mid = req.policy_decision.selected_model.model_id
        requested_sequence.append(mid)
        if mid == "model_c":
            return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success", execution_mode=ExecutionMode.MOCK.value)
        return GatewayResponse("R1", ExecutionStatus.TIMEOUT, error_message="Timeout", execution_mode=ExecutionMode.MOCK.value)
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    mock_pipeline.route_and_execute({"request_id": "R1"})
    
    assert requested_sequence == ["model_a", "model_b", "model_c"]

def test_g_no_fallback_on_client_error(mock_pipeline):
    """Test G: Candidate A returns 400 Bad Request -> No cross-provider fallback -> Candidate B is not attempted."""
    model_a = create_mock_ranked_model(1, "model_a", "ProviderA")
    model_b = create_mock_ranked_model(2, "model_b", "ProviderB")
    
    ranking_result = RankingResult("R1", True, 2, [model_a, model_b])
    mock_pipeline.ranking_engine.rank = MagicMock(return_value=ranking_result)
    
    # We will track the sequence of models requested
    requested_sequence = []
    
    def mock_policy_eval(ranking_result, context, usage_state):
        if not ranking_result.ranked_candidates:
            return PolicyDecision("R1", DecisionState.NO_CANDIDATE, None, None, False, 0, [], [], {})
        selected = ranking_result.ranked_candidates[0]
        return PolicyDecision("R1", DecisionState.APPROVED, selected, selected.rank_position, False, 0, [], [], {})
    mock_pipeline.policy_engine.evaluate = MagicMock(side_effect=mock_policy_eval)
    
    def mock_gateway_exec(req):
        mid = req.policy_decision.selected_model.model_id
        requested_sequence.append(mid)
        if mid == "model_a":
            # Simulate a client-side 400 bad request error
            return GatewayResponse("R1", ExecutionStatus.FAILED, error_message="400 Bad Request: Invalid payload", execution_mode=ExecutionMode.MOCK.value)
        return GatewayResponse("R1", ExecutionStatus.SUCCESS, content="Success", execution_mode=ExecutionMode.MOCK.value)
        
    mock_pipeline.gateway.execute = MagicMock(side_effect=mock_gateway_exec)
    
    resp = mock_pipeline.route_and_execute({"request_id": "R1"})
    
    # Assert that only model_a was attempted
    assert requested_sequence == ["model_a"]
    # Assert that the final response is the failure from model_a
    assert resp.status == ExecutionStatus.FAILED
    assert "400" in resp.error_message
