"""Sanitized evidence assembler used by migration QA stages."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def comparison_contract_evidence(
    *, sha: str, configurations: Sequence[Mapping[str, Any]], policy: Mapping[str, int],
    focused_tests: Sequence[str],
) -> dict[str, Any]:
    """Build the immutable stage-1 evidence payload without financial data."""
    return {
        "contract": "portfolio-selection-v2-migration@v1",
        "sha": sha,
        "stage": "comparison_contract_frozen",
        "stage_ordinal": 1,
        "completed_implementation_prs": ["PR461"],
        "completed_qa_prs": ["PR462"],
        "selection_authority": "legacy_lw_full",
        "comparison_configuration_count": len(configurations),
        "comparison_split_policy": dict(policy),
        "comparison_split_policy_fingerprint": "",
        "split_local_three_spec_risk_fits": False,
        "fourteen_split_local_candidates": False,
        "common_oos_metrics_measured": False,
        "config_keyed_scorecards_authoritative": False,
        "decision_v2_consumes_common_oos": False,
        "full_sample_family_materialized": False,
        "exact_lineage_joins": False,
        "checkpoint_resume_compatible": True,
        "dash_persisted_selection_read_only": True,
        "legacy_authority_retired": False,
        "focused_tests": list(focused_tests),
        "status": "PASS",
        "failure_reasons": [],
    }
