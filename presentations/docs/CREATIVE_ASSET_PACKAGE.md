# Creative Asset Approval Package

Use this workflow to prepare Google Ads image and YouTube video assets for client approval before any creative is used in Search image assets, responsive display ads, logo assets, Performance Max, Demand Gen, or YouTube campaigns.

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
  --youtube-channel-url "https://www.youtube.com/@clientchannel" \
  --youtube-video-url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --campaign-intent pmax \
  --google-ads-evidence path/to/youtube_link_evidence.json \
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
- `youtube_video_manifest.json`
- `youtube_video_review.csv`
- `youtube_account_discovery.json`
- `youtube_account_review.csv`
- `youtube_account_discovery.md`
- `youtube_sync_checklist.md`
- `source_images/`
- `processed_images/`

All generated or processed variants start as `needs client approval`. YouTube videos also start as `needs client approval`, `needs Google Ads and YouTube link confirmation`, and `needs client rights confirmation`. The package validation fails if an asset is marked campaign-ready before approval.

## Source Rules

The scanner uses the shared website scanner at `shared/tools/website/website_scanner.py`. It collects image evidence from image tags, `srcset`, icons, meta images, and JSON-LD image fields when available.

The downloader only brings local likely first-party assets into the repo. Same-domain assets, subdomains, shared registered-root hosts, and operator-supplied `--first-party-cdn-domain` hosts are allowed. Other hosts are rejected for review rather than downloaded.

## YouTube Account And Video Rules

The tool inventories YouTube channels and videos from operator-supplied URLs, website links, embeds, JSON-LD fields, optional Google Ads evidence files, and optional public YouTube search. It records the canonical 11-character YouTube video ID for Google Ads video asset use.

V1 does not connect accounts or mutate YouTube Studio or Google Ads. Use `youtube_sync_checklist.md` to confirm:

- Google Ads account admin access.
- YouTube channel or video link approval.
- Client rights to use the video in ads.
- Final sync status before any campaign use.

Use `--campaign-intent pmax`, `--campaign-intent demand_gen`, `--campaign-intent youtube_video`, or `--require-video-assets` when the package is preparing video-required work. If video is required and no campaign-ready video is confirmed, `validation_report.json` returns `blocked_pending_client_video` and `client_email_draft.md` asks the client for the official YouTube channel URL, approver, linking permission, rights confirmation, and priority videos.

Public YouTube search is opt-in with `--enable-public-youtube-search`. Public search candidates are treated as `needs_confirmation`; they do not prove ownership and cannot become campaign-ready without client approval, rights confirmation, and Google Ads link confirmation.

## Google References

- [Responsive display ad best practices](https://support.google.com/google-ads/answer/9823397)
- [Image assets for Search campaigns](https://support.google.com/google-ads/answer/9566341)
- [Image asset policy requirements](https://support.google.com/adspolicy/answer/10347108)
- [Google Ads ad specs](https://support.google.com/google-ads/answer/13676244)
- [Performance Max image and logo requirements](https://developers.google.com/google-ads/api/performance-max/asset-requirements)

- [Link YouTube channels or videos and Google Ads accounts](https://support.google.com/google-ads/answer/3063482)
- [Google Ads API YouTube linking](https://developers.google.com/google-ads/api/docs/account-management/linking-youtube)
- [Google Ads API YoutubeVideoAsset](https://developers.google.com/google-ads/api/reference/rpc/v20/YoutubeVideoAsset)
- [Google Ads API assets overview](https://developers.google.com/google-ads/api/docs/assets/overview)
