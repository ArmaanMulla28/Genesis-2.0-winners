"""
metrics.py - Evaluation Metrics Calculator for Self-Healing Tool Registry.

Calculates key reliability and recovery performance metrics based on structured
audit log events:
- Total recovery attempts
- Successful recoveries
- Failed recoveries
- Adaptation rate (%)
- Mean Time to Recovery (MTTR) in milliseconds
- Average retry count
- Patch rejection count
"""

from typing import Any, Dict, List, Optional
from app.audit import audit_logger


class RecoveryMetricsCalculator:
    """
    Computes statistical evaluation metrics from the recorded audit log events.
    """

    @classmethod
    def calculate_metrics(cls, events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Compute evaluation metrics from audit trail.

        Definitions & Boundaries:
        - Eligible Recovery Attempts: All requests where the recovery engine was engaged
          due to a runtime schema drift mismatch. Ordinary successful requests (natively valid)
          are intentionally excluded from the recovery denominator.
        - Adaptation Rate: (successful_recoveries / eligible_recovery_attempts) * 100.
          Returns 0.0 when no eligible recovery attempts have occurred.
        - Mean Time to Recovery (MTTR): The mean elapsed time, in milliseconds, measured from
          the detection of a recoverable schema failure (HTTP 422) to the completion of its
          successful recovery attempt and retried response (HTTP 200). Returns 0.0 when there are
          no successful recoveries.
        - Average Retry Count: The mean retry count across all recovery attempts.
        - Patch Rejection Count: Count of recovery attempts where patch validation failed or
          was rejected due to schema incompatibility.
        """
        if events is None:
            events = audit_logger.get_events()

        total_attempts = len(events)
        if total_attempts == 0:
            return {
                "total_recovery_attempts": 0,
                "successful_recoveries": 0,
                "failed_recoveries": 0,
                "eligible_recovery_attempts": 0,
                "adaptation_rate": 0.0,
                "mean_time_to_recovery_ms": 0.0,
                "average_retry_count": 0.0,
                "patch_rejection_count": 0,
                "dataset_status": "empty",
                "notes": "No recovery attempts recorded. Numerical metrics default to 0.0.",
            }

        successful = [
            e for e in events
            if e.get("recovery_outcome") == "SUCCESS" or e.get("final_outcome") == "SUCCESS"
        ]
        failed = [
            e for e in events
            if e.get("recovery_outcome") != "SUCCESS" and e.get("final_outcome") != "SUCCESS"
        ]

        successful_count = len(successful)
        failed_count = len(failed)
        eligible_attempts = total_attempts

        # Adaptation rate: % of eligible attempts successfully recovered
        adaptation_rate = (
            round((successful_count / eligible_attempts) * 100.0, 2)
            if eligible_attempts > 0
            else 0.0
        )

        # Mean Time to Recovery (MTTR) for successful recoveries in milliseconds
        successful_times = [
            float(e["elapsed_time_ms"])
            for e in successful
            if e.get("elapsed_time_ms") is not None
        ]
        mttr_ms = (
            round(sum(successful_times) / len(successful_times), 2)
            if len(successful_times) > 0
            else 0.0
        )

        # Average retry count across all attempts
        retry_counts = [int(e.get("retry_count", 0)) for e in events]
        avg_retries = (
            round(sum(retry_counts) / total_attempts, 2)
            if total_attempts > 0
            else 0.0
        )

        # Count of rejected patches
        patch_rejections = sum(
            1 for e in events
            if e.get("recovery_outcome") == "REJECTED"
            or "REJECTED" in str(e.get("patch_decision", "")).upper()
        )

        return {
            "total_recovery_attempts": total_attempts,
            "successful_recoveries": successful_count,
            "failed_recoveries": failed_count,
            "eligible_recovery_attempts": eligible_attempts,
            "adaptation_rate": adaptation_rate,
            "mean_time_to_recovery_ms": mttr_ms,
            "average_retry_count": avg_retries,
            "patch_rejection_count": patch_rejections,
            "dataset_status": "populated",
            "notes": "Calculated from in-memory audit log.",
        }
