from __future__ import annotations

from portfell.app_services.multivariate_compute import _objective_score
from portfell.multivariate_validation import CandidateScorecard


def test_return_risk_objective_uses_persisted_median_oos_sharpe() -> None:
    scorecard = CandidateScorecard(
        candidate_id="candidate-1",
        method="equal_weight",
        completed_split_count=4,
        median_post_cost_return=0.2,
        adverse_post_cost_return=-0.1,
        median_volatility=0.4,
        scenario_count=4,
        availability_reasons=(),
        median_sharpe_ratio=1.25,
    )
    assert _objective_score("return_risk", scorecard, ()) == 1.25


def test_return_drawdown_objective_uses_persisted_same_split_ratio() -> None:
    scorecard = CandidateScorecard(
        "candidate-1", "equal_weight", 4, 0.2, -0.1, 0.4, 4, (),
        median_return_drawdown_ratio=0.75,
    )
    assert _objective_score("return_drawdown", scorecard, ()) == 0.75
