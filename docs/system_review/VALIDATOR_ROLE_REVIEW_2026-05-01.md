# Validator Role Review

Date: 2026-05-01

## Plain-English Decision

Keep `shared/validators/`.

Do not archive it.

Do not delete it.

Do not treat it as the active final validator yet.

This folder contains valuable validation ideas, but it currently mixes old assumptions with current agent rules. The right next move is to salvage and rewrite the useful checks into the current Google Ads Editor staging flow.

## Current Source Of Truth

The current agent rules come from:

- `AGENTS.md`
- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `docs/STAGE_3_TOOL_SALVAGE_APPROVAL_2026-04-30.md`

The key current rules that affect validators:

- Google Ads Editor is the staging environment.
- Search rebuilds use phrase match by default.
- Keyword text goes in `Keyword` as plain text.
- Match type goes in `Criterion Type`, usually `Phrase`.
- Broad match is not allowed by default.
- Exact match is not allowed unless explicitly requested later.
- New generated builds must produce validation output and human review.
- Existing client folders stay actionable until tested and explicitly reviewed.

## What I Reviewed

I reviewed the validator files by behavior and relationships:

- package entry points:
  - `shared/validators/__init__.py`
  - `shared/validators/search/__init__.py`
- orchestration:
  - `shared/validators/master_validator.py`
  - `shared/validators/search_master_validator.py`
  - `shared/validators/search/search_master_validator.py`
  - `shared/validators/search/search_validator.py`
- Search checks:
  - `shared/validators/search/search_campaign_validator.py`
  - `shared/validators/search/search_keyword_validator.py`
  - `shared/validators/search/search_adgroup_validator.py`
  - `shared/validators/search/search_location_validator.py`
  - `shared/validators/search/search_text_ad_validator.py`
  - `shared/validators/search/search_budget_validator.py`
  - `shared/validators/search/search_bid_strategy_validator.py`
  - `shared/validators/search/search_schedule_validator.py`
  - older paired modules such as `keyword_validator.py`, `ad_group_validator.py`, and `text_ad_validator.py`
- broad validators:
  - `shared/validators/account_validator.py`
  - `shared/validators/campaign_validator.py`
  - `shared/validators/targeting_validator.py`
  - `shared/validators/asset_group_validator.py`
  - `shared/validators/asset_validator.py`
- workflow helper:
  - `shared/validators/csv_stage_manager.py`
- PMAX validator:
  - `shared/validators/pmax_campaign/pmax_campaign_validator.py`

## Actual Test Findings

Commands run:

```bash
python3 -m compileall -q shared presentations docs/system_review/api_mcp/google_ads_mcp clients/therappc/thinkhappylivehealthy/build/search_rebuild_test
python3 -m shared.validators.search.search_master_validator --help
python3 -m shared.validators.search_master_validator --help
python3 -m shared.validators.master_validator --help
file clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv
```

Results:

- Full Python syntax compilation passes after the syntax repair batch.
- `shared.validators.search.search_master_validator` imports without crashing, but it has no real command-line behavior.
- `shared.validators.master_validator` imports without crashing, but it also has no useful command-line behavior.
- `shared.validators.search_master_validator` fails at import because `shared/validators/search/__init__.py` does not export `SearchValidator`.
- The current THLH staging CSV is UTF-16, which matches the current generated workflow, but most old validators read only `utf-8-sig`.

Important meaning:

- The folder is parseable.
- The folder is not operationally ready.
- The folder should not be used as the current authority for pass/fail decisions.

## Useful Pieces To Keep

### 1. Google Ads Editor Structure Checks

Useful ideas:

- required columns
- row-level validation
- campaign, ad group, keyword, ad, location, budget, and status checks
- validation report output

Role:

- merge later into the active rebuild validator

Correction needed:

- align headers with the real Google Ads Editor exports being generated now
- support UTF-16 tab-separated files
- avoid assuming one small fixed header set

### 2. Search Campaign Checks

Useful ideas:

- Search campaigns should not be confused with PMAX asset groups
- Search campaigns need ad groups
- Search network settings should be checked
- Final URLs should be checked
- campaign and ad group relationships should be checked

Role:

