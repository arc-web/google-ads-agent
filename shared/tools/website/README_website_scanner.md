# Website Scanner Tool

Generic scanner for new-campaign source artifacts. It fetches a website URL plus optional source pages, extracts titles, headings, links, and service candidates, then writes reviewable JSON into a client build folder.

## Usage

```bash
python3 shared/tools/website/website_scanner.py \
  --url https://example.com/ \
  --output-dir clients/agency/client/build/2026-05-04_initial_search_build \
  --source-page https://example.com/services/ \
  --service "Core Services"
```

## Outputs

- `website_scan.json`
- `source_attribution.json`
- `raw_website_crawl.json`

The scanner separates verified website facts, strategy inferences, and human-review-needed claims so shared tooling does not inject facts from another client.

## Notes

- The scanner uses the Python standard library and does not require browser automation.
- Service candidates are inferred from source-page URLs and headings unless explicit `--service` values are provided.
- Client approval is still required before launch.
