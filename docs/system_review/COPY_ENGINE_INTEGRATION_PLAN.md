# Google Ads Agent - Copy Engine Integration Plan
Last updated: 2026-04-27

---

## Phase 0: Sweep & Grade (What We Have)

### Existing asset generation - honest grades

| Component | File | Grade | Problem |
|---|---|---|---|
| AssetGenerationEngine | `shared/gads/core/business_logic/asset_generation_engine.py` | D | Fully template-based, no LLM, hardcoded for resume/Florida verticals |
| RSAOptimizationTool | `shared/tools/campaign/rsa_optimization_tool.py` | C- | Production Python but locked to one client (impact windows), 3H/2D limit (Google supports 15/4) |
| CTREvaluationEngine | `shared/gads/core/business_logic/ctr_evaluation_engine.py` | C | Scores on 5 criteria but doesn't generate — evaluator with no generator |
| PolicyComplianceChecker | `shared/gads/core/business_logic/policy_compliance_checker.py` | C+ | Catches violations but replacements degrade copy ("guaranteed" → "available") |
| WebsiteContentAnalyzer | `shared/tools/campaign/website_content_analyzer.py` | C | Regex-based USP extraction — no semantic understanding |
| IndustryModifiers | `shared/gads/core/business_logic/industry_modifiers.py` | D+ | 3 industries only, compliance-additive not copy-transformative |
| MASTER_AI_AGENT_INSTRUCTIONS | `shared/MASTER_AI_AGENT_INSTRUCTIONS.md` | F | Zero copywriting guidance — only timeline prohibition rules |
| rsa_campaign_generator.py | `shared/tools/campaign/rsa_campaign_generator.py` | D | Skeleton |
| pmax_theme_generator.py | `shared/tools/campaign/pmax/pmax_theme_generator.py` | Unknown | Needs audit |
| GoogleAdsEditorExporter | `shared/gads/core/business_logic/google_ads_editor_exporter.py` | B | CSV structure is correct, char validation works — no copy intelligence |

### What works well (keep)
- CSV export pipeline + character limit validation (`google_ads_editor_exporter.py`)
- Policy compliance detection (detection only — not the auto-replacement)
- Client config schema and isolation layer
- Workflow orchestration in `google_ads_workflow.py`

### What gets replaced
- All hardcoded headline/description templates
- The 3H/2D limit in RSAOptimizationTool
- Auto-replacement strings in PolicyComplianceChecker

---

## Phase 1: Architecture - Split Asset Generation

### New directory structure

```
shared/
  copy_engine/
    __init__.py
    orchestrator.py              # runs full copy pipeline per campaign type
    models.py                    # OpenRouter/Kimi-k2 client wrapper

    search/
      __init__.py
      headlines.py               # Search RSA headlines (30 char, 8-15 per ad group)
      descriptions.py            # Search RSA descriptions (90 char, 2-4 per ad group)
      paths.py                   # Display paths (15 char each, path1 + path2)
      sitelinks.py               # Sitelink text + desc1 + desc2 (25/35/35 char)
      callouts.py                # Callout text (25 char max)
      structured_snippets.py     # Header + values

    pmax/
      __init__.py
      headlines.py               # PMax short headlines (30 char, up to 15)
      long_headlines.py          # PMax long headlines (90 char, up to 5)
      descriptions.py            # PMax descriptions (90 char, up to 5)
      business_name.py           # Business name (25 char)
      search_themes.py           # PMax search themes (no char limit)

    editor/
      __init__.py
      grader.py                  # 7-sweep quality gate (from copy-editing SKILL.md)
      evaluator.py               # CTR score + policy check + plain-english pass
      reporter.py                # generates human-review report (HTML + JSON)

    frameworks/
      ad_copy_templates.md       # from marketingskills paid-ads/references/
      copy_frameworks.md         # from marketingskills copywriting/references/
      copy_editing_sweeps.md     # from marketingskills copy-editing/SKILL.md
      plain_english.md           # from marketingskills copy-editing/references/
```

---

## Phase 2: Character Count Rules & Copy Rules Per Component

### Search RSA Headlines
- Max chars: **30** (hard limit)
- Count required: **8 minimum, 15 maximum**
- Required mix (enforce in `headlines.py`):
  - 3+ keyword-lead: `[Keyword] + [Benefit]`
  - 2+ benefit-lead: `[Outcome verb] + [Result]`
  - 1+ question: `[Pain point question?]`
  - 1+ proof/social: `[Number] + [Credibility]`
  - 1+ location/geo: `[City] + [Service]`
  - 1+ CTA: `[Action verb] + [Offer]`
- Rules:
  - No word repeated across 3+ headlines
  - Min 2 headlines must include CTA verb
  - No ALL CAPS words
  - No exclamation marks (policy)
  - Avoid: streamline, innovative, cutting-edge, best-in-class, world-class

### Search RSA Descriptions
- Max chars: **90** (hard limit)
- Count required: **2 minimum, 4 maximum**
- Required mix:
  - D1: PAS lead (Problem → Agitate → Solution in one sentence)
  - D2: Benefit + social proof + CTA
  - D3 (if used): Insurance/differentiator + booking CTA
  - D4 (if used): Urgency or geo-specific
