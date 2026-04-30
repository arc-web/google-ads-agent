# Client-Facing Language Rules

Date: 2026-04-28

## Purpose

Client reports must sound direct, confident, and useful to non-technical decision-makers. The writing should make the work feel substantial without sounding inflated, templated, or model-generated.

## Voice Standard

Use language that is:

- Influential.
- Direct.
- Clear.
- Specific.
- Calm.
- Client-readable.
- Evidence-led.

The report should show the amount of work completed without overexplaining implementation details.

## Do-Not-Use List

Do not use:

- Em dashes.
- `Why this matters:`
- `Key takeaways`
- `Game changer`
- `Unlock growth`
- `Supercharge`
- `Seamlessly`
- Draft review language such as `flagged for rewrite`.
- Placeholder language such as `Run full sweep for grade`.
- Generic praise that does not explain what improved.

## Preferred Pattern

Use direct statements instead of contrived labels.

Weak:

`Why this matters: Phrase match gives us more control.`

Better:

`Phrase match keeps the launch controlled and prevents broad-match waste.`

Weak:

`Key takeaways`

Better:

`What changed`

Weak:

`This unlocks better performance.`

Better:

`This gives the team cleaner data by separating service, location, and intent.`

## Report Writing Rule

For every strategic point, state:

- What changed.
- What the client can now see or approve.
- What the team will monitor next.

Avoid explaining like a developer unless the section is explicitly internal.

## Enforcement

`shared/presentation/report_quality_audit.py` blocks banned phrases in client-facing HTML before PDF export.

`shared/presentation/prepare_client_review_html.py` removes or rewrites known draft phrases during deterministic report preparation.

## Sources

- Nielsen Norman Group visual design principles: https://www.nngroup.com/articles/principles-visual-design/
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
