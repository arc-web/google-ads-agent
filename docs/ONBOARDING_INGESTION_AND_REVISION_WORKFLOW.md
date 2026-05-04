# Onboarding, Ingestion, And Revision Workflow

Date: 2026-04-28

## Purpose

`Google_Ads_Agent` must separate three sources of truth before it builds or revises campaigns:

1. Client onboarding and client feedback.
2. Website scan and landing page evidence.
3. Ad account, search term, location, conversion, and analytics data.

The client is the source of truth for business facts. The website is the source of truth for what prospects can verify before converting. Account and analytics data are the source of truth for observed historical performance, but only when the old campaign structure was capable of producing clean evidence.

Client feedback should improve the build engine. It should not automatically override campaign architecture.

## Source-Of-Truth Rules

### Client Feedback

Use client feedback as authoritative for:

- Services offered.
- Services not offered.
- Current capacity.
- Insurance, billing, and reimbursement language.
- Provider licensing, geography, and telehealth limits.
- Legal entity changes.
- Brand voice and claim approval.
- Priority services and revenue goals.

Do not use client feedback as automatically authoritative for:

- How many campaigns should exist.
- How many ad groups should exist.
- How many keywords should exist.
- Whether a geography should be excluded based only on old weak data.
- Bidding method, unless it is tied to budget, risk, compliance, or business constraints.

### Website Evidence

Use website evidence as authoritative for:

- Public service pages.
- Landing page availability.
- Visible locations.
- Public-facing claims.
- Insurance language visible to prospects.
- Calls to action.
- Whether the page supports the campaign promise.

If client feedback contradicts the website, flag it as a website guidance item instead of silently changing only the campaign.

Example:

- Client says Maryland is low priority.
- Website does not explain Maryland access, Maryland telehealth limits, or Maryland location logistics.
- Campaign decision may be to exclude Maryland or keep it separate.
- Website guidance may be to create a Maryland page or clarify service limits before spending there.

### Account And Analytics Evidence

Use account and analytics data as authoritative only when the historical structure supports the conclusion.

Reliable evidence usually requires:

- Clear campaign and ad group separation.
- Enough spend.
- Enough impressions and clicks.
- Clean conversion tracking.
- Matching landing pages.
- Search terms mapped to the right service.
- Location reporting at the right level.

Unreliable evidence includes:

- Mixed services inside one ad group.
- Broad match traffic.
- Weak or missing conversion tracking.
- Low spend.
- No landing page match.
- Regions that were targeted but not messaged correctly.
- Campaigns that were not structured to test the question being asked.

## Automation Stages

### Stage 0: Client Intake

Collect structured client truth before strategy generation.

Required outputs:

- `client_intake.json`
- `business_constraints.json`
- `service_priority_matrix.csv`
- `compliance_claims_review.csv`
- `capacity_and_exclusions.csv`

Questions to capture:

- What services are active now?
- What services should not be advertised?
- Which services have provider capacity?
- Which services need more volume?
- Which locations are licensed, practical, and profitable?
- Which insurance claims are approved?
- Which age groups are eligible?
- Which legal entity name should appear in verification and billing?

### Stage 1: Website Evidence Scan

Scan the site and map what is actually supported.

Required outputs:

- `website_scan.json`
- `landing_page_map.json`
- `website_evidence_gaps.csv`

Evidence gap examples:

- Campaign references Anthem/CareFirst BCBS, but the site says "most major insurance."
- Campaign targets Maryland, but the site does not explain Maryland service access.
- Client says no EMDR openings, but the site still presents EMDR as available.
- Client says ADHD testing ends at age 21, but site copy implies general adult testing.

### Stage 2: Account And Analytics Ingestion

Ingest historical account and performance data.

Required outputs:

- `account_snapshot.json`
- `account_audit.json`
- `search_term_analysis.csv`
- `geo_performance_analysis.csv`
- `conversion_tracking_audit.json`
- `evidence_quality_report.json`
- `optimization_cadence_plan.json`
- `bid_strategy_recommendation.json`
- `audience_mode_audit.json`
- `recommendations_triage.csv`
- `policy_disapproval_audit.json`
- `launch_readiness_checklist.md`

