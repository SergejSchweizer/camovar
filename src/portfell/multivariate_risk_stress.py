"""Asset-level covariance stress diagnostics for Multivariate candidates.

Stress results are descriptive evidence only: they never participate in
candidate ranking or production eligibility decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from typing import Any

from portfell.contract_versioning import ContractVersion
from portfell.multivariate_candidates import PortfolioCandidate
from portfell.multivariate_risk_model import MultivariateRiskModelArtifact

RISK_STRESS_CONTRACT = ContractVersion("multivariate.risk_stress", 1)
VOLATILITY_UP_25PCT = "volatility_up_25pct"


@dataclass(frozen=True)
class RiskStressResult:
    scenario: str
    status: str
    reason: str | None
    candidate_id: str
    candidate_configuration_id: str
    risk_model_id: str
    stressed_variance: float | None
    stressed_volatility: float | None

    def to_row(self) -> dict[str, Any]:
        return {"contract_version": RISK_STRESS_CONTRACT.qualified_name, **asdict(self)}


def volatility_up_25pct(
    *, risk_model: MultivariateRiskModelArtifact, candidate: PortfolioCandidate
) -> RiskStressResult:
    """Scale every asset volatility by 1.25 while preserving correlations."""

    identity = candidate.candidate_configuration_id or candidate.candidate_id
    base = dict(
        scenario=VOLATILITY_UP_25PCT,
        candidate_id=candidate.candidate_id,
        candidate_configuration_id=identity,
        risk_model_id=risk_model.risk_model_id,
    )
    if not risk_model.available or candidate.status != "feasible":
        return RiskStressResult(
            **base, status="unavailable", reason="risk_model_or_candidate_unavailable",
            stressed_variance=None, stressed_volatility=None,
        )
    n = len(risk_model.listings)
    if n == 0 or len(risk_model.covariance) != n or any(len(row) != n for row in risk_model.covariance):
        return RiskStressResult(
            **base, status="unavailable", reason="covariance_shape_invalid",
            stressed_variance=None, stressed_volatility=None,
        )
    weights = [0.0] * n
    index = {key: i for i, key in enumerate(risk_model.listings)}
    for key, value in candidate.weights:
        if key not in index or not isfinite(value):
            return RiskStressResult(
                **base, status="unavailable", reason="candidate_weights_invalid",
                stressed_variance=None, stressed_volatility=None,
            )
        weights[index[key]] = value
    # Multiplying each standard deviation by 1.25 scales every covariance
    # element by 1.25² while leaving the correlation matrix unchanged.
    scale = 1.25 * 1.25
    variance = sum(
        weights[i] * weights[j] * float(risk_model.covariance[i][j]) * scale
        for i in range(n) for j in range(n)
    )
    if not isfinite(variance) or variance < -1e-12:
        return RiskStressResult(
            **base, status="unavailable", reason="stressed_variance_invalid",
            stressed_variance=None, stressed_volatility=None,
        )
    variance = max(0.0, variance)
    return RiskStressResult(
        **base, status="available", reason=None,
        stressed_variance=variance, stressed_volatility=sqrt(variance),
    )


__all__ = [
    "RISK_STRESS_CONTRACT",
    "VOLATILITY_UP_25PCT",
    "RiskStressResult",
    "volatility_up_25pct",
]
