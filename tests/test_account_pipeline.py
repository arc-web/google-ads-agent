from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from shared.copy_engine.search.copy_matrix import (
    CopyCandidate,
    CopyConstraints,
    build_rsa_copy,
    candidate_issues,
    write_rsa_copy_matrix,
)
from shared.rebuild.scaffold_client import scaffold_client
from shared.rebuild.staging_validator import validate_file


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "new_campaign_site"


def test_copy_gate_rejects_failed_candidates_from_matrix(tmp_path: Path) -> None:
    failed = CopyCandidate(
        campaign="ARC - Search - Services - V1",
        ad_group="Services - Repair - General",
        asset_type="headline",
        slot=1,
        text="Repair",
        chars=6,
        role="keyword_match",
        source="test",
        grade="F",
        status="fail",
        issues=["bare_or_one_word_headline"],
    )
    assert "bare_or_one_word_headline" in candidate_issues("headline", "Repair", CopyConstraints())
    try:
        write_rsa_copy_matrix(tmp_path / "rsa_copy_matrix.csv", [failed])
    except ValueError as exc:
        assert "failed candidates" in str(exc)
    else:
        raise AssertionError("Expected failed copy candidate to block matrix write")


def test_copy_gate_requires_long_description_cta_and_value_prop() -> None:
    constraints = CopyConstraints()

    assert "description_under_value_minimum" in candidate_issues(
        "description",
        "Repair support is available. Call Today.",
        constraints,
    )
    assert "description_missing_cta" in candidate_issues(
        "description",
        "Review repair support options with practical local guidance and a focused service team.",
        constraints,
    )
    assert "description_missing_value_prop" in candidate_issues(
        "description",
        "This message has enough characters to pass length but says almost nothing. Call Today.",
        constraints,
    )
    assert "description_generic_workflow_language" in candidate_issues(
        "description",
        "Request details to confirm service fit audience needs timing and budget before launch.",
        constraints,
    )
    assert "description_missing_service_specificity" in candidate_issues(
        "description",
        "Review support options with practical local guidance and a focused team. Call Today.",
        constraints,
        {"service_terms": ["lay", "counselor", "academy"]},
    )


def test_copy_gate_blocks_unverified_delivery_and_hard_superlatives() -> None:
    constraints = CopyConstraints()

    assert "unverified_delivery_claim:virtual" in candidate_issues(
        "description",
        "Review virtual repair support options with practical local guidance. Call Today.",
        constraints,
    )
    assert "unverified_superlative_claim" in candidate_issues(
        "headline",
        "Best Repair Support Today",
        constraints,
    )
    assert "unverified_superlative_claim" not in candidate_issues(
        "headline",
        "Top Repair Support Options",
        constraints,
    )


def test_build_rsa_copy_uses_verified_delivery_mode_only() -> None:
    bundle = build_rsa_copy(
        campaign="ARC - Search - Services - V1",
        ad_group="Services - Repair Services - General",
        service="Repair Services",
        client_name="Fixture Client",
        geo=["United States|2840"],
        keywords=["Repair Services"],
        constraints=CopyConstraints(),
        source_evidence={
            "status": "readable",
            "matched_terms": ["repair", "services"],
            "delivery_modes": ["virtual", "in_person"],
            "landing_page_claims": ["focused repair support and practical service options"],
            "copy_allowed_claims": ["virtual", "in_person", "focused repair support and practical service options"],
        },
    )

    assert len(bundle.headlines) == 15
    assert len(bundle.descriptions) == 4
    assert all(75 <= len(description) <= 90 for description in bundle.descriptions)
    assert any("online and in-person" in description.lower() for description in bundle.descriptions)
    assert not [candidate for candidate in bundle.candidates if candidate.status == "fail"]


def test_build_rsa_copy_uses_lay_counselor_service_logic_in_descriptions() -> None:
    bundle = build_rsa_copy(
        campaign="ARC - Search - Mental Health Consulting - V1",
        ad_group="Services - Lay Counselor Academy",
        service="Lay Counselor Academy",
        client_name="EM Consulting",
        geo=["California, United States|21137"],
        keywords=["lay counselor academy"],
        constraints=CopyConstraints(),
        source_evidence={
            "service_terms": ["lay", "counselor", "academy"],
            "matched_terms": ["lay", "counselor", "academy"],
            "landing_page_claims": ["staff training for lay counseling skills and mental health access"],
            "copy_allowed_claims": ["staff training for lay counseling skills and mental health access"],
            "service_logic": {
                "service_mechanism": "Training staff in lay counseling skills",
                "outcome": "Expanded mental health access through trained lay counselor teams",
                "concept_tokens": ["academy", "access", "counseling", "counselor", "lay", "mental", "staff", "training"],
            },
        },
    )

    text = " ".join(bundle.descriptions).lower()
    tokens = set(token for token in text.replace(".", " ").replace(",", " ").split() if token)
    assert len(bundle.descriptions) == 4
    assert not any(phrase in text for phrase in ("campaign approval", "account import", "launch readiness"))
    assert {"lay", "staff", "training"} <= tokens
    assert {"counselor", "counseling"} & tokens


