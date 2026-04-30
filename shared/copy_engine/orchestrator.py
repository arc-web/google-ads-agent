"""
Copy engine pipeline orchestrator for the google_ads_agent.

Two modes:
  sweep    - parse an existing Google Ads Editor CSV, grade + evaluate all
             current copy, generate a HITL report, then stop.
  generate - run all generators (headlines, descriptions, extensions),
             grade + evaluate the new copy, generate a comparison report.
             CSV export is not yet wired (placeholder only).

Usage:
  python -m copy_engine.orchestrator --mode sweep   --csv /path/to/export.tsv --client thinkhappylivehealthy
  python -m copy_engine.orchestrator --mode generate --client thinkhappylivehealthy --client-dir /path/to/client
"""

from __future__ import annotations

import codecs
import csv
import os
import sys
from typing import Optional

import yaml

from copy_engine.context import AdGroupContext, ClientContext
from copy_engine.editor.evaluator import CopyEvaluator
from copy_engine.editor.grader import CopyGrader
from copy_engine.editor.reporter import HITLReporter
from copy_engine.models import OpenRouterClient
from copy_engine.search.descriptions import DescriptionGenerator
from copy_engine.search.extensions import ExtensionGenerator
from copy_engine.search.headlines import HeadlineGenerator


# ---------------------------------------------------------------------------
# CSV column names for Google Ads Editor TSV exports
# ---------------------------------------------------------------------------

