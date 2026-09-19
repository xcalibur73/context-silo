"""
ContextSilo CLI: Semantic Anchor Text & Vector Contiguity Auditor.
"""

import argparse
import json
import sys

from context_silo.extractor import crawl_site_cluster
from context_silo.vector_analyzer import analyze_anchor_network
from context_silo.scorer import score_anchor_network
from context_silo.report_generator import (
    print_terminal_report,
    export_markdown_report,
    export_json_report,
)


def run_audit(url: str, max_pages: int = 10) -> dict:
    """Execute complete semantic anchor text and vector contiguity audit pipeline."""
    cluster_data = crawl_site_cluster(url, max_pages=max_pages)
    network_analysis = analyze_anchor_network(cluster_data)
    scores = score_anchor_network(network_analysis)

    return {
        "url": cluster_data["start_url"],
        "base_domain": cluster_data["base_domain"],
        "overall_score": scores["overall_score"],
        "grade": scores["grade"],
        "component_scores": scores["component_scores"],
        "recommendations": scores["recommendations"],
        "network_analysis": network_analysis,
    }


def main():
    from context_silo import __version__
    parser = argparse.ArgumentParser(
        prog="context-silo",
        description="ContextSilo: The Semantic Anchor Text & Vector Contiguity Auditor",
        epilog="Example: python run.py https://webaudits.pro --max-pages 12",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Target URL or domain to audit for semantic anchor text and vector contiguity.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ContextSilo v{__version__}",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum pages to crawl for link context passages (default: 10).",
    )
    parser.add_argument(
        "--output",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Output format (default: terminal).",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save report to file path.",
    )

    args = parser.parse_args()
    if not args.url:
        parser.print_help()
        return 0

    target_url = args.url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    print(f"ContextSilo: Auditing semantic anchor passages and vector contiguity on {target_url}...")

    try:
        audit_result = run_audit(url=target_url, max_pages=args.max_pages)
    except Exception as e:
        print(f"Error during ContextSilo audit: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output == "terminal":
        print_terminal_report(audit_result)
    elif args.output == "markdown":
        md = export_markdown_report(audit_result)
        print(md)
    elif args.output == "json":
        js = export_json_report(audit_result)
        print(js)

    if args.save:
        save_path = args.save
        if save_path.endswith(".json"):
            content = export_json_report(audit_result)
        elif save_path.endswith(".md"):
            content = export_markdown_report(audit_result)
        else:
            content = export_json_report(audit_result)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nReport saved to: {save_path}")


if __name__ == "__main__":
    main()
