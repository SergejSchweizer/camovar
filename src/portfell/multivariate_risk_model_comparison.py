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
            } for candidate in candidates)
    return {
        "contract_version": RISK_MODEL_COMPARISON_CONTRACT.qualified_name,
        "configuration_count": len(definitions),
        "configurations": definitions,
        "full_sample_evidence": evidence,
        "risk_models": {
            key: {"risk_model_id": model.risk_model_id, "fit_calendar_id": model.fit_calendar_id,
                  "status": "available" if model.available else "unavailable"}
            for key, model in models.items()
        },
    }


__all__ = ["COMPARISON_METHODS", "COMPARISON_SPECS", "RISK_MODEL_COMPARISON_CONTRACT", "build_risk_model_comparison"]