_COL_CAMPAIGN        = "Campaign"
_COL_CAMPAIGN_STATUS = "Campaign Status"
_COL_AD_GROUP        = "Ad Group"
_COL_AG_STATUS       = "Ad Group Status"
_COL_FINAL_URL       = "Final URL"
_HEADLINE_COLS       = [f"Headline {i}" for i in range(1, 16)]
_DESCRIPTION_COLS    = [f"Description {i}" for i in range(1, 5)]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class CopyEngineOrchestrator:
    """
    Wires all copy engine components into a two-mode pipeline.

    Attributes:
        agency:     Agency slug (e.g. "therappc").
        client:     Client slug (e.g. "thinkhappylivehealthy").
        client_dir: Path to client directory - used to find YAML config and
                    to store reports.
        base_path:  Root of the google_ads_agent repo.  Reports land under
                    <base_path>/clients/<agency>/<client>/reports/.
    """

    def __init__(
        self,
        agency: str,
        client: str,
        client_dir: Optional[str] = None,
        base_path: str = "/Users/home/ai/agents/ppc/google_ads_agent",
    ) -> None:
        self.agency     = agency
        self.client     = client
        self.client_dir = client_dir or os.path.join(base_path, "clients", agency, client)
        self.base_path  = base_path

        # Shared LLM client - instantiated once; all generators reuse it.
        self._llm       = OpenRouterClient()
        self._grader    = CopyGrader(self._llm)
        self._evaluator = CopyEvaluator()
        self._reporter  = HITLReporter(base_path=base_path)

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_sweep(self, csv_path: str) -> str:
        """
        Sweep mode: audit existing copy from a Google Ads Editor CSV export.

        Steps:
          1. Load client context (YAML or minimal from CSV data).
          2. Parse the CSV.
          3. Extract current copy per ad group.
          4. Grade every headline and description.
          5. Evaluate every ad group.
          6. Generate HITL report.

        Returns:
            Absolute path to the generated HTML report.
        """
        print(f"[sweep] Parsing CSV: {csv_path}")
        rows = self._read_csv(csv_path)

        current_copy = self._extract_current_copy(rows)
        if not current_copy:
            print("[sweep] No enabled ad groups found in CSV. Exiting.")
            sys.exit(1)

        print(f"[sweep] Found {len(current_copy)} enabled ad group(s).")

        client_ctx = self._load_client_context(current_copy)

        print("[sweep] Grading current copy ...")
        grade_reports = self._grade_all(current_copy, client_ctx)

        print("[sweep] Evaluating current copy ...")
        eval_reports = self._evaluate_all(current_copy, client_ctx)

        # Build plan describes what *would* be generated (shown in Section D).
        build_plan = self._make_build_plan(current_copy)

        print("[sweep] Generating HITL report ...")
        report_path = self._reporter.generate(
            client_ctx=client_ctx,
            grade_reports=grade_reports,
            eval_reports=eval_reports,
            current_copy=current_copy,
            proposed_copy={},
            build_plan=build_plan,
        )

        print(f"\n[sweep] Report written to:\n  {report_path}")
        print("  Open it in a browser to review, then run --mode generate to proceed.\n")
        return report_path

    def run_generate(self) -> str:
        """
        Generate mode: produce new headlines, descriptions, and extensions,
        then grade + evaluate them and write a comparison report.

        Requires a client YAML config at <client_dir>/client_config.yaml or
        <client_dir>/<client>_client_config.yaml.

        Returns:
            Absolute path to the generated HTML comparison report.
        """
        client_ctx = self._load_client_context_from_yaml()

        print(f"[generate] Client: {client_ctx.client} | {len(client_ctx.services)} service(s)")

        # Build a minimal AdGroupContext per service so generators have
        # everything they need.  In real use the YAML would supply ad groups;
        # this creates one ad group per top-level service as a sensible default.
        ad_groups = self._build_ad_group_contexts(client_ctx)
        print(f"[generate] {len(ad_groups)} ad group(s) to generate.")

        hl_gen   = HeadlineGenerator(self._llm)
        desc_gen = DescriptionGenerator(self._llm)
        ext_gen  = ExtensionGenerator(self._llm)

        generated_copy: dict[str, dict] = {}

        for ag_ctx in ad_groups:
            print(f"[generate]   Ad group: {ag_ctx.name}")
            headlines = hl_gen.generate(ag_ctx)
            descs     = desc_gen.generate(ag_ctx)

            generated_copy[ag_ctx.name] = {
                "headlines":    [h.text for h in headlines],
                "descriptions": [d.text for d in descs],
            }

        # Extensions are per client, not per ad group.
        print("[generate] Generating extensions ...")
        extensions = ext_gen.generate(client_ctx)
        # Attach extensions to a synthetic "Extensions" key in generated_copy
        # so the reporter renders them in Section C.
        generated_copy["[Extensions]"] = {
            "sitelinks": [
                f"{sl.link_text} | {sl.description_1} | {sl.description_2}"
                for sl in extensions.sitelinks
            ],
            "callouts": [co.text for co in extensions.callouts],
            "snippets": [
                f"{sn.header}: {', '.join(sn.values)}"
                for sn in extensions.snippets
            ],
        }

        print("[generate] Grading generated copy ...")
        grade_reports = self._grade_all(generated_copy, client_ctx)

        print("[generate] Evaluating generated copy ...")
        eval_reports = self._evaluate_all(generated_copy, client_ctx)

        build_plan = self._make_build_plan(generated_copy)

        print("[generate] Writing comparison report ...")
        report_path = self._reporter.generate(
            client_ctx=client_ctx,
            grade_reports=grade_reports,
            eval_reports=eval_reports,
            current_copy={},
            proposed_copy=generated_copy,
            build_plan=build_plan,
        )

        print(f"\n[generate] Report written to:\n  {report_path}")
        print("  TODO: wire google_ads_editor_exporter\n")
        return report_path

    # ------------------------------------------------------------------
    # CSV parsing
    # ------------------------------------------------------------------

    def _read_csv(self, csv_path: str) -> list[dict]:
        """
        Read a Google Ads Editor TSV export (UTF-16, tab-delimited).
        Falls back to UTF-8 if UTF-16 decoding fails.

        Returns a list of row dicts.
        """
        # Google Ads Editor typically exports UTF-16 LE with BOM.
        for encoding in ("utf-16", "utf-8-sig", "utf-8"):
            try:
                rows: list[dict] = []
                with codecs.open(csv_path, encoding=encoding, errors="strict") as fh:
                    reader = csv.DictReader(fh, delimiter="\t")
                    for row in reader:
                        rows.append(row)
                print(f"[csv] Parsed {len(rows)} row(s) using {encoding}.")
                return rows
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as exc:
                print(f"[csv] Failed to read with {encoding}: {exc}")
                continue
        raise RuntimeError(f"Could not parse CSV at {csv_path} with UTF-16, UTF-8-sig, or UTF-8.")

    def _extract_current_copy(self, rows: list[dict]) -> dict[str, dict]:
        """
        Pull headlines, descriptions, campaign, and URL from each enabled row.

        Returns:
            {ad_group_name: {headlines: [str], descriptions: [str],
                             campaign: str, url: str}}
        """
        copy: dict[str, dict] = {}

        for row in rows:
            # Skip paused/removed campaigns
            camp_status = (row.get(_COL_CAMPAIGN_STATUS) or "").strip().lower()
            if camp_status and camp_status != "enabled":
                continue

            # Skip paused/removed ad groups
            ag_status = (row.get(_COL_AG_STATUS) or "").strip().lower()
            if ag_status and ag_status != "enabled":
                continue

            ad_group = (row.get(_COL_AD_GROUP) or "").strip()
            if not ad_group:
                continue

            campaign = (row.get(_COL_CAMPAIGN) or "").strip()
            url      = (row.get(_COL_FINAL_URL) or "").strip()

            headlines = [
                row[col].strip()
                for col in _HEADLINE_COLS
                if col in row and row[col].strip()
            ]
            descriptions = [
                row[col].strip()
                for col in _DESCRIPTION_COLS
                if col in row and row[col].strip()
            ]

            if ad_group not in copy:
                copy[ad_group] = {
                    "headlines":    [],
                    "descriptions": [],
                    "campaign":     campaign,
                    "url":          url,
                }

            # Merge rows that belong to the same ad group (split rows)
            for h in headlines:
                if h not in copy[ad_group]["headlines"]:
                    copy[ad_group]["headlines"].append(h)
            for d in descriptions:
                if d not in copy[ad_group]["descriptions"]:
                    copy[ad_group]["descriptions"].append(d)
            if not copy[ad_group]["url"] and url:
                copy[ad_group]["url"] = url

        return copy

    # ------------------------------------------------------------------
    # Client context loading
    # ------------------------------------------------------------------

    def _load_client_context(
        self,
        current_copy: dict[str, dict],
    ) -> ClientContext:
        """
        Try to load a YAML client config.  If not found, build a minimal
        ClientContext from the data scraped from the CSV.
        """
        yaml_ctx = self._try_load_yaml()
        if yaml_ctx:
            return yaml_ctx

        print("[context] No YAML config found - building minimal context from CSV data.")
        return self._minimal_context_from_csv(current_copy)

    def _load_client_context_from_yaml(self) -> ClientContext:
        """Load context strictly from YAML; raise if not found."""
        yaml_ctx = self._try_load_yaml()
        if yaml_ctx:
            return yaml_ctx
        raise FileNotFoundError(
            f"No client YAML config found in {self.client_dir}. "
            "Create client_config.yaml or <client>_client_config.yaml before running generate."
        )

    def _try_load_yaml(self) -> Optional[ClientContext]:
        """Return a ClientContext from YAML if a config file is found, else None."""
        candidates = [
            os.path.join(self.client_dir, f"{self.client}_client_config.yaml"),
            os.path.join(self.client_dir, "client_config.yaml"),
        ]
        for path in candidates:
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                if not isinstance(data, dict):
                    continue
                ctx = ClientContext(
                    agency=data.get("agency", self.agency),
                    client=data.get("client", self.client),
                    practice_name=data.get("practice_name", ""),
                    services=data.get("services", []),
                    geo=data.get("geo", []),
                    USPs=data.get("USPs", data.get("usps", [])),
                    insurance_accepted=data.get("insurance_accepted", []),
                    practice_type=data.get("practice_type", ""),
                    website_url=data.get("website_url", ""),
                )
                print(f"[context] Loaded YAML config from {path}")
                return ctx
            except Exception as exc:
                print(f"[context] Failed to parse {path}: {exc}")
        return None

    def _minimal_context_from_csv(self, current_copy: dict[str, dict]) -> ClientContext:
        """Build a bare-minimum ClientContext from CSV-extracted data."""
        # Derive geo hints from ad group names (e.g. "ADHD Testing - Ashburn VA")
        geos: list[str] = []
        services: list[str] = []
        url = ""

        for ag_name, data in current_copy.items():
            if not url:
                url = data.get("url", "")
            parts = [p.strip() for p in ag_name.split("-")]
            if len(parts) == 1:
                services.append(parts[0])
            else:
                services.append(parts[0])
                geos.append(parts[-1])

        return ClientContext(
            agency=self.agency,
            client=self.client,
            practice_name=self.client.replace("_", " ").title(),
            services=list(dict.fromkeys(services)),  # deduplicated, order preserved
            geo=list(dict.fromkeys(geos)),
            USPs=[],
            insurance_accepted=[],
            practice_type="",
            website_url=url,
        )

    # ------------------------------------------------------------------
    # Grading and evaluation
    # ------------------------------------------------------------------

    def _grade_all(
        self,
        copy_data: dict[str, dict],
        client_ctx: ClientContext,
    ) -> dict[str, dict]:
        """
        Run CopyGrader.grade_ad_group for every ad group.

        Returns:
            {ad_group_name: {headlines: [GradeReport], descriptions: [GradeReport], summary: dict}}
        """
        grade_reports: dict[str, dict] = {}

        for ag_name, data in copy_data.items():
            headlines    = data.get("headlines", [])
            descriptions = data.get("descriptions", [])

            # Skip extension buckets added by generate mode
            if ag_name == "[Extensions]":
                continue

            if not headlines and not descriptions:
                continue

            context_hint = (
                f"{client_ctx.practice_name} - {ag_name} - "
                f"{client_ctx.practice_type or 'general'} "
                f"in {', '.join(client_ctx.geo) or 'unspecified location'}"
            )

            grade_reports[ag_name] = self._grader.grade_ad_group(
                headlines=headlines,
                descriptions=descriptions,
                context=context_hint,
            )

        return grade_reports

    def _evaluate_all(
        self,
        copy_data: dict[str, dict],
        client_ctx: ClientContext,
    ) -> dict[str, object]:
        """
        Run CopyEvaluator.evaluate_ad_group for every ad group.

        Returns:
            {ad_group_name: EvalReport}
        """
        eval_reports = {}

        for ag_name, data in copy_data.items():
            if ag_name == "[Extensions]":
                continue

            headlines    = data.get("headlines", [])
            descriptions = data.get("descriptions", [])

            if not headlines and not descriptions:
                continue

            # Build a minimal AdGroupContext so the evaluator can check
            # keyword-in-description coverage.
            ag_ctx = AdGroupContext(
                name=ag_name,
                service=ag_name,
                geo=client_ctx.geo,
                USPs=client_ctx.USPs,
                top_keywords=[],   # not available from CSV data alone
                landing_url=data.get("url", client_ctx.website_url),
                industry=client_ctx.practice_type or "general",
                insurance_accepted=client_ctx.insurance_accepted,
                practice_name=client_ctx.practice_name,
            )

            eval_reports[ag_name] = self._evaluator.evaluate_ad_group(
                headlines=headlines,
                descriptions=descriptions,
                ctx=ag_ctx,
            )

        return eval_reports

    # ------------------------------------------------------------------
    # Build plan
    # ------------------------------------------------------------------

    def _make_build_plan(self, copy_data: dict[str, dict]) -> dict[str, dict]:
        """
        Generate a build plan dict for the reporter's Section D checklist.

        For sweep mode: plan reflects what *would* be generated (12 headlines,
        4 descriptions per ad group, plus client-level extensions).
        For generate mode: plan reflects what was actually generated.
        """
        plan: dict[str, dict] = {}
        first_ag = True

        for ag_name, data in copy_data.items():
            if ag_name == "[Extensions]":
                continue
            hl_count   = len(data.get("headlines", [])) or 12
            desc_count = len(data.get("descriptions", [])) or 4

            plan[ag_name] = {
                "headlines":    hl_count,
                "descriptions": desc_count,
                "sitelinks":    8 if first_ag else 0,  # client-level, shown once
                "callouts":     10 if first_ag else 0,
            }
            first_ag = False

        return plan

    # ------------------------------------------------------------------
    # Ad group context helpers (generate mode)
    # ------------------------------------------------------------------

    def _build_ad_group_contexts(
        self, client_ctx: ClientContext
    ) -> list[AdGroupContext]:
        """
        Build one AdGroupContext per service listed in the ClientContext.
        A real YAML config can supply ad_groups[] directly; this is the
        fallback when it does not.
        """
        return [
            AdGroupContext(
                name=service,
                service=service,
                geo=client_ctx.geo,
                USPs=client_ctx.USPs,
                top_keywords=[service],   # callers should supply real keywords
                landing_url=client_ctx.website_url,
                industry=client_ctx.practice_type or "general",
                insurance_accepted=client_ctx.insurance_accepted,
                practice_name=client_ctx.practice_name,
            )
            for service in client_ctx.services
        ]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Copy engine pipeline orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sweep - audit THHL's existing CSV
  python -m copy_engine.orchestrator \\
      --mode sweep \\
      --csv /Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/exports/ads.tsv \\
      --client thinkhappylivehealthy

  # Generate - produce new copy (requires client_config.yaml)
  python -m copy_engine.orchestrator \\
      --mode generate \\
      --client thinkhappylivehealthy \\
      --client-dir /Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy
""",
    )

    parser.add_argument(
        "--mode",
        choices=["sweep", "generate"],
        required=True,
        help="sweep = audit existing CSV; generate = produce new copy",
    )
    parser.add_argument(
        "--csv",
        help="Path to Google Ads Editor export (UTF-16 TSV). Required for --mode sweep.",
    )
    parser.add_argument(
        "--client-dir",
        dest="client_dir",
        help="Path to client directory (for YAML config + report output).",
    )
    parser.add_argument(
        "--agency",
        default="therappc",
        help="Agency slug (default: therappc)",
    )
    parser.add_argument(
        "--client",
        required=True,
        help="Client slug (e.g. thinkhappylivehealthy)",
    )

    args = parser.parse_args()

    orchestrator = CopyEngineOrchestrator(
        agency=args.agency,
        client=args.client,
        client_dir=args.client_dir,
    )

    if args.mode == "sweep":
        if not args.csv:
            parser.error("--csv is required when --mode sweep")
        report = orchestrator.run_sweep(args.csv)

    elif args.mode == "generate":
        report = orchestrator.run_generate()

    print(f"Done. Report: {report}")
