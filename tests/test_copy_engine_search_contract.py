from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))

from copy_engine.context import AdGroupContext
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
            {"text": "Therapy Support", "mix_type": "keyword_lead"},
            {"text": "Counseling Care", "mix_type": "keyword_lead"},
            {"text": "Mental Health Help", "mix_type": "keyword_lead"},
            {"text": "Feel Steady Again", "mix_type": "benefit_lead"},
            {"text": "Build Calmer Days", "mix_type": "benefit_lead"},
            {"text": "Feeling Stuck?", "mix_type": "question"},
            {"text": "Licensed Care Team", "mix_type": "proof"},
            {"text": "Local Wellness Help", "mix_type": "geo"},
            {"text": "Schedule A Visit", "mix_type": "cta"},
            {"text": "Private Support Options", "mix_type": "benefit_lead"},
            {"text": "Start With A Call", "mix_type": "cta"},
            {"text": "Anxiety Guidance", "mix_type": "keyword_lead"},
            {"text": "Stress Relief Steps", "mix_type": "benefit_lead"},
            {"text": "Trusted Local Team", "mix_type": "proof"},
            {"text": "Nearby Counseling", "mix_type": "geo"},
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