- salvage for active Search validation

Correction needed:

- normalize field names such as `Campaign Type` versus `Campaign type`
- match current exported column names
- decide which network checks are required, which are warnings, and which are client-specific strategy choices

### 3. Keyword Checks

Useful ideas:

- keywords must not be blank
- keyword rows need an ad group
- keyword length should be checked
- negative keywords need separate handling
- unsupported match types should be caught
- counts by ad group are useful

Role:

- high-value merge target

Correction needed before activation:

- stop treating quoted keywords as required phrase format
- stop treating bracketed exact keywords as normal
- stop treating broad match as normal
- stop recommending exact match
- current rule is plain keyword text in `Keyword` and `Criterion Type` set to `Phrase`
- negative keyword rules need to use the current exported format, such as `Negative Phrase`, not only a leading `-`

### 4. Text Ad And RSA Checks

Useful ideas:

- headline length checks
- description length checks
- repeated-word checks
- excessive punctuation checks
- final URL checks

Role:

- salvage after copy-system alignment

Correction needed:

- older files only expect 3 headlines and 2 descriptions in places
- current RSA standard asks for 15 headlines and 4 descriptions when possible
- one older validator contains Wright's Impact Window & Door specific requirements, so that logic must not be used as shared behavior
- healthcare and therapy policy review needs client and industry context, not one hard-coded brand profile

### 5. Location And Targeting Checks

Useful ideas:

- location format review
- radius review
- bid modifier review
- language review

Role:

- salvage for targeting validation

Correction needed:

- current process prefers `Location ID` when available
- generated city ad groups must include all approved city modifiers
- location rules need to read `targeting_spec.json`, not guess from generic formatting alone

### 6. CSV Stage Manager

Useful ideas:

- stage metadata should not be written into row 1 of the CSV
- validation should have a clear lifecycle
- validation feedback should be written separately

Role:

- keep as process reference

Correction needed:

- old paths assume `campaigns/new_campaigns`
- current generated builds live under `clients/{agency}/{client}/build/{date}_account_rebuild/`
- current final names are `Google_Ads_Editor_Staging_CURRENT.csv` and revision variants

## Unsafe Or Stale Pieces

### 1. PMAX-First Behavior

Several validators still treat PMAX as a normal active path.

Decision:

- keep as reference only
- do not activate for the current Search-first rebuild workflow
- revisit only if the user starts a PMAX phase later

### 2. Broad And Exact Match Assumptions

Some code treats Broad and Exact as normal keyword modes, and one validator recommends exact match when exact usage is low.

Decision:

- do not activate
- rewrite around phrase-only default first

### 3. Broken Root Search Validator Entry Point

`shared/validators/search_master_validator.py` imports `SearchValidator` from `shared.validators.search`, but `shared/validators/search/__init__.py` does not export it.

Decision:

- do not fix only the import yet
- the downstream behavior also needs review, so a simple import fix could make the tool look more ready than it is

### 4. Encoding Mismatch

Current generated staging files are UTF-16 tab-separated CSVs.

Most old validators read `utf-8-sig`.

Decision:

- do not use these validators against current client CSVs until encoding detection is added

### 5. Client Directory Scanning

`MasterValidator.validate_all_clients()` defaults to a generic `google_ads_agent` base directory and scans child folders as clients.

Decision:

- do not use this as active client discovery
- current active layout is `clients/{agency}/{client}/`, with older `clients/{client_slug}/` still active until reviewed

## Role Assignment

