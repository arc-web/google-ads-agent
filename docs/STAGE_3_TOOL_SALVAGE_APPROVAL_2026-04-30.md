# Stage 3 Tool Salvage Approval

Date: 2026-04-30

## Plain-English Summary

I reviewed the older tool folders by what they actually do, not just by their names.

The short version:

- There is useful work here.
- It should not be turned on as-is.
- The useful pieces should be mined and merged into the current `Google_Ads_Agent` process later.
- Nothing in these reviewed tool areas should be deleted just because it looks old.
- Removal requires a later role review, test run, and clear reason why the code is no longer needed.

The current agent from Stage 1 remains the source of truth. These older tools are candidates for salvage, not the active system.

## Areas Reviewed

- `shared/gads/`
- `shared/tools/`
- `shared/validators/`
- `shared/config/`
- `mcp/`
- `docs/browser_automation/`

## What I Found

### 1. `shared/validators/`

Recommendation: merge selected validation logic into the current agent.

This folder has real value. It checks campaign rows, search campaign rows, keywords, locations, budgets, asset groups, and CSV staging details.

But it is not clean enough to accept wholesale:

- Some validation still assumes Performance Max is a normal active path.
- Some keyword logic treats broad and exact match as normal options.
- One search auto-fix defaults missing match type to `Exact`, which conflicts with the current phrase-match Search default.
- The current agent requires Google Ads Editor staging files, validation output, and human review, so the validation idea is right.
- The old implementation needs alignment before it is trusted.

Decision:

- Keep as salvage.
- Later merge the Search and Google Ads Editor validation ideas into the current rebuild flow.
- Do not run these validators as the current final authority yet.
- Do not remove validator files until the active rebuild system has tested replacements or confirmed which rules are obsolete.

### 2. `shared/tools/campaign/`

Recommendation: salvage specific tools, archive or delete the rest later.

Useful candidates:

- `str_keyword_analyzer.py`
- `map_keywords_to_campaigns.py`
- `rsa_optimization_tool.py`, as idea material only
- selected sitelink and RSA generation concepts

Why these matter:

- The search-term analyzer understands Google Ads Search Term Report style inputs.
- The keyword mapping tool works toward Google Ads Editor-ready CSV outputs.
- These are close to the agent's current job: take real account exports and reports, then produce reviewable staging work.

Problems:

- `str_keyword_analyzer.py` sometimes recommends `Exact` for converting terms, but current rules say phrase match by default.
- Some tools assume old client folders such as root-level `my_expert_resume`.
- Some generators are tied to old PMAX or broad-match thinking.
- The old client template generator conflicts with the current template system under `templates/client_template/` and `shared/rebuild/scaffold_client.py`.

Decision:

- Keep the useful campaign analysis and mapping ideas.
- Do not keep the old client generator as active.
- Do not delete PMAX-first or broad/exact-first tools yet.
- Later assign each tool one role: active merge, reference, archive summary, or proven obsolete.

### 3. `shared/tools/website/`

Recommendation: keep as reference, then rebuild properly later.

This area matches a real current need because website scans are part of the current process.

Problem:

- `website_scanner.py` is not a real scanner yet. It simulates output from one old client site.
- The README itself says production use would need real browser automation.

Decision:

- Keep the concept.
- Do not call it active.
- Later replace it with a real repo-local website scan tool that writes `website_scan.json` into the client build folder.
- Preserve it until the replacement has been tested.

### 4. `shared/config/`

Recommendation: keep reference values only, not default behavior.

Useful parts:

- Character limits.
- Ad format limits.
- Some Google Ads settings references.

Problems:

- `campaign_defaults.yaml` tries to define defaults for Search, Display, PMAX, Shopping, Video, App, Discovery, and Local.
- That is broader than the current agent.
- It includes PMAX and multi-campaign-type automation that conflicts with the current Search-first rebuild process.
- It references old client-specific paths and examples.

Decision:

- Preserve ad limits and character-limit ideas.
- Do not use old campaign defaults as active defaults.
- Current active defaults stay in the current process docs and rebuild tooling.
- Keep all config files until each value has been reviewed against the current build outputs and Google Ads Editor staging requirements.

### 5. `shared/gads/`

Recommendation: keep as a reference library, then mine it carefully.

This is the largest old tool area. It includes:

- Google Ads API service ideas.
- MCP integration ideas.
- Google Ads Editor exporter ideas.
- asset generation ideas.
- client onboarding workflow ideas.
- compliance checking ideas.
- reporting engine ideas.
- PMAX campaign generation.
- ad group, keyword, and extension management systems.

Useful salvage:

- Google Ads Editor exporter concepts.
- policy and compliance checks.
- client onboarding workflow ideas.
- client reporting ideas.
- source/reference helper concepts.
- ad copy and asset quality checks.

Not active:

- Google Ads API execution.
- MCP orchestration.
- Airtable or Gmail workflow automation.
- PMAX campaign builders.
- broad or exact match keyword systems.
- automatic file cleanup or auto-archive behavior.

