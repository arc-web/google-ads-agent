from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from shared.rebuild.geo_taxonomy import build_geo_ad_group_plans, parse_geo_target
from shared.rebuild.revision_feedback import classify_revision_feedback, merge_client_hq_revision_facts, revise_rows


NYC_FEEDBACK = """
I have immediate openings for about 2-3 clients on my caseload. My associate therapist who joins my practice at the end of May will have openings for 6 clients and will eventually work up to 10-12 clients in the fall.
Let's keep it to young adults and adults for now. Can we target college students instead of adolescents?
I think splitting it up by state makes the most sense.
Does the amount I already paid only go toward the management fee or does some of it go toward ad spend? I'm curious what you'd recommend for my budget. It might make sense to be more conservative in May and then increase in June once my associate therapist starts and has more capacity for new clients.
I'm not currently enrolling any groups. I'm planning to launch two groups in September so we can hold off on that for now.
"""


def test_revision_feedback_classifies_nyc_response() -> None:
    classified = classify_revision_feedback(NYC_FEEDBACK)
    categories = {category for item in classified["items"] for category in item["categories"]}

    assert "capacity_ramp" in categories
    assert "audience_constraint" in categories
    assert "geo_architecture" in categories
    assert "budget_strategy" in categories
    assert "service_pause" in categories
    assert classified["report_goal"]["minimum_qualified_leads"] == 4
    assert classified["campaign_directives"]["split_by_state"] is True


def test_revision_feedback_merges_client_hq_facts(tmp_path: Path) -> None:
    client_root = tmp_path / "client"
    hq_dir = client_root / "docs" / "client_hq"
    hq_dir.mkdir(parents=True)
    (hq_dir / "client_hq.json").write_text(json.dumps({"client_name": "Fixture"}), encoding="utf-8")

    classified = classify_revision_feedback(NYC_FEEDBACK, source="test")
    merge_client_hq_revision_facts(client_root, classified)
    merged = json.loads((hq_dir / "client_hq.json").read_text(encoding="utf-8"))

    assert "Owner has immediate openings for about 2 to 3 clients." in merged["capacity_notes"]
    assert "Target college students instead of adolescents." in merged["audience_notes"]
    assert "Group Therapy" in merged["paused_services"]
    assert merged["revision_facts"]["campaign_directives"]["split_by_state"] is True
    assert merged["revision_facts"]["report_goal"]["planning_qualified_lead_range"] == "4 to 8"


def test_geo_taxonomy_builds_state_and_city_tiers() -> None:
    plans = build_geo_ad_group_plans(
        base_campaign="ARC - Search - Anxiety Therapy - V1",
        services=["Anxiety Therapy"],
        locations=[
            parse_geo_target("New York, United States|21167"),
            parse_geo_target("New Jersey, United States|21164"),
            parse_geo_target("Brooklyn, New York, United States|1023191"),
        ],
        final_url_for_service=lambda _service: "https://example.com/anxiety",
        path_part=lambda value: value.replace(" ", "")[:15],
        version_suffix="REV1",
        split_by_state=True,
        ad_group_prefix="Therapy",
    )
    campaigns = {plan.campaign for plan in plans}
    ad_groups = {plan.ad_group for plan in plans}
    brooklyn = next(plan for plan in plans if plan.intent_tier == "city")

    assert campaigns == {
        "ARC - Search - Anxiety Therapy - NY - REV1",
        "ARC - Search - Anxiety Therapy - NJ - REV1",
    }
    assert "Therapy - Anxiety Therapy - General" in ad_groups
    assert "Therapy - Anxiety Therapy - Near Me" in ad_groups
    assert "Therapy - Anxiety Therapy - New York" in ad_groups
    assert "Therapy - Anxiety Therapy - New Jersey" in ad_groups
    assert "Therapy - Anxiety Therapy - Brooklyn" in ad_groups
    assert "anxiety therapy in Brooklyn" in brooklyn.keywords
    assert "Brooklyn NY anxiety therapy" in brooklyn.keywords


def test_revision_feedback_revises_staging_rows_by_state() -> None:
    fieldnames = [
        "Campaign",
        "Campaign Type",
        "Networks",
        "Budget",
        "Budget type",
        "EU political ads",
        "Broad match keywords",
        "Ad Group",
        "Criterion Type",
        "Keyword",
        "Final URL",
        "Location",
        "Location ID",
        "Ad type",
        "Status",
        "Campaign status",
        "Ad Group status",
        "Keyword status",
        "Ad status",
        "Path 1",
        "Path 2",
    ]
    rows = [
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", **{"Campaign Type": "Search", "Networks": "Google search", "Budget": "50.00", "Budget type": "Daily", "EU political ads": "No", "Broad match keywords": "Off", "Status": "Paused", "Campaign status": "Paused"}),
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", Location="New York, United States", **{"Location ID": "21167"}),
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", **{"Ad Group": "Therapy - Anxiety - General", "Status": "Paused", "Ad Group status": "Paused"}),
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", **{"Ad Group": "Therapy - Group Therapy - General", "Status": "Paused", "Ad Group status": "Paused"}),
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", **{"Ad Group": "Therapy - Anxiety - General", "Criterion Type": "Phrase", "Keyword": "adolescent anxiety therapy", "Final URL": "https://example.com", "Keyword status": "Paused"}),
        row(fieldnames, Campaign="ARC - Search - Anxiety Therapy - V1", **{"Ad Group": "Therapy - Anxiety - General", "Criterion Type": "Phrase", "Keyword": "anxiety therapy", "Final URL": "https://example.com", "Keyword status": "Paused"}),
    ]

    revised = revise_rows(rows, fieldnames, classify_revision_feedback(NYC_FEEDBACK))
    text = rows_to_text(fieldnames, revised)

    assert " - NY - REV1" in text
    assert " - NJ - REV1" in text
    assert "Therapy - Anxiety - Near Me" in text
    assert "Therapy - Anxiety - New York" in text
    assert "Therapy - Anxiety - New Jersey" in text
    assert "college student therapy" in text
    assert "Negative Phrase" in text
    assert "adolescent anxiety therapy" not in text
    assert "Therapy - Group Therapy - General" not in text
    assert "Therapy - Group - New York City" not in text


def row(fieldnames: list[str], **values: str) -> dict[str, str]:
    data = {field: "" for field in fieldnames}
    data.update(values)
    return data


def rows_to_text(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
