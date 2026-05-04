# Creative Asset Approval Package

Use this workflow to prepare Google Ads image assets for client approval before any creative is used in Search image assets, responsive display ads, or logo assets.

## Command

```bash
python3 presentations/tools/build_creative_asset_package.py \
  --agency agency_slug \
  --client client_slug \
  --display-name "Client Name" \
  --website "https://www.example.com" \
  --service-theme "Service Theme" \
  --landing-page "https://www.example.com/service-page" \
  --brand-rules "Short brand notes or approved tone" \
  --client-dir clients/agency_slug/client_slug \
  --max-candidates 24 \
  --first-party-cdn-domain "cdn.example.com"
```

The tool writes a self-contained approval package under `clients/{agency}/{client}/media/{run_name}/`. Source images live in `source_images/`, processed images live in `processed_images/`, and the approval HTML, CSV, manifest, email draft, validation, and attribution files live in the same run folder.

## Outputs

- `creative_asset_manifest.json`
- `creative_asset_review.csv`
- `Client_Creative_Approval.html`
- `client_email_draft.md`
- `validation_report.json`
- `creative_source_attribution.json`
- `source_images/`
- `processed_images/`

All generated or processed variants start as `needs client approval`. The package validation fails if an asset is marked campaign-ready before approval.

## Source Rules

The scanner uses the shared website scanner at `shared/tools/website/website_scanner.py`. It collects image evidence from image tags, `srcset`, icons, meta images, and JSON-LD image fields when available.

The downloader only brings local likely first-party assets into the repo. Same-domain assets, subdomains, shared registered-root hosts, and operator-supplied `--first-party-cdn-domain` hosts are allowed. Other hosts are rejected for review rather than downloaded.

## Google References

- [Responsive display ad best practices](https://support.google.com/google-ads/answer/9823397)
- [Image assets for Search campaigns](https://support.google.com/google-ads/answer/9566341)
- [Image asset policy requirements](https://support.google.com/adspolicy/answer/10347108)
- [Google Ads ad specs](https://support.google.com/google-ads/answer/13676244)
- [Performance Max image and logo requirements](https://developers.google.com/google-ads/api/performance-max/asset-requirements)
