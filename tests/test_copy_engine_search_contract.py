from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))

from copy_engine.context import AdGroupContext
from copy_engine.editor.evaluator import CopyEvaluator
from copy_engine.editor.char_limit_enforcer import assert_rsa_clean
from copy_engine.editor.reporter import HITLReporter
from copy_engine.orchestrator import CopyEngineOrchestrator, RSA_DESCRIPTION_TARGET, RSA_HEADLINE_TARGET
from copy_engine.search.descriptions import DescriptionGenerator
from copy_engine.search.headlines import HeadlineGenerator


class FakeCopyClient:
    def complete_json(self, system: str, user: str, schema: object, max_tokens: int) -> list[dict[str, str]]:
        del system, schema, max_tokens
        if "description" in user.lower():
            return [
                {"text": "Therapy support helps you plan your next step today.", "role": "pas"},
                {"text": "Therapy care offers steady guidance when life feels heavy.", "role": "proof_cta"},
                {"text": "Private sessions match your needs with clear next steps.", "role": "differentiator"},
                {"text": "Local appointments help you start with less waiting.", "role": "geo_urgency"},
            ]
        return [
            {"text": "Therapy Plan That Fits You", "mix_type": "keyword_lead"},
            {"text": "Counseling Options Near You", "mix_type": "keyword_lead"},
            {"text": "Mental Health Help Near You", "mix_type": "keyword_lead"},
            {"text": "Build Calmer Days With Care", "mix_type": "benefit_lead"},
            {"text": "Find Relief With Guidance", "mix_type": "benefit_lead"},
            {"text": "Feeling Stuck And Anxious", "mix_type": "question"},
            {"text": "Licensed Clinicians Ready", "mix_type": "proof"},
            {"text": "Springfield Therapy Visits", "mix_type": "geo"},
            {"text": "Schedule A Private Consult", "mix_type": "cta"},
            {"text": "Private Session Options Today", "mix_type": "benefit_lead"},
            {"text": "Book Your First Visit Today", "mix_type": "cta"},
            {"text": "Anxiety Support Next Steps", "mix_type": "keyword_lead"},
            {"text": "Stress Relief Support Plan", "mix_type": "benefit_lead"},
            {"text": "Trusted Local Clinician Team", "mix_type": "proof"},
            {"text": "Nearby Counseling Guidance", "mix_type": "geo"},
        ]


def _ad_group_context() -> AdGroupContext:
    return AdGroupContext(
        name="Therapy Services",
        service="Therapy",
        geo=["Springfield"],
        USPs=["Private sessions", "Flexible scheduling"],
        top_keywords=["therapy", "counseling"],
        landing_url="https://example.com/therapy",
        industry="general",
        practice_name="Example Practice",
    )


def test_search_generators_default_to_full_rsa_asset_counts() -> None:
    fake_client = FakeCopyClient()
    ctx = _ad_group_context()

    headlines = HeadlineGenerator(fake_client).generate(ctx)
    descriptions = DescriptionGenerator(fake_client).generate(ctx)

    assert len(headlines) == RSA_HEADLINE_TARGET
    assert len(descriptions) == RSA_DESCRIPTION_TARGET
    assert HeadlineGenerator(fake_client).validate(headlines) == []
    assert DescriptionGenerator(fake_client).validate(descriptions, ctx) == []
    assert_rsa_clean([headline.text for headline in headlines], [description.text for description in descriptions])


def test_orchestrator_defaults_are_repo_local_and_search_rsa_complete(tmp_path: Path) -> None:
    orchestrator = CopyEngineOrchestrator(
        agency="agency_slug",
        client="client_slug",
        base_path=str(tmp_path),
        llm_client=FakeCopyClient(),
    )

    assert orchestrator.base_path == str(tmp_path.resolve())
    assert orchestrator.client_dir == str(tmp_path.resolve() / "clients" / "agency_slug" / "client_slug")

    plan = orchestrator._make_build_plan({"Service": {"headlines": [], "descriptions": []}})

    assert plan["Service"]["headlines"] == RSA_HEADLINE_TARGET
    assert plan["Service"]["descriptions"] == RSA_DESCRIPTION_TARGET


def test_reporter_default_base_path_is_repo_local_not_user_specific() -> None:
    reporter = HITLReporter()

    assert reporter.base_path == str(REPO_ROOT)
    reporter_source = (REPO_ROOT / "shared/copy_engine/editor/reporter.py").read_text(encoding="utf-8")
    local_home_prefix = "/" + "Users/home"
    assert local_home_prefix not in reporter_source


def test_copy_evaluator_marks_short_low_value_headlines_unclean() -> None:
    report = CopyEvaluator().evaluate_headline("Ashburn Care")

    assert not report.is_clean
    assert any(
        violation.asset_type == "headline"
        and violation.reason == "min_value"
        and violation.limit == 25
        for violation in report.char_violations
    )