Important concern:

- `shared/gads/core/file_management.py` aggressively archives and deletes files. That conflicts with the current cleanup rule, where client history is preserved until reviewed and summarized.

Decision:

- Keep for salvage.
- Mine the useful logic later.
- Do not let this folder drive active client work yet.
- Do not remove modules here until the current system has test runs showing which logic is duplicated, unsafe, or obsolete.

### 6. `mcp/`

Recommendation: archive note only for now.

This folder is about Google Ads MCP setup, credential collection, and MCC testing.

Problems:

- It points to external local paths outside this repo.
- It references Claude MCP commands.
- Its test log shows a broken import: `cannot import name 'create_server' from 'ads_mcp.server'`.
- It is not part of the current Google Ads Editor staging workflow.

Decision:

- Keep a short record that this existed.
- Do not merge into the active agent right now.
- Revisit only when the user intentionally starts a later API/MCP phase.
- Preserve until API/MCP scope is intentionally reviewed.

### 7. `docs/browser_automation/`

Recommendation: archive note only for now.

This folder documents browser automation for credentials.

Problems:

- It points to old external paths such as `/Users/home/aimacpro/...`.
- It assumes a separate browser automation agent.
- It is about credential setup, not the current local cleanup or Google Ads Editor staging process.

Decision:

- Keep a note that this existed.
- Do not treat it as current operating documentation.
- Revisit only in a later API/MCP credential phase.
- Preserve until credential and browser automation scope is intentionally reviewed.

## Recommended Salvage Map

### Merge Later Into Current Agent

- Search and Google Ads Editor validation ideas from `shared/validators/`.
- Search term report analysis from `shared/tools/campaign/str_keyword_analyzer.py`.
- Keyword-to-campaign mapping from `shared/tools/campaign/map_keywords_to_campaigns.py`.
- Selected Google Ads Editor exporter concepts from `shared/gads/core/business_logic/google_ads_editor_exporter.py`.
- Compliance and policy-checking ideas from `shared/gads/core/business_logic/policy_compliance_checker.py`.
- Client onboarding workflow ideas from `shared/gads/core/business_logic/client_onboarding_workflow.py`.
- Character-limit and ad-limit references from `shared/config/`.

### Keep As Reference Only

- Most of `shared/gads/`.
- `shared/tools/website/`.
- Google Ads reference helper ideas in `shared/gads/tools/google_ads_reference_tool.py`.
- Some RSA and sitelink generation concepts.

### Archive Note Only

- `mcp/`
- `docs/browser_automation/`
- old API/MCP credential collection plans
- old Airtable and Gmail automation ideas
- old external-path setup notes

### Delete Later Only After Proof

- `__pycache__/`
- `.pyc` files
- stale MCP test result logs
- stale generated test reports
- old duplicate examples only after they are summarized
- tools that only support old root-level client folder behavior only after a replacement exists or the behavior is proven irrelevant

Deletion standard:

- The item has been reviewed for current and future use.
- Its useful lessons have been moved into an active tool, a reference note, or an archive summary.
- A test run or direct code comparison proves it is duplicated, unsafe, or not part of the agent direction.
- The reason for removal is written down before deletion.

### Do Not Activate Without Rewrite

- PMAX generators.
- broad-match keyword managers.
- exact-match-first keyword logic.
- aggressive file auto-archive tools.
- old client template generator.
- simulated website scanner.
- API/MCP execution code.

## My Recommendation For Your Approval

Approve Stage 3 as a tool salvage decision, not as a code merge.

That means:

1. We keep the old tool folders visible for now.
2. We record which pieces are worth salvaging.
3. We do not commit to using the old tools as active automation.
4. We defer deletion until the whole system is tested and each tool has a role.
5. In later cleanup stages, we summarize stale API/MCP and PMAX material before any removal.

## Why This Is The Right Next Step

This protects useful tool thinking without letting stale automation control the current agent.

The default posture is now preservation. These folders contain too many relevant ideas to remove early. Cleanup should reduce risk and clutter only after test runs prove what can safely go.

The agent you are actively building is still:

- Search-first.
- Phrase-match by default.
- Google Ads Editor staging-first.
- Client-history preserving.
- HTML/PDF report focused.
- Built around `clients/{agency}/{client}/`, `templates/client_template/`, `shared/rebuild/`, and `presentations/`.

## Sources Checked

- `AGENTS.md`
- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `shared/rebuild/scaffold_client.py`
- `shared/validators/master_validator.py`
- `shared/validators/search/search_keyword_validator.py`
- `shared/tools/campaign/str_keyword_analyzer.py`
- `shared/tools/campaign/map_keywords_to_campaigns.py`
- `shared/tools/campaign/client_structure_validator.py`
- `shared/tools/website/website_scanner.py`
- `shared/gads/core/file_management.py`
- `shared/gads/tools/google_ads_reference_tool.py`
- `shared/config/campaign_defaults.yaml`
- `mcp/test_results/server_init_test.log`
- `docs/browser_automation/readme_automation.md`
