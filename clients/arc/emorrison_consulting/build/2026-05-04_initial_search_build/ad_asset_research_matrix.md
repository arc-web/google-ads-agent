# Search Asset Research Matrix

## sitelink

- Source: https://support.google.com/google-ads/answer/2375416?hl=en
- Limits: `{"description_line": 35, "link_text": 25, "minimum_to_show": 2, "preferred_count": 6}`
- Editor fields: `Campaign, Ad Group, Link text, Final URL, Description line 1, Description line 2`
- Generation rule: Use user-intent labels, never bare sitemap labels. Require distinct final URLs and both description lines.

## callout

- Source: https://support.google.com/google-ads/answer/6079510?hl=en
- Limits: `{"text": 25}`
- Editor fields: `Campaign, Ad Group, Callout text`
- Generation rule: Use confirmed value props that apply at the selected account branch.

## structured_snippet

- Source: https://support.google.com/google-ads/answer/6280012?hl=en
- Limits: `{"value": 25, "values_max": 10, "values_min": 3}`
- Editor fields: `Campaign, Structured snippet header, Structured snippet values`
- Generation rule: Use approved headers. Prefer Services and service-area lists when evidence supports them.

## call

- Source: https://support.google.com/google-ads/answer/2454052?hl=en
- Limits: `{"phone_number": "must match website or client evidence"}`
- Editor fields: `Campaign, Phone number, Country code`
- Generation rule: Generate only when website evidence has one confirmed phone number.

## price

- Source: https://support.google.com/google-ads/answer/7065415?hl=en
- Limits: `{"description": 25, "header": 25, "items_min": 3}`
- Editor fields: `Campaign, Price type, Price qualifier, Currency, Price header, Price amount, Final URL`
- Generation rule: Generate only from explicit website prices. Skip if fewer than 3 price points are visible.

## promotion

- Source: https://support.google.com/google-ads/answer/7367521?hl=en
- Limits: `{"promotion_target": 20}`
- Editor fields: `Campaign, Promotion target, Percent off, Money amount off, Promotion code, Final URL`
- Generation rule: Generate only when explicit promotion or sale evidence exists.

## image

- Source: https://support.google.com/google-ads/answer/9566341?hl=en
- Limits: `{"minimum_local_manifest_check": "300x300 with known file path"}`
- Editor fields: `manifest only until Editor import/export is verified`
- Generation rule: Copy only local image files with basic dimension evidence into the review import package.

## business_logo

- Source: https://support.google.com/adspolicy/answer/12499303?hl=en
- Limits: `{"minimum_local_manifest_check": "128x128 with logo evidence"}`
- Editor fields: `manifest only until Editor import/export is verified`
- Generation rule: Require website logo evidence and flag approval depends on advertiser verification.

## business_name

- Source: https://support.google.com/google-ads/answer/12497613?hl=en-GB
- Limits: `{"business_name": 25}`
- Editor fields: `Campaign, Business name`
- Generation rule: Generate when inferred name fits limits. Human review must confirm legal or domain match.

## location

- Source: https://support.google.com/google-ads/answer/2404182?hl=en
- Limits: `{"gbp_link_required": true}`
- Editor fields: `review task only`
- Generation rule: Do not fake location assets. Create GBP linking review task when not confirmed.
