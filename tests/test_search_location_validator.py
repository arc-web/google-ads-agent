from __future__ import annotations

from shared.validators.search.search_location_validator import SearchLocationValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def location_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Location": "Ashburn, Virginia, United States",
        "Location ID": "1027067",
        "Status": "Enabled",
    }
    row.update(overrides)
    return row


def test_accepts_location_with_numeric_location_id():
    issues = SearchLocationValidator().validate_location_row(location_row(), 2)

    assert issues == []


def test_warns_when_location_id_is_missing_for_named_location():
    issues = SearchLocationValidator().validate_location_row(location_row(**{"Location ID": ""}), 2)

    assert "location_id_preferred" in issue_types(issues)


def test_rejects_non_numeric_location_id():
    issues = SearchLocationValidator().validate_location_row(location_row(**{"Location ID": "abc"}), 2)

    assert "invalid_location_id" in issue_types(issues)


def test_accepts_positive_radius_target():
    issues = SearchLocationValidator().validate_location_row(
        location_row(Location="Office", **{"Location ID": "", "Radius": "25", "Unit": "miles"}),
        2,
    )

    assert issues == []


def test_rejects_invalid_radius():
    issues = SearchLocationValidator().validate_location_row(location_row(**{"Radius": "nope"}), 2)

    assert "invalid_radius_format" in issue_types(issues)


def test_flags_duplicate_location_target_inside_campaign():
    issues = SearchLocationValidator().validate_location_data([location_row(), location_row()])

    assert "duplicate_location_target" in issue_types(issues)
