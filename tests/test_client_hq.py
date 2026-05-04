from __future__ import annotations

from html import escape
from pathlib import Path
from zipfile import ZipFile

from shared.rebuild.client_hq import parse_client_hq_docx


def write_docx(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = "".join(f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in lines)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body></w:document>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "")
        archive.writestr("word/document.xml", document)


def test_client_hq_parser_extracts_generic_core_facts(tmp_path: Path) -> None:
    docx = tmp_path / "Client HQ - Fixture Therapy.docx"
    write_docx(
        docx,
        [
            "Business Information",
            "Company Name: Fixture Therapy Group",
            "Company Address: 123 Main St, Suite 200, Chicago, IL 60616",
            "Company Website: https://www.fixturetherapy.example",
            "Primary Services to Increase Business: Anxiety Therapy, ADHD Testing & EMDR Therapy",
            "Google Ads",
            "Google Ads Account ID: 123-456-7890",
            "Monthly Budget: $3,000/month",
        ],
    )

    facts = parse_client_hq_docx(docx)

    assert facts.client_name == "Fixture Therapy Group"
    assert facts.website == "https://www.fixturetherapy.example"
    assert facts.google_ads_account_id == "123-456-7890"
    assert facts.monthly_budget == "$3,000/month"
    assert "Anxiety Therapy" in facts.primary_services
    assert "ADHD Testing" in facts.primary_services


def test_client_hq_parser_extracts_virtual_targeting(tmp_path: Path) -> None:
    docx = tmp_path / "Client HQ - Virtual Practice.docx"
    write_docx(
        docx,
        [
            "VirtualPractice.example",
            "Monthly Budget: $1,500/month",
            "Target Locations",
            "Practice is fully virtual; licensed in Example State and Sample State only.",
            "Example State",
            "Sample City, Example State",
            "Telehealth",
            "Sample State statewide",
            "Audience Targeting & Landing Pages",
            "Priority 1: Anxiety Therapy (highest priority)",
            "https://virtualpractice.example/anxiety-therapy/",
        ],
    )

    facts = parse_client_hq_docx(docx)

    assert facts.virtual_only is True
    assert facts.website == "https://VirtualPractice.example"
    assert "Sample State statewide" in facts.telehealth_regions
    assert "Sample City" in facts.service_area_regions
    assert "Anxiety Therapy" in facts.primary_services
    assert not facts.physical_locations


def test_client_hq_parser_extracts_physical_locations_and_do_not_target(tmp_path: Path) -> None:
    docx = tmp_path / "Client HQ - Local Clinic.docx"
    write_docx(
        docx,
        [
            "Client Name: Local Clinic",
            "Target Locations",
            "In-Person",
            "North City, VA",
            "South City, VA",
            "Telehealth",
            "Virginia statewide",
            "Audience Targeting & Landing Pages",
            "Priority 1: Psychiatry",
            "Do NOT Target",
            "Child therapy: waitlist is full",
            "Billing",
        ],
    )

    facts = parse_client_hq_docx(docx)

    assert facts.client_name == "Local Clinic"
    assert facts.physical_locations == ["North City, VA", "South City, VA"]
    assert facts.telehealth_regions == ["Virginia statewide"]
    assert "Psychiatry" in facts.primary_services
    assert "Child therapy: waitlist is full" in facts.do_not_target
