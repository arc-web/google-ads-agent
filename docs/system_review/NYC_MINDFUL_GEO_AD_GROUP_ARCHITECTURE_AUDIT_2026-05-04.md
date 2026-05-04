# NYC Mindful Geo Ad Group Architecture Audit

Date: 2026-05-04

## Issue

The first NYC Mindful revision split the staging file into New York and New Jersey campaigns, but it did not rebuild ad group taxonomy. Generic ad group names were copied under both state campaigns, so the CSV did not clearly show general, near-me, state, and future city intent tiers.

## Root Cause

- The revision path renamed campaign rows after the initial build instead of regenerating campaign and ad group plans from geo strategy.
- Tests verified campaign names, negative exclusions, college-student intent, and validation status, but did not assert geo-specific ad group names.
- Group-service pause logic matched `group therapy` and `therapy group`, but missed generic `Group` labels such as `Therapy - Group - New York City`.

## Corrected Rule

- State splits must be planned before row generation.
- Each state campaign must include general, near-me, and state-specific ad groups.
- City ad groups are created only when approved target cities are explicit.
- City ad groups must include every approved city modifier for that city target.
- Paused services must be removed by service label, not only by exact keyword phrase.

## Validation Added

- Geo taxonomy unit tests cover state, near-me, and city ad group tiers.
- NYC revision tests now fail if group ad groups remain, if state ad groups are missing, or if only campaign names change.
- One-shot fixture tests now cover state targets and approved city targets.

## Reference

- Repo rule: `AGENTS.md`, city ad groups must include approved target city modifiers.
- Google Ads Editor staging remains a human review flow: https://support.google.com/google-ads/editor/answer/30564?hl=en
