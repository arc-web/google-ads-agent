# Google_Ads_Agent Instructions

These instructions apply to this repository.

## Canonical Process

The canonical process is `Google_Ads_Agent`, documented here:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md`
- `docs/instruction_audit_2026-04-28.md`
- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `presentations/docs/DEVELOPER_GUIDE.md`
- `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- `docs/AI_REASONING_GATES.md`
- `docs/CLIENT_FACING_LANGUAGE_RULES.md`

Do not treat any single client-specific folder as the source of truth for global process rules.
Client folders are active data assets and examples until the repo owner explicitly marks them for archive.

## Active Directory Rules

- Active client work belongs under `clients/{agency}/{client}/`.
- New clients must be created from `templates/client_template/`.
- Existing client folders that predate the agency/client layout still belong under `clients/{client_slug}/` until they are reviewed and normalized.
- Do not archive, purge, or label client folders as historical until the overall system is tested and the repo owner explicitly approves that status.
- Planning documents that may conflict with the current process belong in `docs/system_review/` until they are reconciled, superseded, or explicitly retired.
- Generated rebuilds belong in `clients/{agency}/{client}/build/{date}_account_rebuild/`.

## Rebuild Standards

- Google Ads Editor is the staging environment. Generated CSVs are not directly deployable without human review.
- Client onboarding is a first-class source of truth for business facts, capacity, compliance, age eligibility, legal entity changes, insurance language, and priorities.
- Website scans are a first-class source of truth for what prospects can verify before they convert.
- Account and analytics data are a first-class source of truth only when the prior structure produced clean evidence.
- Search campaign rebuilds use phrase match only by default.
- Do not use broad match.
- Do not use exact match unless the user explicitly requests a controlled later test.
- Keywords must use Google Ads Editor format: plain keyword text in `Keyword`, with `Criterion Type` set to `Phrase`.
- New campaign rows must populate `EU political ads`.
- Location rows should use `Location ID` when available.
- City ad groups must include all approved target city modifiers, not just one city.
- RSA ads need 15 headlines and 4 descriptions when possible.
- Headlines must be useful ad copy, not one-word labels or bare service names.
- Copy must be service-specific, value-driven, and compliant with the client industry.
- Every generated build must include validation output and a human review file.
- Client-facing reports must be designed in HTML first and exported to PDF with Chrome headless.
- The HTML file is the editable source of truth for revisions.
- Presentation build instructions and human-facing commands belong under `presentations/`.
- Use `presentations/tools/` commands for client-facing HTML/PDF preparation, export, and audits.
- Treat `shared/presentation/` as implementation and compatibility code, not the operating manual.
- DOCX is not a canonical client-facing deliverable for branded rebuild reviews.
- Client-facing presentation preparation is deterministic. Do not use AI reasoning to remove draft language, insert known copy grades, apply page-break rules, or export PDFs.
- AI reasoning is reserved for strategy, source interpretation, client-feedback triage, nuanced copy generation, and qualitative notes when structured grader output is missing.
- Client-facing reports must use influential, direct, clear language for non-technical readers.
- Do not use em dashes, `Why this matters:`, hype phrases, placeholder QA language, or contrived model-style labels in client-facing reports.
- Client revision feedback must be classified before editing the CSV.
- Client feedback should correct facts and priorities, but it should not automatically override campaign architecture.
- Advertising Report Card is the agency brand for client-facing rebuild review documents.
- Use `ARC` for ownership-level campaign prefixes and labels that identify who built or manages the work.
- Default generated Search campaign naming pattern is `ARC - Search - {CampaignTheme} - V1`.
- Client names, services, websites, locations, and value props belong in ad-facing copy, final URLs, landing pages, and client review context.
- Previous provider names from source files are source attribution only.
- Do not reuse previous provider names in generated campaign names, ad group names, keywords, RSA copy, display paths, final URLs, output filenames, or repeated document branding.
- Previous provider names may appear only in raw source files, `source_attribution.json`, internal audit notes, and one controlled before-and-after or source notes section.

## One-Shot Output Contract

A rebuild run should create:

- `account_audit.json`
- `account_snapshot.json`
- `source_attribution.json`
- `website_scan.json`
- `service_catalog.json`
- `landing_page_map.json`
- `geo_strategy.json`
- `search_term_analysis.csv`
- `keyword_expansion_candidates.csv`
- `negative_review_candidates.csv`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `targeting_spec.json`
- `human_review.md`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`
- `validation_report.json`
- `Google_Ads_Editor_Staging_CURRENT.csv`
- `client_feedback_classified.json`
- `revision_decision_log.csv`
- `Google_Ads_Editor_Staging_REV1.csv` when revisions are approved

## Communication Rules

- Never use em dashes.
- Always link to sources when citing platform behavior, repo process, or documentation.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Google Ads EU political advertising status: https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus
- Google Ads bid adjustments: https://support.google.com/google-ads/answer/2732132?hl=en
- Google Ads healthcare and medicines policy: https://support.google.com/adspolicy/answer/176031?hl=en
- Google Analytics HIPAA guidance: https://support.google.com/analytics/answer/13297105?hl=en


<claude-mem-context>
# Memory Context

# [google_ads_agent] recent context, 2026-05-01 1:28pm GMT+8

No previous sessions found.
</claude-mem-context>
