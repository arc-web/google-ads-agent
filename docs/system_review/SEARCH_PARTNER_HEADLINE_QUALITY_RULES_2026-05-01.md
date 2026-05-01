# Search Partner And Headline Quality Rules

Date: 2026-05-01

## Decision

Two rules are now active system rules:

1. Search partners are disabled 100 percent of the time.
2. RSA headlines under 25 characters fail quality review unless a human explicitly approves a rare exception.

These are enforced in the active staging validator and Search staging generator.

## Search Partner Rule

Active Search campaign rows must use:

- `Networks`: `Google search`

Any other network value fails validation. This includes:

- `Google search;Search Partners`
- `Search Partners`
- `Search`

Reason:

- the active rebuild workflow is Google Ads Editor staging-first
- the account-build system should not quietly expand distribution
- Search partners are not part of the current Search rebuild policy

## Headline Quality Rule

Active RSA headlines must be:

- 25 to 30 characters whenever possible
- concrete
- service-specific
- value-bearing
- clear enough to understand without surrounding context

Headlines now fail if they are short low-value labels such as:

- `Ashburn Care`
- `Anxiety Counseling`
- `Northern Virginia Care`
- `Appointments Available`

Those examples use too little of the 30-character space and do not carry enough value, specificity, action, proof, or next-step meaning.

## THLH REV1 Impact

The current THLH REV1 staging file now fails headline quality validation.

Audit outputs:

- [THLH headline quality failures](../../clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1_headline_quality_failures.csv)
- [THLH headline quality summary](../../clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1_headline_quality_summary.json)

Audit result:

- total failed headline placements: 443
- unique failed headlines: 63
- failure rule: `headline_minimum_value`

Most repeated failures:

- `Northern Virginia Care`
- `Anthem/CareFirst BCBS`
- `Ashburn Care`
- `Appointments Available`
- `Book Therapy Appointment`
- `Support That Fits Life`

## Required Repair Direction

Weak short labels should be rewritten into value-bearing headlines.

Examples:

- `Ashburn Care` should become a specific local service headline.
- `Anxiety Counseling` should become a clearer therapy or consult headline.
- `Appointments Available` should become a stronger scheduling or next-step headline.
- `Anthem/CareFirst BCBS` should become a clearer insurance-access headline if kept.

Repair constraints:

- stay at or under 30 characters
- use at least 25 characters whenever possible
- do not imply sensitive-condition knowledge
- do not activate PMAX
- do not activate API upload
- keep Search phrase-only
- keep Search partners off

## Sources

- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
- [Google Ads Editor CSV Columns](https://support.google.com/google-ads/editor/answer/57747)
- [Google Responsive Search Ads](https://support.google.com/google-ads/answer/7684791)
