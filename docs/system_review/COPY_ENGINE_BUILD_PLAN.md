# Copy Engine Build Plan
Last updated: 2026-04-27
Status: AWAITING CONFIRMATION

---

## Scope

Phase 1: Search Ads only. PMax deferred until Search is proven.
Test client: ThinkHappyLiveHealthy.com (TherapPC).
LLM: OpenRouter / `moonshot/kimi-k2`.
Workflow per build: sweep → grade → HITL report → human approves → generate → validate → export.

---

## Phase 1: Search Ads Copy Engine

---

### Stage 0 — Foundation
**Must complete before anything else. Run 0A + 0B in parallel.**

#### 0A — Fetch framework files
Pull 4 reference files from marketingskills repo into the agent.

```
shared/copy_engine/frameworks/
  ad_copy_templates.md       ← paid-ads/references/ad-copy-templates.md
  copy_frameworks.md         ← copywriting/references/copy-frameworks.md
  copy_editing_sweeps.md     ← copy-editing/SKILL.md
  plain_english.md           ← copy-editing/references/plain-english-alternatives.md
```

Also pull from aimacpro (already mapped, don't rebuild):
```
shared/copy_engine/frameworks/
  ad_character_limits.yaml   ← aimacpro config/ad_character_limits.yaml
  ad_limits.yaml             ← aimacpro config/ad_limits.yaml
```

#### 0B — OpenRouter/Kimi-k2 client
File: `shared/copy_engine/models.py`

- `class OpenRouterClient`
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Default model: `moonshot/kimi-k2`
- Fallback model: `google/gemini-2.5-flash`
- Credential: `OPENROUTER_API_KEY` pulled via OpenBao at runtime
- Methods: `complete(system, user, max_tokens) → str`, `complete_json(system, user, schema) → dict`
- No hardcoded keys

**Stage 0 gate:** both files exist + `models.py` makes a successful test call before Stage 1 starts.

---

### Stage 1 — Search Asset Generators
**Run 1A + 1B + 1C in parallel. All require Stage 0.**

#### 1A — Headlines
File: `shared/copy_engine/search/headlines.py`

Character rules:
- Hard limit: 30 chars (reject over)
- Min: 8, Max: 15 per ad group

Required mix (enforced, not suggestions):
| Type | Min count | Formula |
|---|---|---|
| Keyword-lead | 3 | `[Keyword] + [Benefit]` |
| Benefit-lead | 2 | `[Outcome verb] + [Result]` |
| Question | 1 | `[Pain point?]` |
| Proof | 1 | `[Number/stat] + [Credibility]` |
| Geo | 1 | `[City/Region] + [Service]` |
| CTA | 1 | `[Action verb] + [Offer]` |

Forbidden:
- ALL CAPS words
- Exclamation marks
- Words: streamline, innovative, cutting-edge, best-in-class, world-class, comprehensive, robust
- Same word in 3+ headlines
- Duplicate headline meaning across mix types

System prompt sources: `frameworks/ad_copy_templates.md` + `frameworks/copy_frameworks.md`

Input: `AdGroupContext(name, service, geo, USPs, top_keywords, landing_url, industry)`
Output: `list[Headline(text, char_count, mix_type)]`

#### 1B — Descriptions
File: `shared/copy_engine/search/descriptions.py`

Character rules:
- Hard limit: 90 chars (reject over)
- Min: 2, Max: 4 per ad group

Required structure:
| Slot | Role | Formula |
|---|---|---|
| D1 | PAS | Problem → Agitate → Solution (one sentence) |
| D2 | Proof + CTA | Benefit + social proof + booking verb |
| D3 | Differentiator | Insurance / unique qualifier + CTA (if slot used) |
| D4 | Geo/urgency | Location-specific or urgency signal (if slot used) |

Rules:
- Each description works standalone (Google rotates independently)
- End with period or CTA verb
- Min 2 descriptions include ad group primary keyword
- No "we" lead (start with benefit or problem, not the business)

System prompt sources: `frameworks/ad_copy_templates.md`

Input: `AdGroupContext`
Output: `list[Description(text, char_count, role)]`

#### 1C — Extensions
File: `shared/copy_engine/search/extensions.py`

**Sitelinks:**
- Link text: 25 char max
- Description line 1: 35 char max
- Description line 2: 35 char max
- Min 4, max 20

**Callouts:**
- Text: 25 char max
- Noun phrases only — no verbs, no punctuation, no exclamation
- Min 4, max 20

**Structured Snippets:**
- Header: must be from Google's approved list (Services, Types, Styles, etc.)
- Values: 25 char max each, min 3 values per header

Input: `ClientContext(services, geo, insurance_accepted, USPs, practice_type)`
Output: `Extensions(sitelinks, callouts, snippets)`

---

### Stage 2 — Quality Gate
**Run 2A + 2B in parallel. Require Stage 0 only (can run parallel to Stage 1).**

#### 2A — 7-Sweep Grader
File: `shared/copy_engine/editor/grader.py`

Runs 7 sequential LLM passes per asset (from copy-editing SKILL.md):
1. **Clarity** — reader comprehension, no ambiguity
2. **Voice/Tone** — consistent personality, no corporate speak
3. **So What** — every claim tied to reader benefit
4. **Prove It** — assertions backed by evidence or specifics
5. **Specificity** — vague words → concrete replacements
6. **Emotion** — resonance, not sterile
7. **Zero Risk** — barriers to action removed

Each pass: asset in → issues flagged → rewrite suggested (not auto-applied)
Output: `GradeReport(asset, sweep_scores[7], issues[], suggestions[], overall_grade)`

Grades: A (90-100), B (75-89), C (60-74), D (40-59), F (<40)

#### 2B — Evaluator
File: `shared/copy_engine/editor/evaluator.py`

Four checks (no auto-fixing, flag only):
1. **Policy** — flag violations from `policy_compliance_checker.py` detection logic
2. **Plain English** — suggest swaps from `frameworks/plain_english.md`
3. **Char validation** — hard fail anything over limit
4. **Mix compliance** — required headline types present? keyword in min 2 descriptions?

Output: `EvalReport(policy_flags[], word_swaps[], char_violations[], mix_gaps[])`

---

### Stage 3 — HITL Report
**Requires Stage 2. Single file.**

#### 3A — HTML Reporter
File: `shared/copy_engine/editor/reporter.py`

Generates: `clients/[agency]/[client]/reports/[client]_copy_review_[date].html`
Opens automatically after generation (rule: open files immediately).

Report structure:

**Section A — Sweep Grades**
Table per ad group: component | grade | top 3 issues

**Section B — Gap Analysis**
Bullets: missing headline types, char violations, policy flags, weak descriptions

**Section C — Side-by-Side Proposals**
Per ad group: current (left) | proposed (right)
Changed words: yellow highlight. New additions: green highlight.

**Section D — What Gets Built Next**
Checkbox list of what the engine will generate upon approval
Human marks up, approves, or redirects before generation runs.

---

### Stage 4 — Orchestrator
**Requires all stages. Single file.**

#### 4A — Pipeline runner
File: `shared/copy_engine/orchestrator.py`

```
load_client_context(client_dir)
  → read_existing_csv(path)           # read current Google Ads Editor export
  → sweep_and_grade(csv_rows)         # Stage 2A per component
  → evaluate_rules(csv_rows)          # Stage 2B
  → generate_report(grade, eval)      # Stage 3A → open HTML
  → [PAUSE — human reviews, approves]
  → generate_search_copy(context)     # Stages 1A + 1B + 1C
  → grade_new_copy(generated)         # Stage 2A again on new copy
  → export_csv(approved_copy)         # google_ads_editor_exporter.py
```

Human pause is explicit — orchestrator exits after report, resumes only on `--approved` flag.

---

### Stage 5 — THHL Test Run
**Requires Stage 4.**

Input: `THHL_Search_Campaign_2026-04-28.csv` (9 ad groups, manually written)

Steps:
1. Sweep + grade manually-written RSAs → report
2. Human reviews report → approves or edits
3. Regenerate all 9 ad groups through engine
4. Grade engine output
5. Side-by-side HTML: manual vs engine
6. Iterate rules until engine output grades ≥ manual

Pass criteria: all 9 ad groups grade B or above, zero char violations, zero policy flags.

---

## Parallel execution map

```
Stage 0A ──┐
Stage 0B ──┴── gate ──► Stage 1A ──┐
                         Stage 1B ──┤
                         Stage 1C ──┤
                         Stage 2A ──┤
                         Stage 2B ──┴── Stage 3A ──► Stage 4A ──► Stage 5
```

0A + 0B parallel → gate check → 1A + 1B + 1C + 2A + 2B all parallel → 3A → 4A → 5.

---

## Directory when Phase 1 complete

```
shared/copy_engine/
  __init__.py
  models.py
  orchestrator.py
  frameworks/
    ad_copy_templates.md
    copy_frameworks.md
    copy_editing_sweeps.md
    plain_english.md
    ad_character_limits.yaml
    ad_limits.yaml
  search/
    __init__.py
    headlines.py
    descriptions.py
    extensions.py
  editor/
    __init__.py
    grader.py
    evaluator.py
    reporter.py
```

---

## What does NOT change (Phase 1)

- `google_ads_editor_exporter.py` — kept as-is, called by orchestrator for final CSV
- `policy_compliance_checker.py` — detection logic reused by evaluator.py, auto-replace stays disabled
- `client_config_schema.py` — client context schema feeds into `AdGroupContext`
- All existing client campaign CSVs — read-only inputs to sweep, never modified
- PMax tooling — untouched until Phase 2

---

## Phase 2 (deferred)

PMax copy engine — same structure (headlines, long headlines, descriptions, search themes).
Only begins after THHL Search test run passes criteria above.
