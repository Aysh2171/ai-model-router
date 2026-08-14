"""
Feedback Analytics Layer.
Computes aggregated metrics, latency averages, fallback frequencies, and quality distributions from historical data.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from .repository import FeedbackRepository
from .models import RoutingEvent, FeedbackRecord


class FeedbackAnalytics:
    """
    Lightweight analytical engine querying historical repository records to compute summary telemetry metrics.
    """

    def __init__(self, repository: FeedbackRepository):
        self.repository = repository

    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Compute top-level system health and volume summary metrics.
        """
        events = self.repository.list_events(limit=10000)
        total_requests = len(events)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate_pct": 0.0,
                "avg_latency_ms": 0.0,
                "avg_retry_count": 0.0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0
            }

        success_count = sum(1 for e in events if e.is_success)
        failed_count = total_requests - success_count
        total_latency = sum(e.latency_ms for e in events)
        total_retries = sum(e.retry_count for e in events)
        total_p_tokens = sum(e.prompt_tokens for e in events)
        total_c_tokens = sum(e.completion_tokens for e in events)
        total_toks = sum(e.total_tokens for e in events)

        return {
            "total_requests": total_requests,
            "successful_requests": success_count,
            "failed_requests": failed_count,
            "success_rate_pct": round((success_count / total_requests) * 100.0, 2),
            "avg_latency_ms": round(total_latency / total_requests, 2),
            "avg_retry_count": round(total_retries / total_requests, 2),
            "total_prompt_tokens": total_p_tokens,
            "total_completion_tokens": total_c_tokens,
            "total_tokens": total_toks
        }

    def get_routing_distribution(self) -> Dict[str, Any]:
        """
        Compute routing distributions: model selection, provider breakdown, fallback rates, and complexity tiers.
        """
        events = self.repository.list_events(limit=10000)
        total_requests = len(events)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "fallback_count": 0,
                "fallback_rate_pct": 0.0,
                "model_usage": {},
                "provider_usage": {},
                "complexity_distribution": {},
                "execution_status_distribution": {}
            }

        model_usage: Dict[str, int] = defaultdict(int)
        provider_usage: Dict[str, int] = defaultdict(int)
        complexity_dist: Dict[str, int] = defaultdict(int)
        status_dist: Dict[str, int] = defaultdict(int)
        fallback_count = 0

        for e in events:
            if e.fallback_used:
                fallback_count += 1
            if e.model_id:
                model_usage[e.model_id] += 1
            if e.provider:
                provider_usage[e.provider] += 1
            if e.complexity_tier:
                complexity_dist[e.complexity_tier] += 1
            status_dist[e.execution_status] += 1

        return {
            "total_requests": total_requests,
            "fallback_count": fallback_count,
            "fallback_rate_pct": round((fallback_count / total_requests) * 100.0, 2),
            "model_usage": dict(model_usage),
            "provider_usage": dict(provider_usage),
            "complexity_distribution": dict(complexity_dist),
            "execution_status_distribution": dict(status_dist)
        }

    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Compute feedback quality scores, rating distribution, and satisfaction percentages.
        """
        feedback_list = self.repository.list_all_feedback(limit=10000)
        total_feedback = len(feedback_list)
        if total_feedback == 0:
            return {
                "total_feedback_count": 0,
                "average_rating": 0.0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "satisfaction_rate_pct": 0.0,
                "quality_category_counts": {}
            }

        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        quality_counts: Dict[str, int] = defaultdict(int)
        total_rating_sum = 0
        satisfied_count = 0

        for f in feedback_list:
            rating_dist[f.rating] = rating_dist.get(f.rating, 0) + 1
            total_rating_sum += f.rating
            if f.rating >= 4:
                satisfied_count += 1
            if f.quality_category:
                quality_counts[f.quality_category] += 1

        return {
            "total_feedback_count": total_feedback,
            "average_rating": round(total_rating_sum / total_feedback, 2),
            "rating_distribution": rating_dist,
            "satisfaction_rate_pct": round((satisfied_count / total_feedback) * 100.0, 2),
            "quality_category_counts": dict(quality_counts)
        }

    def get_model_performance_summary(self) -> List[Dict[str, Any]]:
        """
        Compute per-model performance and quality summary breakdown.
        """
        events = self.repository.list_events(limit=10000)
        feedback_list = self.repository.list_all_feedback(limit=10000)

        # Map feedback ratings by event_id
        feedback_by_event: Dict[str, List[int]] = defaultdict(list)
        for f in feedback_list:
            feedback_by_event[f.event_id].append(f.rating)

        # Aggregate by model_id
        model_stats: Dict[str, Dict[str, Any]] = {}
        for e in events:
            if not e.model_id:
                continue
            m_id = e.model_id
            if m_id not in model_stats:
                model_stats[m_id] = {
                    "model_id": m_id,
                    "provider": e.provider or "Unknown",
                    "request_count": 0,
                    "success_count": 0,
                    "total_latency_ms": 0.0,
                    "total_tokens": 0,
                    "ratings": []
                }
            s = model_stats[m_id]
            s["request_count"] += 1
            if e.is_success:
                s["success_count"] += 1
            s["total_latency_ms"] += e.latency_ms
            s["total_tokens"] += e.total_tokens
            if e.event_id in feedback_by_event:
                s["ratings"].extend(feedback_by_event[e.event_id])

        result = []
        for m_id, s in model_stats.items():
            req_cnt = s["request_count"]
            succ_cnt = s["success_count"]
            ratings = s["ratings"]
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

            result.append({
                "model_id": m_id,
                "provider": s["provider"],
                "request_count": req_cnt,
                "success_count": succ_cnt,
                "success_rate_pct": round((succ_cnt / req_cnt) * 100.0, 2) if req_cnt > 0 else 0.0,
                "avg_latency_ms": round(s["total_latency_ms"] / req_cnt, 2) if req_cnt > 0 else 0.0,
                "avg_tokens": round(s["total_tokens"] / req_cnt, 1) if req_cnt > 0 else 0.0,
                "feedback_count": len(ratings),
                "avg_rating": avg_rating
            })

        # Sort by request count descending
        result.sort(key=lambda x: x["request_count"], reverse=True)
        return result

    def get_full_dashboard_summary(self) -> Dict[str, Any]:
        """
        Produce a unified analytical snapshot combining summary health, routing distribution, and quality metrics.
        """
        return {
            "summary": self.get_summary_metrics(),
            "routing_distribution": self.get_routing_distribution(),
            "quality_metrics": self.get_quality_metrics(),
            "model_performance": self.get_model_performance_summary()
        }
