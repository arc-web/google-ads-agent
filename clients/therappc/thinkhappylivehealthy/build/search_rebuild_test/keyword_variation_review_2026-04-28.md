# Keyword Variation Review

Date: 2026-04-28

Source: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/reports/performance_inputs/search_terms_report_min_10_impressions_2026-04-28.csv`
Analysis CSV: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/search_term_variation_analysis_2026-04-28.csv`
Expansion CSV: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/phrase_keyword_expansion_candidates_2026-04-28.csv`

## Summary

- Search terms analyzed: `789`
- Phrase keyword expansion candidates: `22`

## Action Counts

- `variation_candidate`: `718`
- `review_negative`: `26`
- `review_spend_no_conversion`: `23`
- `add_phrase`: `17`
- `review_low_ctr`: `5`

## Service Counts

- `Human Review`: `390`
- `Therapy - Anxiety`: `158`
- `Psychiatry - Adult`: `65`
- `Therapy - Depression`: `64`
- `Testing - Child Psychological`: `38`
- `Therapy - ADHD`: `31`
- `Psychiatry - Children`: `23`
- `Testing - ADHD`: `16`
- `Therapy - Children`: `4`

## Top Converting Terms

- `anxiety doctors near me` -> `Therapy - Anxiety - Local`, 4.0 conversions, 35.0 impressions, action `add_phrase`
- `child and adolescent psychiatry` -> `Psychiatry - Children - General`, 3.0 conversions, 422.0 impressions, action `add_phrase`
- `adhd therapist near me` -> `Therapy - ADHD - Local`, 2.0 conversions, 275.0 impressions, action `add_phrase`
- `adhd therapist` -> `Therapy - ADHD - General`, 2.0 conversions, 84.0 impressions, action `add_phrase`
- `esketamine` -> `Therapy - Depression - General`, 2.0 conversions, 59.0 impressions, action `add_phrase`
- `child behavioral therapist` -> `Therapy - Children - General`, 2.0 conversions, 33.0 impressions, action `add_phrase`
- `add treatment for adults` -> `Therapy - ADHD - General`, 2.0 conversions, 20.0 impressions, action `add_phrase`
- `aislynn collier` -> `Human Review`, 2.0 conversions, 219.0 impressions, action `review_negative`
- `uva child psychology` -> `Testing - Child Psychological - General`, 2.0 conversions, 21.0 impressions, action `review_negative`
- `child psychiatry` -> `Psychiatry - Children - General`, 1.0 conversions, 177.0 impressions, action `add_phrase`
- `child psychiatry near me` -> `Psychiatry - Children - Local`, 1.0 conversions, 103.0 impressions, action `add_phrase`
- `psychological evaluation for child` -> `Testing - Child Psychological - General`, 1.0 conversions, 98.0 impressions, action `add_phrase`
- `psych np near me` -> `Psychiatry - Adult - Local`, 1.0 conversions, 77.0 impressions, action `add_phrase`
- `physiatrists near me` -> `Human Review`, 1.0 conversions, 60.0 impressions, action `add_phrase`
- `overcoming anxiety` -> `Therapy - Anxiety - General`, 1.0 conversions, 53.0 impressions, action `add_phrase`

## Top High-Impression Terms

- `panic attack treatment` -> `Therapy - Anxiety - General`, 586.0 impressions, 39.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `spravato treatment` -> `Human Review`, 470.0 impressions, 5.0 clicks, 0.0 conversions, action `variation_candidate`
- `chkd mental health` -> `Human Review`, 468.0 impressions, 15.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `psychiatry near me` -> `Psychiatry - Adult - Local`, 466.0 impressions, 22.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `adhd coach` -> `Human Review`, 461.0 impressions, 36.0 clicks, 0.5 conversions, action `review_negative`
- `psychotherapy` -> `Human Review`, 442.0 impressions, 6.0 clicks, 0.0 conversions, action `variation_candidate`
- `spravato` -> `Human Review`, 430.0 impressions, 2.0 clicks, 0.0 conversions, action `variation_candidate`
- `child and adolescent psychiatry` -> `Psychiatry - Children - General`, 422.0 impressions, 6.0 clicks, 3.0 conversions, action `add_phrase`
- `adhd treatment` -> `Therapy - ADHD - General`, 408.0 impressions, 36.0 clicks, 0.5 conversions, action `add_phrase`
- `adhd treatments` -> `Therapy - ADHD - General`, 344.0 impressions, 46.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `mental health clinic near me` -> `Human Review`, 317.0 impressions, 19.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `adhd coach near me` -> `Human Review`, 312.0 impressions, 30.0 clicks, 1.0 conversions, action `review_negative`
- `children's national psychiatry` -> `Psychiatry - Adult - General`, 287.0 impressions, 13.0 clicks, 0.0 conversions, action `review_spend_no_conversion`
- `adhd therapist near me` -> `Therapy - ADHD - Local`, 275.0 impressions, 22.0 clicks, 2.0 conversions, action `add_phrase`
- `adhd treatment for adults` -> `Therapy - ADHD - General`, 274.0 impressions, 35.0 clicks, 0.0 conversions, action `review_spend_no_conversion`

## Interpretation

- Templates are necessary for coverage, but search-term variation should decide which terms graduate into extra phrase keywords.
- High-impression, no-click terms should not automatically become keywords. They should either inform RSA wording, become negatives, or stay in review.
- Singular and plural variants should be generated only when the root term is directly relevant to the service and landing page.
- Provider names, institutions, competitors, coaching terms, and out-of-market cities should be review or negative candidates.
