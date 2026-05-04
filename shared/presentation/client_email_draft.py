"""Build client-facing email drafts for campaign report packages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EmailQuestionGroup:
    title: str
    question: str
    terms: list[str]
    regions: list[str] | None = None
    default_action: str = "Review"
    group_type: str = "regional"


@dataclass(frozen=True)
class EmailDraftInput:
    client: str
    date_label: str
    report_type: str
    pdf_path: Path
    summary: Any
    next_step: str = "Please review the attached PDF and send any service, location, budget, or copy feedback."
    search_term_question_groups: list[EmailQuestionGroup] | None = None
    client_notes: list[str] | None = None
    internal_review_notes: list[str] | None = None
    confirmation_items: list[str] | None = None


def build_client_email_draft(data: EmailDraftInput) -> str:
    campaign_label = data.report_type.strip() or "campaign build"
    if data.search_term_question_groups and "search" in campaign_label.lower():
        return build_search_term_email_draft(data, campaign_label)

    primary_campaign = data.summary.campaigns[0] if data.summary.campaigns else "the campaign build"
    locations = ", ".join(data.summary.locations) if data.summary.locations else "the approved service area"
    lines = [
        f"Subject: {data.client} {campaign_label} review",
        "",
        "Hi [Client Name],",
        "",
        f"I attached the {campaign_label} review for {data.client}.",
        "",
        "The attached PDF summarizes the campaign build, the structure we prepared, the services and locations covered, and the items we need confirmed before launch.",
        "",
        "Quick summary:",
        f"- Campaign build: {primary_campaign}",
        f"- Ad groups: {data.summary.ad_groups}",
        f"- Search intent coverage: {data.summary.phrase_keywords} phrase-match keyword themes",
        f"- Ads prepared: {data.summary.rsa_rows} responsive search ads",
        f"- Targeting to confirm: {locations}",
    ]
    if data.client_notes:
        lines.extend(["", "Revision notes:"])
        lines.extend(f"- {note}" for note in data.client_notes)
    if data.internal_review_notes:
        lines.extend(["", "Internal review before sending:"])
        lines.extend(f"- {note}" for note in data.internal_review_notes)
    confirmation_items = data.confirmation_items if data.confirmation_items is not None else [
        "Which services should be the highest priority",
        "Whether you serve all 50 states, or whether the campaign should use a smaller service area",
        "If you do not want equal national coverage, your top 5 states and top 5 cities or metro areas",
        "Where you currently do most of your work, and where we can get faster wins if those areas are different",
        "Any states, cities, ZIPs, or regions that should be excluded",
        "Whether the budget assumptions are approved",
        "Whether any wording, claims, or service details need to be adjusted",
    ]
    lines.extend([
        "",
        "Before anything goes live, please review the attached PDF and confirm:",
        *[f"- {item}" for item in confirmation_items],
    ])
    lines.extend(["", data.next_step])
    if "new campaign" in campaign_label.lower():
        lines.extend(["", "No changes have been pushed live. This is prepared for review and approval first."])
    lines.extend(
        [
            "",
            "Looking forward to your feedback on these. If you have any questions on how this process works, just reach out and we are happy to hop on a call and help.",
            "",
            "Thanks,",
            "[Your Name]",
            "",
            "Attachment:",
            f"- {data.pdf_path.name}",
        ]
    )
    return "\n".join(lines) + "\n"


def build_search_term_email_draft(data: EmailDraftInput, campaign_label: str) -> str:
    lines = [
        f"Subject: {data.client} {campaign_label} review",
        "",
        "Hey [Client Name]!",
        "",
        "We reviewed the latest search terms and location performance. A few terms are clear enough to stage for review, and a few need your call before we build around them.",
        "",
        "The main thing we need from you is how you want to handle the cities and a small set of unclear searches below.",
        "",
        "Please reply inline with Focus, Keep, or Exclude where noted.",
    ]
    for section_title, group_type in (
        ("Service Confirmations", "service"),
        ("Regional Confirmations", "regional"),
    ):
        section_groups = [group for group in data.search_term_question_groups or [] if group.group_type == group_type]
        if not section_groups:
            continue
        lines.extend(["", section_title, ""])
        for group in section_groups:
            if group.group_type == "regional":
                lines.append(group.title)
                lines.append(group.question)
                lines.append("")
                for region in group.regions or []:
                    lines.append(f"{region}: [Focus / Keep / Exclude]")
                lines.append(
                    "If any city is unclear, mark it Discuss and we can talk through it. Based on your response we plan on building out ad groups focused on these independently."
                )
                continue
            lines.append(f"{group.question} Example searches:")
            lines.append("")
            for term in group.terms[:3]:
                lines.append(term)

    lines.extend(
        [
            "",
            "Looking forward to your feedback on these. If you have any questions on how this process works, just reach out and we are happy to hop on a call and help.",
            "",
            "Thanks,",
            "[Your Name]",
        ]
    )
    return "\n".join(lines) + "\n"


def write_client_email_draft(path: Path, data: EmailDraftInput) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_client_email_draft(data), encoding="utf-8")
    return path
