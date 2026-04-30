# Source Attribution And Brand Rules

Date: 2026-04-28

## Purpose

`Google_Ads_Agent` ingests old account exports, search term reports, location reports, and campaign names. Those source files often contain previous vendor names, old naming conventions, and legacy labels.

Those source labels are evidence. They are not branding.

## Agency Brand

The agency brand for client-facing work is:

`Advertising Report Card`

Use this brand in:

- Client-facing review documents.
- Prepared-by lines.
- Internal process references where agency identity matters.
- Top-level campaign ownership names.
- Labels that identify who built or manages the work.
- Optional cover page or footer treatment.

Use `ARC` for ownership-level campaign prefixes and build labels. Use the client's name, website, services, and locations in ad-facing fields, URLs, copy, and client context.

## Previous Provider Names

Previous provider names, vendor names, and old campaign suffixes must be treated as source metadata only.

Examples:

- `RevKey`
- Legacy agency names.
- Old vendor labels.
- Old campaign suffixes.

These may appear in:

- Raw imported CSVs.
- `account_snapshot.json`.
- `account_audit.json`.
- Internal migration notes.
- One controlled client-facing before-and-after section.

These must not appear in:

- New campaign names.
- New ad group names.
- New keywords.
- New RSA headlines.
- New RSA descriptions.
- New display paths.
- New final URLs.
- Client-facing page titles except the controlled before-and-after section.
- Output file names except archived raw-source files.

## Rule Levels

### Level 1: Ingestion

When parsing source CSVs:

- Preserve original campaign and ad group names in source fields.
- Detect source-provider tokens.
- Store detected tokens in `source_attribution.json`.
- Never use source provider tokens as default naming tokens.

Recommended fields:

- `source_campaign_name`
- `source_ad_group_name`
- `source_provider_tokens`
- `source_file`
- `source_row_id`

### Level 2: Normalization

Before strategy generation:

- Strip source-provider suffixes from canonical campaign names.
- Strip legacy vendor labels from working taxonomy names.
- Convert old naming into neutral categories.

Example:

- Source: `Psychiatry - RevKey`
- Canonical source label: `Psychiatry`
- New generated campaign: `ARC - Search - Services - V1`

### Level 3: Generated Campaign Naming

Generated campaign names must follow an ARC-owned naming pattern when the campaign name is used to identify who built or manages the structure.

Default campaign pattern:

`ARC - Search - {CampaignTheme}`

Optional version:

`ARC - Search - {CampaignTheme} - V1`

Do not use:

- Previous provider names.
- Imported source suffixes.
- Full agency names where `ARC` is enough.
- Client names as the ownership prefix unless the account explicitly requires client-prefixed campaign names.
- Tactical labels that only make sense internally.

Allowed examples:

- `ARC - Search - Services`
- `ARC - Search - Brand`
- `ARC - Search - Testing`
- `ARC - Search - Therapy`
- `ARC - Search - Services - V1`

Blocked examples:

- `THHL - Search - Services - RevKey`
- `THHL - Search - Services - V1`
- `Psychiatry - RevKey`
- `Falls Church-Pmax-RevKey`

Client identity still belongs in:

- Final URLs.
- Display paths when appropriate.
- Ad copy when it improves relevance.
- Landing page selection.
- Client-facing reports.
- Account source attribution.

### Level 4: Generated Ad Group Naming

Ad groups must describe service and intent, not vendor provenance.

Default ad group pattern:

`Service - Audience/Category - IntentLayer`

Allowed examples:

- `Psychiatry - Adult - General`
- `Therapy - Trauma - City`
- `Testing - ADHD - Local`

Blocked examples:

- `Psychiatry - RevKey`
- `RevKey - Psychiatry - Adult`
- `Old Vendor - Therapy - City`

### Level 5: Keyword And Copy

Provider names must not enter ad-facing assets unless they are the client brand or an approved competitor strategy.

Blocked generated fields:

- `Keyword`
- `Headline 1` through `Headline 15`
- `Description 1` through `Description 4`
- `Path 1`
- `Path 2`
- `Final URL`

Exception:

- Competitor or provider terms may be added to a negative keyword review file.
- Competitor conquest campaigns require explicit human approval and separate policy review.

### Level 6: Client-Facing Documents

Client-facing review documents should use:

- Client brand.
- Advertising Report Card as the prepared-by agency.
- Neutral language for the prior state.

Allowed prior-state references:

- `The inherited account structure`
- `The previous campaign naming convention`
- `The source export`
- `The prior build`

Allowed explicit previous-provider reference:

- One before-and-after or appendix page that explains the inherited naming issue.

Example:

`Several imported campaigns used the suffix RevKey. We treated that as source metadata only and removed it from the rebuilt campaign naming system.`

Do not repeatedly mention the previous provider throughout the document.

### Level 7: Validation

Before writing final outputs, scan generated artifacts for blocked provider tokens.

Required scan targets:

- Google Ads Editor staging CSV.
- `campaign_taxonomy.csv`.
- `keyword_matrix.csv`.
- `rsa_copy_matrix.csv`.
- `Client_Rebuild_Review.html` source data before PDF export.
- `Client_Rebuild_Review.pdf` text extraction when available.
- `human_review.md`.

If a blocked provider token appears outside an allowed attribution section, validation must fail.

Initial validator:

```bash
python3 shared/rebuild/provider_token_validator.py \
  --token RevKey \
  --file clients/{agency}/{client}/build/{date}_account_rebuild/Google_Ads_Editor_Staging_CURRENT.csv
```

Validation output should include:

- Token found.
- File.
- Field or section.
- Whether it is allowed or blocked.
- Suggested neutral replacement.

### Level 8: Configuration

Each client profile should include source attribution settings.

```yaml
agency:
  display_name: "Advertising Report Card"
  short_name: "ARC"

source_attribution:
  previous_provider_tokens:
    - "RevKey"
  allowed_client_facing_sections:
    - "Before And After"
    - "Sources And Staging Notes"
  blocked_generated_fields:
    - "Campaign"
    - "Ad Group"
    - "Keyword"
    - "Headline"
    - "Description"
    - "Path"

campaign_naming:
  ownership_prefix: "ARC"
  pattern: "ARC - Search - {CampaignTheme} - V1"
  client_identity_in_ad_facing_assets: true
```

## Validator Behavior

Hard fail:

- Provider token in generated campaign name.
- Provider token in ad group name.
- Provider token in keyword.
- Provider token in ad copy.
- Provider token in document title or repeated page headers.

Allowed:

- Provider token in raw source file path.
- Provider token in `source_attribution.json`.
- Provider token in one controlled before-and-after section.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
