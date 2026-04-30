# RSA Copy Generation System

Date: 2026-04-28

Client: ThinkHappyLiveHealthy

Campaign: `THHL - Search - Services - RevKey`

## Goal

Build a repeatable process for creating one responsive search ad per ad group, with 15 headlines, 4 descriptions, custom URL paths, and a final URL that matches the service and intent layer.

The automation should not write one generic ad and copy it across the campaign. It should reuse some proven account-wide language, but every ad group needs service-specific and intent-specific assets.

## Source Inputs

- Ad group taxonomy: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/service_ad_group_taxonomy_2026-04-28.csv`
- Search term evidence: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/organized_search_terms_2026-04-28.csv`
- Location evidence: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/organized_locations_2026-04-28.csv`
- Copy blueprint: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/rsa_copy_blueprint.json`
- Existing copy review: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/reports/thinkhappylivehealthy_copy_review_2026-04-27.html`
- Google RSA reference: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google AI Search steering reference: https://support.google.com/google-ads/answer/12159014?hl=en
- Google Ads API RSA reference: https://developers.google.com/google-ads/api/docs/responsive-search-ads/overview

## RSA Format

Each ad group should produce:

- 15 headlines, max 30 characters each.
- 4 descriptions, max 90 characters each.
- Path 1, max 15 characters.
- Path 2, max 15 characters.
- Final URL matched to the service landing page.

Google can mix RSA assets at serve time, so every headline and description must make sense independently. Descriptions should not depend on another description to complete the thought.

## Asset Mix

Each RSA should be assembled from four asset types.

Ad-group-specific assets:

- Primary keyword headline.
- Service variant headline.
- Audience or category headline.
- Landing page match headline.
- Backup keyword headline.
- Description 1 focused on the service fit.

Geo and intent-layer assets:

- Local, city, or state headline.
- `near me`, Ashburn, Falls Church, Virginia, or Northern Virginia access headline.
- Description 3 focused on location access.
- Path 2 based on `General`, `Local`, `City`, or `State`.

Service-specific reusable assets:

- Service benefit headline.
- Differentiator headline.
- Description 2 focused on care process or evaluation process.
- Path 1 based on service.

Account-shared assets:

- Appointment CTA.
- Consultation CTA.
- Telehealth or in-person option.
- Licensed clinician language.
- Ashburn and Falls Church location language.
- Description 4 with CTA and access qualifier.

## Headline Slot Design

Use all 15 headline slots. The slots do not have to be pinned at first, but the generator should label each role for review.

1. Primary keyword, ad-group-specific.
2. Service variant, ad-group-specific.
3. Intent layer, ad-group-specific.
4. Audience or category, ad-group-specific.
5. Landing page match, ad-group-specific.
6. City or state, geo-layer.
7. Local access or near me, geo-layer.
8. Ashburn and Falls Church, account-shared.
9. Care quality, account-shared.
10. Appointment CTA, account-shared.
11. Consultation CTA, account-shared.
12. Telehealth or in-person, account-shared.
13. Insurance or access, account-shared if verified.
14. Differentiator, service-specific.
15. Backup keyword, ad-group-specific.

This creates the balance we want: enough shared language for consistency, enough specific language for relevance, and enough geo language for local intent.

## Description Slot Design

Use exactly 4 descriptions.

Description 1, service fit:

- Explain the service in plain language.
- Include the main keyword naturally.
- Avoid implying the user has a sensitive condition.

Description 2, care process:

- Explain process, matching, testing, therapy, or psychiatry workflow.
- Mention licensed clinicians or evaluation process where relevant.

Description 3, location access:

- Ashburn, Falls Church, Northern Virginia, telehealth, or city-specific access.
- For `City` ad groups, mention the city if it fits within 90 characters.

Description 4, CTA and qualifier:

- Book appointment, request appointment, consultation, or matched clinician.
- Use only true claims.

## URL And Path Rules

Final URL:

- Must match the service landing page.
- If a service-specific landing page exists, use it.
- If not, use the closest parent landing page and flag the ad group for human review.

Path 1:

- Service family or category, such as `Therapy`, `Testing`, `Psychiatry`, `EMDR`, `ADHD`, `Autism`.
- Must be 15 characters or fewer.

Path 2:

- Intent layer or geo, such as `Near-Me`, `Ashburn`, `FallsChurch`, `Virginia`, `Care`.
- Must be 15 characters or fewer.

Examples:

- `thinkhappylivehealthy.com/Therapy/Near-Me`
- `thinkhappylivehealthy.com/Testing/Ashburn`
- `thinkhappylivehealthy.com/Psychiatry/Virginia`

## Landing Page Mapping

Known pages from the site and search results:

- Psychiatry: `https://www.thinkhappylivehealthy.com/psychiatry`
- ADHD therapy: `https://www.thinkhappylivehealthy.com/adhd-therapy`
- EMDR therapy: `https://www.thinkhappylivehealthy.com/emdr-therapy`
- Child psychological testing: `https://www.thinkhappylivehealthy.com/comprehensive-psychological-testing`
- Psychoeducational evaluations: `https://www.thinkhappylivehealthy.com/psychoeducational-evaluations`
- Kindergarten readiness testing: `https://www.thinkhappylivehealthy.com/kindergarten-readiness`
- Parent child services: `https://www.thinkhappylivehealthy.com/parent-child`

