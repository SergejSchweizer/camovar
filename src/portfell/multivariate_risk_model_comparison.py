"""Shadow comparison manifest for the frozen 14 risk-model configurations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import Executor
from typing import Any

from portfell.contract_versioning import ContractVersion
from portfell.income import IncomeEvidence
from portfell.multivariate_candidates import build_candidate_set
from portfell.multivariate_inputs import MultivariateInputSnapshot, MultivariateListingKey
from portfell.multivariate_risk_model import build_multivariate_risk_model
from portfell.multivariate_risk_spec import EWMA_094, LW_FULL, LW_ROLLING_252, RiskModelSpecification
from portfell.multivariate_validation import DEFAULT_WALK_FORWARD_POLICY, _walk_forward_starts

RISK_MODEL_COMPARISON_CONTRACT = ContractVersion("multivariate.risk_model_comparison", 1)
COMPARISON_SPECS = (LW_FULL, LW_ROLLING_252, EWMA_094)
COMPARISON_METHODS = {
    "equal_weight": ("LW_FULL",),
    "inverse_volatility": ("LW_FULL", "LW_ROLLING_252", "EWMA_094"),
    "minimum_variance": ("LW_FULL", "LW_ROLLING_252", "EWMA_094"),
    "equal_risk_contribution": ("LW_FULL", "LW_ROLLING_252", "EWMA_094"),
    "hierarchical_risk_parity": ("LW_FULL", "LW_ROLLING_252", "EWMA_094"),
    "minimum_cvar": ("LW_FULL",),
}


def build_risk_model_comparison(
    *, snapshot: MultivariateInputSnapshot, return_rows: Sequence[Mapping[str, Any]],
    income: Mapping[MultivariateListingKey, IncomeEvidence], executor: Executor | None = None,
) -> dict[str, Any]:
    """Build the deterministic shadow manifest and current full-sample evidence."""
    models: dict[str, Any] = {}
    for spec in COMPARISON_SPECS:
        models[spec.spec_key] = build_multivariate_risk_model(
            snapshot=snapshot, return_rows=return_rows, spec=spec
        )
    definitions: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    split_evidence: list[dict[str, Any]] = []
    dates = _common_dates(return_rows, snapshot.listing_keys)
    starts = _walk_forward_starts(dates, DEFAULT_WALK_FORWARD_POLICY)
    for method, spec_keys in COMPARISON_METHODS.items():
        for spec_key in spec_keys:
            spec = next(item for item in COMPARISON_SPECS if item.spec_key == spec_key)
            model = models[spec_key]
            definitions.append({"method": method, "spec_key": spec.spec_key, "spec_id": spec.spec_id})
            candidates = build_candidate_set(
                snapshot=snapshot, risk_model=model, return_rows=return_rows,
                income=income, executor=executor
            )
            evidence.extend({
                "method": candidate.method,
                "spec_key": spec.spec_key,
                "spec_id": spec.spec_id,
                "candidate_id": candidate.candidate_id,
                "candidate_configuration_id": candidate.candidate_configuration_id,
                "status": candidate.status,
                "reason": candidate.reasons[0] if candidate.reasons else None,
            } for candidate in candidates if candidate.method == method)
            for start in starts:
                split_evidence.append({
                    "split_index": starts.index(start),
                    "train_start": dates[0] if dates else None,
                    "train_end": dates[start - 1] if start else None,
                    "test_start": dates[start] if start < len(dates) else None,
                    "test_end": dates[min(len(dates) - 1, start + DEFAULT_WALK_FORWARD_POLICY.test_window_observations - 1)] if dates else None,
                    "method": method,
                    "spec_key": spec.spec_key,
                    "spec_id": spec.spec_id,
                    "status": "scheduled",
                })
    return {
        "contract_version": RISK_MODEL_COMPARISON_CONTRACT.qualified_name,
        "configuration_count": len(definitions),
        "configurations": definitions,
        "full_sample_evidence": evidence,
        "common_split_count": len(starts),
        "common_split_evidence": split_evidence,
        "risk_models": {
            key: {"risk_model_id": model.risk_model_id, "fit_calendar_id": model.fit_calendar_id,
                  "status": "available" if model.available else "unavailable"}
            for key, model in models.items()
        },
    }


__all__ = ["COMPARISON_METHODS", "COMPARISON_SPECS", "RISK_MODEL_COMPARISON_CONTRACT", "build_risk_model_comparison"]


def _common_dates(
    rows: Sequence[Mapping[str, Any]], listings: Sequence[MultivariateListingKey]
) -> tuple[str, ...]:
    indexed = {key: set() for key in listings}
    for row in rows:
        key = MultivariateListingKey.from_row(row)
        if key in indexed:
            indexed[key].add(str(row.get("date", "")))
    if not indexed:
        return ()
    common = set.intersection(*(dates for dates in indexed.values()))
    return tuple(sorted(item for item in common if item))