The evidence quality report must label each conclusion:

- `strong`
- `directional`
- `weak`
- `not_tested`

This prevents old bad structure from creating false negatives.

Department training standards are loaded from `shared/config/department_standards.yaml`.
Rules must keep a scope of `global`, `search_rebuild`, `optimization`, `launch_readiness`, `automotive`, or `manual_sop`.
Automotive rules stay in the automotive profile and must not become global shared logic.

### Stage 3: Strategy Synthesis

Merge client truth, website evidence, and account data into a build strategy.

Required outputs:

- `strategy_brief.md`
- `service_catalog.json`
- `campaign_taxonomy.csv`
- `geo_strategy.json`
- `budget_weighting_plan.csv`
- `website_guidance_for_client.md`

Decision hierarchy:

1. Compliance and legal constraints.
2. Client service availability and capacity.
3. Landing page support.
4. Historical data quality.
5. Performance opportunity.
6. Campaign simplicity and clean measurement.

### Stage 4: Build

Generate the staged CSV and review document.

Required outputs:

- `Google_Ads_Editor_Staging_CURRENT.csv`
- `rsa_copy_matrix.csv`
- `keyword_matrix.csv`
- `negative_review_candidates.csv`
- `targeting_spec.json`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`
- `validation_report.json`

Google Ads Editor remains the staging environment.

### Stage 5: Client Review

Collect client feedback in a structured format.

Required outputs:

- `client_feedback_round_1.md`
- `client_feedback_classified.json`
- `revision_plan.md`

Every feedback item must be classified as one of:

- `business_fact`
- `capacity_constraint`
- `compliance_or_claim`
- `website_gap`
- `campaign_revision`
- `strategy_question`
- `tracking_or_measurement`
- `legal_or_verification`
- `client_preference`
- `expert_override_needed`

### Stage 6: Revision Triage

Do not blindly apply all feedback to the CSV.

For each item, decide:

- Campaign change now.
- Website guidance only.
- Build engine rule update.
- Manual one-off revision script.
- Strategy discussion before change.
- Compliance or legal review before change.

Required outputs:

- `revision_decision_log.csv`
- `engine_rule_updates.md`
- `one_off_revision_patch.md`
- `client_questions_for_call.md`

### Stage 7: Revised Build

Apply approved revisions and regenerate the outputs.

Required outputs:

- `Google_Ads_Editor_Staging_REV1.csv`
- `Client_Rebuild_Review_R1.html`
- `Client_Rebuild_Review_R1.pdf`
- `revision_validation_report.json`
- `client_change_summary.md`

### Stage 8: Launch Readiness

Before posting from Google Ads Editor:

- Confirm conversion tracking and PHI handling.
- Confirm healthcare advertiser verification and entity timing.
- Confirm final services, age ranges, regions, and insurance language.
- Confirm budget and bidding plan.
- Confirm website gaps that affect launch risk.

Required outputs:

- `launch_readiness_checklist.md`
- `posting_notes.md`

## Feedback Classification For Current Client Notes

### Insurance

Classification:

- `business_fact`
- `compliance_or_claim`
- `campaign_revision`
- `website_gap`

Campaign action:

- Replace any language implying most major insurance is directly accepted.
- Use clean language such as `In-network with Anthem BCBS. Superbills provided for out-of-network benefits.`
- Avoid listing carriers that are not directly billed.

Engine rule update:

- Insurance claims require exact client-approved payer language.
- If client says only one carrier is in-network, do not use broad phrases like `most major insurance`.

Website guidance:

- If the site says broader insurance language, flag that as a possible mismatch.

### EMDR

Classification:

- `capacity_constraint`
- `campaign_revision`
- `website_gap`

Campaign action:

- Remove EMDR from active headlines, descriptions, keywords, and roadmap.
- Add EMDR to a paused future-opportunity note only if the client approves.

Engine rule update:

- Service presence on website is not enough. Active ad copy requires current capacity.

Website guidance:

- If the website still promotes EMDR, note that prospects may expect availability.

### ADHD Testing Through Age 21

Classification:

- `business_fact`
- `campaign_revision`
- `negative_keyword_update`
- `website_gap`

Campaign action:

- Reposition as `ADHD Testing for Children, Teens, and Young Adults`.
- Avoid `adult ADHD testing` positioning.
- Add adult-intent negatives such as `adult adhd test`, `adult adhd testing`, and `adhd test for adults`.

Engine rule update:

- Age eligibility must bind keyword generation, RSA copy, and negative keyword generation.

Website guidance:

- If site pages do not clearly say through age 21, flag it for client awareness.

### Parent-Child Versus Standalone Family Therapy

Classification:

- `business_fact`
- `campaign_revision`
- `negative_keyword_update`
- `website_gap`

Campaign action:

- Replace `Family Therapy Services` with `Parent-Child Therapy` or `Family Support Services`.
- Remove standalone `family counseling` language.
- Add negatives for `family therapy`, `family counseling`, and `family therapist`.

Engine rule update:

- Adjacent service language must be checked against whether it is a standalone service or a support context.

### Psychiatry Growth Target

Classification:

- `strategy_question`
- `business_priority`
- `budget_weighting`

Recommended stance:

- Treat the growth target as authoritative.
- Do not let it automatically create more ad groups.
- Use budget, campaign weighting, and possibly a psychiatry-focused campaign split to control volume.

Possible restructure:

- Launch `ARC - Search - Psychiatry - V1` as the highest-priority campaign.
- Keep adult therapy and testing lower weighted.
- Use budget allocation and clean search term mapping before adding unnecessary ad groups.

### Brand Campaign On Day 1

Classification:

- `strategy_question`
- `campaign_revision`

Recommended stance:

- Reasonable to launch day 1 if budget is modest and the goal is clean brand coverage.
- Keep it separate from nonbrand so reporting stays clean.
- Use a capped budget such as the requested monthly range if approved.

### Bidding, Geo Modifiers, And Conversion Tracking

Classification:

- `tracking_or_measurement`
- `strategy_question`
- `compliance_or_claim`

Recommended stance:

- Explain whether manual bid modifiers will actually affect bidding under the selected bid strategy.
- Under Smart Bidding strategies, many manual bid adjustments are limited or not used the same way as manual bidding.
- If geography needs stronger control, split campaigns or use separate budgets rather than assuming bid modifiers will steer everything.

Tracking rule:

- No PHI should be passed to Google Analytics or Google Ads measurement.
- Conversion pipeline must be reviewed before launch.

### Maryland Exclusion

Classification:

- `strategy_question`
- `geo_decision`
- `website_gap`

Recommended stance:

- Do not exclude only because old CPA was high if the structure could not test Maryland cleanly.
- Exclude or separate Maryland if licensing, telehealth, commute friction, or website mismatch makes it strategically weak.
- If kept, isolate Maryland in its own test with clear landing page support and capped budget.

### PLLC And Healthcare Verification

Classification:

- `legal_or_verification`
- `launch_readiness_blocker`

Recommended stance:

- Track entity name timing before launch.
- Avoid verification changes mid-flight when possible.
- Add this to launch readiness and account verification planning.

## Client Feedback Guardrail

Client feedback should answer:

- What is true?
- What is allowed?
- What is available?
- What is profitable?
- What should be prioritized?

The build engine should answer:

- How should campaigns be structured?
- Which levers should express priority?
- Whether the requested change should be a budget change, bid strategy change, campaign split, keyword change, copy change, or website recommendation.

When client feedback conflicts with campaign best practice, create a strategy discussion item instead of applying the change directly.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads bid adjustments: https://support.google.com/google-ads/answer/2732132?hl=en
- Google Ads Editor location bid adjustments: https://support.google.com/google-ads/editor/answer/47629?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google Ads healthcare and medicines policy: https://support.google.com/adspolicy/answer/176031?hl=en
- Google Ads customer data policies: https://support.google.com/google-ads/answer/7475709?hl=en
- Google Analytics HIPAA guidance: https://support.google.com/analytics/answer/13297105?hl=en