Landing pages still need review for every therapy and testing service before final CSV assembly. If a service does not have a dedicated page, the automation should use the closest parent page and mark `needs_human_review`.

## Quality Gates

Hard gates:

- 15 headlines.
- 4 descriptions.
- Headline max 30 characters.
- Description max 90 characters.
- Path 1 and Path 2 max 15 characters each.
- Final URL present.
- Path fields present.
- No broad match keyword generation.
- No unsupported claims.
- No copy implying knowledge of the user's mental health, diagnosis, identity, trauma, or other sensitive condition.

Relevance gates:

- At least 5 headlines must be ad-group-specific.
- At least 2 headlines must reflect the intent layer.
- At least 3 headlines can be account-shared.
- At least 1 description must mention the service.
- At least 1 description must mention access, location, or appointment path.
- The final URL must match the service.
- City ad groups must include a city in at least one headline or path.
- Local ad groups must include `near me`, `nearby`, or equivalent local-access language.
- State ad groups must include `Virginia`, `VA`, or approved state language.

Copy quality gates:

- Avoid generic filler like `comprehensive`, `world-class`, `innovative`, and `solutions`.
- Prefer specific service terms.
- Keep headlines distinct enough that Google has useful combinations.
- Do not repeat the same claim across many slots.
- Use plain English.

## Automation Path

1. Read the ad group taxonomy.
2. For each ad group, parse `service`, `audience_or_category`, and `intent_layer`.
3. Select the landing page.
4. Generate phrase keywords separately from copy.
5. Build a copy context object with:
   - service family
   - audience or category
   - intent layer
   - top keywords
   - geo layer
   - landing page
   - approved claims
   - banned claims
6. Generate 20 to 25 headline candidates.
7. Score and filter down to 15.
8. Generate 6 to 8 description candidates.
9. Score and filter down to 4.
10. Generate Path 1 and Path 2.
11. Run hard gates.
12. Run relevance gates.
13. Run policy gates.
14. Write approved RSA rows to the Editor CSV.
15. Write rejected assets and warnings to the human review file.

## Shared Versus Specific Rule

Use shared assets for consistency, but never let shared assets dominate the RSA.

Target mix:

- 60 percent ad-group-specific or service-specific.
- 25 percent account-shared.
- 15 percent geo or intent-layer.

This gives Google enough variation while keeping every ad relevant to the ad group.

## Human Review

The human review file should show for each ad group:

- Final URL.
- Path 1 and Path 2.
- 15 headlines with role labels and character counts.
- 4 descriptions with role labels and character counts.
- Which assets were shared.
- Which assets were service-specific.
- Which assets were generated from search term evidence.
- Any policy warnings.
- Any landing page mismatch warnings.

## Next Implementation Step

Create a generator script that reads `service_ad_group_taxonomy_2026-04-28.csv` and `rsa_copy_blueprint.json`, then produces:

- `rsa_copy_matrix_2026-04-28.csv`
- `rsa_copy_matrix_2026-04-28.json`
- `rsa_copy_review_2026-04-28.md`

After review, the campaign CSV builder can pull approved copy rows into the Google Ads Editor output.