| Area | Current Role | Why |
|---|---|---|
| `shared/validators/search/search_keyword_validator.py` | Rewrite before merge | Valuable checks, but wrong match-type assumptions |
| `shared/validators/search/search_campaign_validator.py` | Rewrite before merge | Good Search versus PMAX separation, but wrong auto-fix default and field mismatch |
| `shared/validators/search/search_location_validator.py` | Salvage | Useful targeting checks, but must read `targeting_spec.json` |
| `shared/validators/search/search_text_ad_validator.py` | Salvage | Useful text checks, but not enough for current RSA standard |
| `shared/validators/search/text_ad_validator.py` | Reference only | Contains hard-coded Wright's client rules |
| `shared/validators/account_validator.py` | Rewrite before merge | Useful required-header concept, but current exports have a much larger real column set |
| `shared/validators/campaign_validator.py` | Reference and partial salvage | Contains PMAX and Search mixed together |
| `shared/validators/targeting_validator.py` | Salvage | Useful generic checks, needs current location ID and geo spec alignment |
| `shared/validators/csv_stage_manager.py` | Process reference | Correct principle, stale paths |
| `shared/validators/pmax_campaign/` | Reference only | Not active for current Search-first rebuild workflow |
| `shared/validators/master_validator.py` | Reference only | Orchestration idea is useful, active behavior is not aligned |
| `shared/validators/search_master_validator.py` | Do not use | Import path is broken and downstream behavior is stale |
| `shared/validators/search/search_master_validator.py` | Reference only | Better architecture shape, but not wired to current CSVs |

## Recommended Next Implementation Batch

Build a new active validator path instead of trying to turn the old folder on wholesale.

Recommended first merge:

1. Create or extend an active Google Ads Editor staging validator under `shared/rebuild/`.
2. Support UTF-16, `utf-8-sig`, and `utf-8` input.
3. Validate the current output contract:
   - `Campaign`
   - `Campaign Type`
   - `Networks`
   - `Budget`
   - `Budget type`
   - `EU political ads`
   - `Ad Group`
   - `Criterion Type`
   - `Keyword`
   - `Final URL`
   - location fields including `Location ID` where available
   - RSA fields through `Headline 15` and `Description 4`
4. Enforce current Search rules:
   - phrase match by default
   - no broad match
   - no exact match unless explicitly allowed
   - plain keyword text, not quoted or bracketed keyword text
   - generated CSV remains staging, not auto-upload
5. Run it against:
   - `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv`
6. Compare its output with:
   - `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1_validation.json`

## Delete Nothing From Validators Yet

Nothing in `shared/validators/` should be deleted in this phase.

The folder still contains useful patterns. The correct cleanup path is:

1. salvage the rules into an active validator
2. test against real client builds
3. document what was absorbed
4. only then decide what old validator files are obsolete

## Active Validator Added

The first active replacement path now exists here:

- `shared/rebuild/staging_validator.py`

Purpose:

- validate current Google Ads Editor staging CSVs
- support real staging encodings, including UTF-16
- enforce phrase-only Search rules
- reject broad and exact match unless the system is intentionally changed later
- require plain keyword text in `Keyword`
- require match type in `Criterion Type`
- validate RSA headline and description counts and character limits
- validate campaign-level requirements such as populated `EU political ads`
- preserve campaign-level `Negative Phrase` rows as valid even when they do not have an ad group

Command:

```bash
python3 shared/rebuild/staging_validator.py \
  --csv clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv
```

Result:

- status: `pass`
- encoding detected: `utf-16`
- rows: 470
- campaigns: 4
- ad groups: 49
- phrase keyword rows: 295
- negative phrase rows: 20
- responsive search ad rows: 49
- location rows: 49
- radius rows: 4
- issues: 0

This does not make the old `shared/validators/` folder obsolete. It starts the safer path: move validated ideas into active rebuild tooling, test them against real client artifacts, then later decide what older files are duplicated or stale.

## Active Validator Tests Added

Focused tests now exist here:

- `tests/test_staging_validator.py`

Protected behavior:

- UTF-16 Google Ads Editor staging files can be read.
- Phrase keyword rows pass when `Keyword` is plain text and `Criterion Type` is `Phrase`.
- Campaign-level `Negative Phrase` rows pass without an ad group.
- Broad and exact match keyword rows fail.
- Quoted keyword text fails because match type belongs in `Criterion Type`.
- Campaign-level broad match setting must remain off.
- Missing `Location ID` is a warning, not a failure, because the process prefers IDs when available.
- The checked-in THLH REV1 staging CSV passes with the current expected shape:
  - 470 rows
  - 4 campaigns
  - 49 ad groups
  - 295 phrase keyword rows
  - 20 negative phrase rows
  - 49 responsive search ad rows

Test command:

```bash
python3 -m pytest tests/test_staging_validator.py -q
```

Result:

- 7 passed
