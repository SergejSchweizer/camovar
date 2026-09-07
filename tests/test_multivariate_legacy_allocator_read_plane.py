from portfell.app_services.workspace import _without_retired_allocator


def test_read_plane_hides_retired_allocator_from_persisted_artifacts() -> None:
    document = {
        "items": [
            {"method": "equal_weight", "candidate_id": "new"},
            {"method": "highest_monthly_return", "candidate_id": "old"},
        ]
    }
    cleaned = _without_retired_allocator(document, "candidates")
    assert [row["method"] for row in cleaned["items"]] == ["equal_weight"]
    assert document["items"][1]["method"] == "highest_monthly_return"


def test_performance_read_plane_hides_retired_allocator_series() -> None:
    cleaned = _without_retired_allocator(
        {"portfolio_series": [{"method": "highest_monthly_return"}, {"method": "equal_weight"}]},
        "performance",
    )
    assert cleaned["portfolio_series"] == [{"method": "equal_weight"}]
