from __future__ import annotations

from pathlib import Path

from shared.presentation.build_new_campaign_report import CampaignSummary
from shared.presentation.client_email_draft import EmailDraftInput, EmailQuestionGroup, build_client_email_draft


def test_client_email_draft_references_pdf_not_csv() -> None:
    draft = build_client_email_draft(
        EmailDraftInput(
            client="Fixture Client",
            date_label="May 4, 2026",
            report_type="new campaign build",
            pdf_path=Path("Client_New_Campaign_Review.pdf"),
            summary=CampaignSummary(
                campaigns=["ARC - Search - Services - V1"],
                ad_groups=2,
                phrase_keywords=14,
                negative_phrase_keywords=1,
                rsa_rows=2,
                locations=["United States"],
                networks=["Google search"],
            ),
        )
    )

    assert "Subject: Fixture Client new campaign build review" in draft
    assert "Attachment:" in draft
    assert "Client_New_Campaign_Review.pdf" in draft
    assert "campaign build" in draft
    assert "CSV" not in draft
    assert "csv" not in draft


def test_client_email_draft_groups_search_term_questions_without_obvious_terms() -> None:
    draft = build_client_email_draft(
        EmailDraftInput(
            client="Sky Therapies",
            date_label="May 4, 2026",
            report_type="search terms and regional focus",
            pdf_path=Path("Search_Terms_Review.pdf"),
            summary=CampaignSummary(
                campaigns=["ARC - Search - Services"],
                ad_groups=7,
                phrase_keywords=730,
                negative_phrase_keywords=0,
                rsa_rows=16,
                locations=["Toronto, Ontario, Canada"],
                networks=["Google search"],
            ),
            search_term_question_groups=[
                EmailQuestionGroup(
                    title="Regional keyword targeting",
                    question="From the search term report, we picked up cities of interest for services. Please confirm if you'd like to Focus, Keep, or Exclude keyword targeting for these cities.",
                    terms=["emdr therapy hamilton", "trauma therapy hamilton"],
                    regions=["Hamilton"],
                    default_action="Discuss before building city-specific ad groups",
                    group_type="regional",
                )
            ],
        )
    )

    assert "**Search Term Questions**" in draft
    assert "**Regional Confirmations**" in draft
    assert "**Regional keyword targeting**" in draft
    assert "Focus, Keep, or Exclude keyword targeting" in draft
    assert "- Hamilton: [Focus / Keep / Exclude]" in draft
    assert "If any city is unclear, mark it Discuss" in draft
    assert "emdr therapy toronto" not in draft
    assert "not already clear from the website" in draft
    assert "No changes have been pushed live" not in draft
    assert "happy to hop on a call" in draft
