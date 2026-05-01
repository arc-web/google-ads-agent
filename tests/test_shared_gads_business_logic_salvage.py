from __future__ import annotations

import ast
from pathlib import Path


ONBOARDING_PATH = Path("shared/gads/core/business_logic/client_onboarding_workflow.py")


def test_onboarding_workflow_no_longer_contains_account_shaped_auto_generation():
    source = ONBOARDING_PATH.read_text(encoding="utf-8")

    ast.parse(source)
    retired_business_name = "My" + "Expert" + "Resume"
    assert retired_business_name not in source
    assert "subprocess.run" not in source
    assert "campaign_generation_status" in source
    assert "manual_review_required" in source
    assert "Google Ads Editor staging workflow" in source


def test_business_logic_folder_documents_active_vs_salvage_roles():
    readme = Path("shared/gads/core/business_logic/README.md").read_text(encoding="utf-8")

    assert "google_ads_editor_exporter.py" in readme
    assert "Salvage Files" in readme
    assert "Shared onboarding must not auto-generate campaigns" in readme
