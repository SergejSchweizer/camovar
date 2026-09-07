from __future__ import annotations

from portfell.app_services.multivariate_compute import _objective_score, _select_decision
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


def test_decision_tie_breaks_turnover_then_hhi_then_configuration() -> None:
    class Candidate:
        def __init__(self, candidate_id: str, configuration_id: str) -> None:
            self.candidate_id = candidate_id
            self.candidate_configuration_id = configuration_id
            self.method = "equal_weight"
            self.status = "feasible"

    scorecards = [
        CandidateScorecard("c1", "equal_weight", 4, 0.1, 0.0, 0.2, 0, (), candidate_configuration_id="cfg-b", median_sharpe_ratio=1.0, median_turnover=0.2, median_herfindahl_index=0.1),
        CandidateScorecard("c2", "equal_weight", 4, 0.1, 0.0, 0.2, 0, (), candidate_configuration_id="cfg-a", median_sharpe_ratio=1.0, median_turnover=0.1, median_herfindahl_index=0.9),
    ]
    result = _select_decision(
        objective="return_risk",
        candidates=[Candidate("c1", "cfg-b"), Candidate("c2", "cfg-a")],
        scorecards=scorecards,
        splits=[],
        scenarios=[],
    )
    assert result.winning_candidate_id == "c2"