def test_account_pipeline_build_creates_search_rebuild_contract(tmp_path: Path) -> None:
    clients_dir = tmp_path / "clients"
    client_root = scaffold_client(
        "fixture_agency",
        "fixture_client",
        "Fixture Client",
        (FIXTURE_DIR / "index.html").as_uri(),
        clients_dir=clients_dir,
    )
    profile_path = client_root / "config" / "client_profile.yaml"
    profile_text = profile_path.read_text(encoding="utf-8")
    profile_text += """
services:
  - Repair Services
  - Consulting Services
competitor_pruning:
  negative_phrase_terms:
    - Competitor Co
budget:
  monthly_budget: 3000
  daily_budget: 100
market:
  primary_service_area: United States
  target_cities: []
  target_states:
    - United States|2840
  target_zip_codes: []
  radius_targets: []
"""
    profile_path.write_text(profile_text, encoding="utf-8")
    (client_root / "config" / "client_copy_constraints.json").write_text(
        json.dumps(
            {
                "approved_claims": [],
                "blocked_claims": ["guaranteed"],
                "services_with_capacity": ["Repair Services", "Consulting Services"],
                "services_excluded": [],
                "insurance_language": "",
                "age_eligibility": {},
                "geo_constraints": {},
                "legal_or_verification_notes": [],
                "approved_ctas": [],
                "blocked_ctas": [],
                "approved_superlatives": [],
                "delivery_modes": [],
                "availability_claims": [],
                "landing_page_fallback_allowed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (client_root / "campaigns" / "account_export.csv").write_text(
        "Campaign\tCampaign Type\tCriterion Type\tKeyword\tAd Group\tAd type\tLocation\n"
        "Legacy RevKey\tSearch\tBroad\trepair\tOld Group\t\t\n",
        encoding="utf-16",
    )
    performance_dir = client_root / "reports" / "performance_inputs"
    performance_dir.mkdir(parents=True, exist_ok=True)
    (performance_dir / "search_terms_report.csv").write_text(
        "Search terms report\n"
        "Search term,Impr.,Clicks,Conversions\n"
        "repair service near me,120,12,2\n"
        "consulting service,80,4,0\n"
        "competitor co repair reviews,30,5,0\n",
        encoding="utf-8",
    )
    (performance_dir / "location_report.csv").write_text(
        "Location report\n"
        "Location,Campaign,Impr.,Interactions,Conversions\n"
        "United States,ARC - Search - Services - V1,200,20,2\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shared.rebuild.account_pipeline",
            "--agency",
            "fixture_agency",
            "--client",
            "fixture_client",
            "--build-date",
            "2026-05-04",
            "--mode",
            "build",
            "--clients-dir",
            str(clients_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    artifacts = json.loads(result.stdout)
    staging = Path(artifacts["staging_csv"])
    manifest = Path(artifacts["run_manifest"])
    copy_matrix = Path(artifacts["rsa_copy_matrix"])
    candidates = Path(artifacts["copy_candidates"])
    search_terms = Path(artifacts["search_term_analysis"])
    search_term_questions = Path(artifacts["search_term_client_question_groups"])
    negative_review = Path(artifacts["negative_review_candidates"])
    validation_report = json.loads(Path(artifacts["validation_report"]).read_text(encoding="utf-8"))
    conversion_audit = Path(artifacts["conversion_tracking_audit"])
    evidence_quality = Path(artifacts["evidence_quality_report"])
    cadence_plan = Path(artifacts["optimization_cadence_plan"])
    bid_strategy = Path(artifacts["bid_strategy_recommendation"])
    audience_audit = Path(artifacts["audience_mode_audit"])
    recommendations = Path(artifacts["recommendations_triage"])
    policy_audit = Path(artifacts["policy_disapproval_audit"])
    launch_checklist = Path(artifacts["launch_readiness_checklist"])

    assert validate_file(staging)["status"] == "pass"
    assert manifest.exists()
    assert Path(artifacts["client_report_html"]).exists()
    assert Path(artifacts["client_report_pdf"]).exists()
    assert search_terms.exists()
    assert search_term_questions.exists()
    assert conversion_audit.exists()
    assert evidence_quality.exists()
    assert cadence_plan.exists()
    assert bid_strategy.exists()
    assert audience_audit.exists()
    assert recommendations.exists()
    assert policy_audit.exists()
    assert launch_checklist.exists()
    assert json.loads(conversion_audit.read_text(encoding="utf-8"))["status"] == "pass"
    assert "weekly" in json.loads(cadence_plan.read_text(encoding="utf-8"))["cadence"]
    assert json.loads(bid_strategy.read_text(encoding="utf-8"))["recommended_strategy"] == "manual_cpc"
    assert validation_report["copy_gate"]["status"] == "pass"
    assert validation_report["landing_page_gate"]["status"] == "pass"
    assert validation_report["landing_page_status"]
    assert json.loads(manifest.read_text(encoding="utf-8"))["launch_state"] == "staged_for_google_ads_editor_review"
    assert json.loads(candidates.read_text(encoding="utf-8"))
    search_term_text = search_terms.read_text(encoding="utf-8")
    assert "focus_candidate" in search_term_text
    assert "Do not ask if service and region are already confirmed." in search_term_text
    assert search_term_questions.read_text(encoding="utf-8").startswith("group_id,group_type,title,question")
    negative_review_text = negative_review.read_text(encoding="utf-8")
    assert "competitor co,Negative Phrase,Campaign" in negative_review_text
    assert "competitor co repair reviews" in negative_review_text

    with copy_matrix.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["status"] for row in rows} == {"pass"}
    assert all(25 <= int(row["chars"]) <= 90 for row in rows)
    assert all(int(row["chars"]) >= 75 for row in rows if row["asset_type"] == "description")
    staging_text = staging.read_text(encoding="utf-16")
    assert "RevKey" not in staging_text
    with staging.open("r", encoding="utf-16", newline="") as handle:
        staging_rows = list(csv.DictReader(handle, delimiter="\t"))
    assert "Broad" not in {row.get("Criterion Type") for row in staging_rows}