- Rules:
  - Each description must stand alone (Google rotates independently)
  - End each description with a period or CTA verb
  - At least 2 descriptions must include a keyword from the ad group

### Search RSA Paths
- Max chars: **15 each** (path1 + path2)
- Format: `[Service Category] / [Qualifier]`
- Examples: `Psychiatry / Near Me`, `ADHD Testing / Ashburn VA`
- No special characters except hyphens

### PMax Short Headlines
- Max chars: **30**
- Count: **3 minimum, 15 maximum**
- Same mix rules as Search headlines

### PMax Long Headlines
- Max chars: **90**
- Count: **1 minimum, 5 maximum**
- Format: Full value proposition sentence — location + service + differentiator
- Must work as standalone ad unit (shown without other headlines)

### PMax Descriptions
- Max chars: **90**
- Count: **2 minimum, 5 maximum**

### Sitelinks
- Link text: **25 char max**
- Description 1: **35 char max**
- Description 2: **35 char max**
- Minimum 4, maximum 20

### Callouts
- Text: **25 char max**
- Minimum 4, maximum 20
- Format: short noun phrases (no verbs, no punctuation)
- Examples: `Accepts Anthem BCBS`, `Online & In-Person`, `Same-Week Appts`

---

## Phase 3: Copy Quality Pipeline (Human-in-the-Loop)

### Workflow per campaign build

```
1. SWEEP EXISTING
   - read current CSV / existing campaigns
   - grade each component (headlines, descs, extensions) against Phase 2 rules
   - output: grade report JSON

2. EVALUATE
   - identify missing components (not enough headline types, missing CTA, etc.)
   - flag policy risks without auto-replacing
   - score readability (plain-english pass)
   - output: gap analysis

3. PLAN
   - propose new copy for each component
   - show what changes vs what stays
   - output: proposed_changes.json

4. HUMAN REVIEW REPORT (HTML)
   - Section A: What we swept (graded table per component)
   - Section B: What we found (gap analysis bullets)
   - Section C: Proposed new copy (side-by-side: current vs proposed)
   - Section D: What will be built next
   - Human approves or edits proposals in report

5. GENERATE
   - run LLM (OpenRouter / kimi-k2) with:
     - client context (service lines, geo, USPs, insurance, landing pages)
     - copy frameworks (PAS, BAB, benefit hierarchy)
     - component-specific rules from Phase 2
   - apply 7-sweep grader
   - apply plain-english pass
   - policy check (flag only, no auto-replace)
   - output: final CSV ready for Google Ads Editor import
```

### LLM config
- Provider: OpenRouter
- Model: `moonshot/kimi-k2`
- Fallback: `google/gemini-2.5-flash`
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`

---

## Phase 4: THHL Test Run

ThinkHappyLiveHealthy.com is the first test account.

Current state:
- 9 ad groups in `THHL_Search_Campaign_2026-04-28.csv` (manually written)
- 5 live campaigns in `ThinkHappyLiveHealthy_export_2026-04-27.csv`

Test sequence:
1. Run sweep/grade on manually-written THHL Search CSV
2. Generate human review report
3. User approves proposed improvements
4. Regenerate all 9 RSAs through new copy engine
5. Compare: manual vs engine-generated (side-by-side HTML)
6. Iterate rules until output matches or beats manual quality

---

## Files to Pull from marketingskills repo

```bash
# Fetch these 4 files into shared/copy_engine/frameworks/
curl -o shared/copy_engine/frameworks/ad_copy_templates.md \
  https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/paid-ads/references/ad-copy-templates.md

curl -o shared/copy_engine/frameworks/copy_frameworks.md \
  https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/copywriting/references/copy-frameworks.md

curl -o shared/copy_engine/frameworks/copy_editing_sweeps.md \
  https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/copy-editing/SKILL.md

curl -o shared/copy_engine/frameworks/plain_english.md \
  https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/copy-editing/references/plain-english-alternatives.md
```

---

## Build Order

| Step | What | Output |
|---|---|---|
| 1 | Fetch 4 framework files from marketingskills | `shared/copy_engine/frameworks/` |
| 2 | Build OpenRouter/Kimi wrapper | `shared/copy_engine/models.py` |
| 3 | Build search/headlines.py with rules + LLM | 15 headlines per ad group |
| 4 | Build search/descriptions.py | 4 descriptions per ad group |
| 5 | Build search/paths.py + sitelinks.py + callouts.py | Extensions |
| 6 | Build editor/grader.py (7-sweep) | Quality gate |
| 7 | Build editor/reporter.py | HTML human-review report |
| 8 | Build editor/evaluator.py | Gap analysis + grade table |
| 9 | Build copy_engine/orchestrator.py | Full pipeline runner |
| 10 | Test run on THHL - Search Campaign | Side-by-side comparison report |
| 11 | PMax copy engine (same structure) | After Search validated |
