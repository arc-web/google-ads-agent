# Campaign Type Guide

## Active Workflow

Search campaigns are the only active default in this phase.

Reason:

- the repo currently stages changes through Google Ads Editor files
- Search rebuilds are phrase-only by default
- generated output must pass `shared/rebuild/staging_validator.py`
- PMAX, API upload, and other campaign types need separate activation plans

## Active Search Rules

- Use Search campaigns for current rebuild output.
- Use phrase keywords through `Criterion Type: Phrase`.
- Keep `Broad match keywords` off.
- Do not use Broad.
- Do not use Exact unless a later controlled test explicitly activates it.
- Generate 15 RSA headlines and 4 descriptions when possible.
- Write UTF-16 tab-separated staging files.
- Keep generated campaigns paused for review.

## Reference-Only Campaign Types

The following campaign types are preserved as reference only:

- Performance Max
- Display
- Shopping
- Video
- App
- Discovery
- Local Services

They should not be selected by shared config defaults.

## Activation Rule

To activate a non-Search campaign type, create a separate cleanup and activation loop with:

- active contract
- config updates
- generator or exporter updates
- synthetic tests
- real artifact validation where relevant
- process docs update
- user approval for live account mutation if API upload is involved
