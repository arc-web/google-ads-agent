"""Executable client-facing language checks for reports and emails."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LanguageFinding:
    severity: str
    code: str
    message: str
    evidence: str = ""


CLIENT_FACING_BANNED_PHRASES = (
    "red counts are over the character limit",
    "flagged for rewrite",
    "run full sweep for grade",
    "why this matters:",
    "key takeaways",
    "game changer",
    "unlock growth",
    "supercharge",
    "seamlessly",
    "at-limit items",
    "exactly 30 chars",
    "may count punctuation differently",
)

EMAIL_ROBOTIC_PHRASES = (
    "no changes are being pushed live",
    "no changes have been pushed live",
    "this is a review package for google ads editor staging only",
    "the attached pdf summarizes",
    "suggested default:",
    "default action if not approved",
)

EMAIL_MARKDOWN_CLUTTER = (
    "**",
    "```",
)

STR_EMAIL_BOILERPLATE = (
    "search term questions",
    "exclude recommendations",
    "not already clear from the website",
)


def banned_phrase_findings(text: str, *, code: str, message: str) -> list[LanguageFinding]:
    lower_text = text.lower()
    findings = []
    for phrase in CLIENT_FACING_BANNED_PHRASES:
        if phrase in lower_text:
            findings.append(LanguageFinding("error", code, message, phrase))
    return findings


def em_dash_findings(text: str, *, code: str, message: str) -> list[LanguageFinding]:
    if "—" not in text:
        return []
    return [LanguageFinding("error", code, message, "—")]


def audit_report_language(text: str) -> list[LanguageFinding]:
    findings = []
    findings.extend(
        banned_phrase_findings(
            text,
            code="presentation.client_facing_draft_language",
            message="Client-facing review contains draft-only copy QA language.",
        )
    )
    findings.extend(
        em_dash_findings(
            text,
            code="presentation.em_dash",
            message="Client-facing reports cannot use em dashes.",
        )
    )
    return findings


def audit_client_email_text(text: str) -> list[LanguageFinding]:
    lower_text = text.lower()
    findings = []
    findings.extend(
        banned_phrase_findings(
            text,
            code="email.client_facing_banned_phrase",
            message="Client email contains banned client-facing language.",
        )
    )
    findings.extend(
        em_dash_findings(
            text,
            code="email.em_dash",
            message="Client emails cannot use em dashes.",
        )
    )
    for phrase in EMAIL_ROBOTIC_PHRASES:
        if phrase in lower_text:
            findings.append(
                LanguageFinding(
                    "error",
                    "email.robotic_or_report_boilerplate",
                    "Client email contains robotic staging language or report boilerplate.",
                    phrase,
                )
            )
    for marker in EMAIL_MARKDOWN_CLUTTER:
        if marker in text:
            findings.append(
                LanguageFinding(
                    "error",
                    "email.markdown_clutter",
                    "Client email contains markdown-heavy formatting that hurts reply readability.",
                    marker,
                )
            )
    if "search term" in lower_text:
        for phrase in STR_EMAIL_BOILERPLATE:
            if phrase in lower_text:
                findings.append(
                    LanguageFinding(
                        "error",
                        "email.search_term_boilerplate",
                        "Search-term emails should stay focused on client decisions.",
                        phrase,
                    )
                )
        repeated_city_prompts = re.findall(r"confirm service area for [a-z() -]+:", lower_text)
        if len(repeated_city_prompts) > 1:
            findings.append(
                LanguageFinding(
                    "error",
                    "email.repeated_city_prompts",
                    "Search-term emails should group regional decisions into one city list.",
                    "; ".join(repeated_city_prompts[:3]),
                )
            )
    return findings


def audit_client_email_file(path: Path) -> tuple[list[LanguageFinding], dict[str, int]]:
    findings = audit_client_email_text(path.read_text(encoding="utf-8", errors="replace"))
    summary = {
        "errors": sum(1 for finding in findings if finding.severity == "error"),
        "warnings": sum(1 for finding in findings if finding.severity == "warning"),
    }
    return findings, summary
