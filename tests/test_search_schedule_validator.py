from __future__ import annotations

from shared.validators.search.search_schedule_validator import SearchScheduleValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def schedule_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Ad Schedule": "(Monday[00:00-23:59]);(Tuesday[09:00-17:00])",
    }
    row.update(overrides)
    return row


def test_accepts_google_editor_style_schedule():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(), 2)

    assert issues == []


def test_accepts_plain_hour_schedule():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(**{"Ad Schedule": "Monday 9-17"}), 2)

    assert issues == []


def test_allows_blank_schedule():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(**{"Ad Schedule": ""}), 2)

    assert issues == []


def test_rejects_invalid_day():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(**{"Ad Schedule": "Funday 9-17"}), 2)

    assert "invalid_day" in issue_types(issues)


def test_rejects_unparseable_schedule():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(**{"Ad Schedule": "weekdays"}), 2)

    assert "invalid_schedule_format" in issue_types(issues)


def test_rejects_end_before_start():
    issues = SearchScheduleValidator().validate_schedule_row(schedule_row(**{"Ad Schedule": "Monday 17-9"}), 2)

    assert "schedule_end_before_start" in issue_types(issues)
