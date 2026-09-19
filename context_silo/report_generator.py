"""
Report generator for ContextSilo Semantic Anchor Text & Vector Contiguity Audits.
Outputs Rich terminal tables, Markdown documents, and JSON objects.
"""

import json
from typing import Dict, Any, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def _safe_str(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text or "")
    text = (
        text.replace("\u2192", "->")
        .replace("\u2190", "<-")
        .replace("\u2194", "<->")
        .replace("\u2022", "*")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return text.encode("ascii", errors="replace").decode("ascii")


def print_terminal_report(audit_result: Dict[str, Any]) -> None:
    """Print complete anchor network report to terminal."""
    if not HAS_RICH:
        _print_plain_report(audit_result)
        return

    console = Console()

    url = _safe_str(audit_result.get("url", ""))
    score = audit_result.get("overall_score", 0.0)
    grade = audit_result.get("grade", "F")
    network = audit_result.get("network_analysis", {})
    comp = audit_result.get("component_scores", {})

    score_color = "green" if score >= 80 else ("yellow" if score >= 60 else "red")

    header = Text()
    header.append("ContextSilo: Semantic Anchor Text & Vector Contiguity Auditor\n", style="bold green")
    header.append(f"Target Origin: {url}\n", style="bold white")
    header.append(f"Silo Contiguity Score: {score}/100 (Grade: {grade})\n", style=f"bold {score_color}")
    header.append(
        f"Links Analyzed: {network.get('total_links_analyzed')} | "
        f"Generic Anchors: {network.get('generic_anchor_count')} ({network.get('generic_anchor_ratio_percent')}%) | "
        f"Avg Vector Contiguity: {network.get('average_vector_contiguity_percent')}% | "
        f"Cannibalization Collisions: {network.get('cannibalization_collisions_count')}",
        style="dim",
    )

    console.print(Panel(header, border_style="green"))

    # Component Scores Table
    comp_table = Table(title="Contiguity & Anchor Quality Breakdown", show_header=True, header_style="bold green")
    comp_table.add_column("Audit Dimension", style="white")
    comp_table.add_column("Weight", justify="center", style="dim")
    comp_table.add_column("Score", justify="right", style="bold green")

    weights = {
        "semantic_contiguity": "35%",
        "generic_anchor_prevention": "30%",
        "cannibalization_prevention": "20%",
        "anchor_diversity": "15%",
    }
    labels = {
        "semantic_contiguity": "Semantic Passage Vector Contiguity",
        "generic_anchor_prevention": "Generic Anchor Prevention ('click here', 'read more')",
        "cannibalization_prevention": "Anchor Collision & Cannibalization Prevention",
        "anchor_diversity": "Anchor Text Diversity Balance",
    }
    for k, v in comp.items():
        comp_table.add_row(labels.get(k, k), weights.get(k, "15%"), f"{v}/100")
    console.print(comp_table)

    # Anchor Classification Distribution Table
    dist = network.get("anchor_type_distribution", {})
    dist_table = Table(title="Anchor Classification Distribution", show_header=True, header_style="bold cyan")
    dist_table.add_column("Anchor Type", style="white")
    dist_table.add_column("Count", justify="center", style="bold cyan")
    dist_table.add_column("Share", justify="right", style="dim")

    total = network.get("total_links_analyzed", 0)
    for a_type, count in dist.items():
        share = f"{round((count / total) * 100, 1)}%" if total else "0%"
        dist_table.add_row(a_type.replace("_", " ").title(), str(count), share)
    console.print(dist_table)

    # Generic Anchors and Smart Replacement Table
    generics = network.get("generic_links", [])
    if generics:
        gen_table = Table(title=f"Detected Generic Anchors ({len(generics)} sample)", show_header=True, header_style="bold red")
        gen_table.add_column("Current Anchor", style="red")
        gen_table.add_column("Target URL", style="dim", max_width=40)
        gen_table.add_column("Recommended Entity Replacement", style="bold green")

        for g in generics[:6]:
            gen_table.add_row(
                _safe_str(g.get("anchor_text", "")),
                _safe_str(g.get("target_url", "")),
                _safe_str(g.get("suggested_replacement", "related guide")),
            )
        console.print(gen_table)

    # Cannibalization Collisions Table
    collisions = network.get("cannibalization_collisions", [])
    if collisions:
        coll_table = Table(title=f"Keyword Cannibalization Collisions ({len(collisions)} detected)", show_header=True, header_style="bold yellow")
        coll_table.add_column("Conflicting Anchor Text", style="bold yellow")
        coll_table.add_column("Conflicting Target URLs", style="white")

        for c in collisions[:5]:
            urls = "\n".join(_safe_str(u) for u in c.get("conflicting_urls", []))
            coll_table.add_row(_safe_str(c.get("anchor_text", "")), urls)
        console.print(coll_table)

    # Remediation Table
    recs = audit_result.get("recommendations", [])
    if recs:
        rec_table = Table(title="Actionable Topical Silo & Anchor Remediation", show_header=True, header_style="bold green")
        rec_table.add_column("Priority", justify="center", style="bold yellow")
        rec_table.add_column("Recommended Action", style="white")
        for idx, rec in enumerate(recs, 1):
            rec_table.add_row(str(idx), _safe_str(rec))
        console.print(rec_table)


def _print_plain_report(audit_result: Dict[str, Any]) -> None:
    """Plain-text report fallback when rich is not available."""
    url = audit_result.get("url", "")
    score = audit_result.get("overall_score", 0.0)
    grade = audit_result.get("grade", "F")
    network = audit_result.get("network_analysis", {})

    print("=" * 70)
    print(f"ContextSilo: Semantic Anchor Text & Vector Contiguity Auditor")
    print(f"Target: {url}")
    print(f"Silo Contiguity Score: {score}/100 (Grade: {grade})")
    print(f"Total Internal Links: {network.get('total_links_analyzed')}")
    print(f"Generic Anchors: {network.get('generic_anchor_count')} ({network.get('generic_anchor_ratio_percent')}%)")
    print(f"Cannibalization Collisions: {network.get('cannibalization_collisions_count')}")
    print("=" * 70)
    print("\nActionable Remediation Steps:")
    for idx, rec in enumerate(audit_result.get("recommendations", []), 1):
        print(f"  {idx}. {rec}")
    print("=" * 70)


def export_markdown_report(audit_result: Dict[str, Any]) -> str:
    """Generate comprehensive Markdown audit report."""
    url = audit_result.get("url", "")
    score = audit_result.get("overall_score", 0.0)
    grade = audit_result.get("grade", "F")
    network = audit_result.get("network_analysis", {})
    comp = audit_result.get("component_scores", {})
    dist = network.get("anchor_type_distribution", {})

    md = [
        f"# ContextSilo Semantic Anchor Text Audit: {url}",
        "",
        f"**Silo Contiguity Score**: `{score} / 100` (Grade: **{grade}**)  ",
        f"**Internal Links Analyzed**: `{network.get('total_links_analyzed')}`  ",
        f"**Average Vector Contiguity**: `{network.get('average_vector_contiguity_percent')}%`  ",
        f"**Generic Anchor Ratio**: `{network.get('generic_anchor_ratio_percent')}%` (`{network.get('generic_anchor_count')}` links)  ",
        f"**Keyword Cannibalization Collisions**: `{network.get('cannibalization_collisions_count')}`  ",
        f"**Anchor Text Diversity**: `{network.get('anchor_diversity_ratio')}%`  ",
        "",
        "---",
        "",
        "## Component Score Breakdown",
        "",
        "| Dimension | Weight | Score |",
        "|:---|:---:|:---:|",
        f"| Semantic Passage Vector Contiguity | 35% | {comp.get('semantic_contiguity', 0)}/100 |",
        f"| Generic Anchor Prevention | 30% | {comp.get('generic_anchor_prevention', 0)}/100 |",
        f"| Cannibalization & Collision Prevention | 20% | {comp.get('cannibalization_prevention', 0)}/100 |",
        f"| Anchor Diversity Balance | 15% | {comp.get('anchor_diversity', 0)}/100 |",
        "",
        "---",
        "",
        "## Anchor Classification Profile",
        "",
        "| Classification | Links | Percentage |",
        "|:---|:---:|:---:|",
    ]

    total = network.get("total_links_analyzed", 0)
    for a_type, count in dist.items():
        share = f"{round((count / total) * 100, 1)}%" if total else "0%"
        md.append(f"| {a_type.replace('_', ' ').title()} | {count} | {share} |")

    md.extend([
        "",
        "---",
        "",
        "## Actionable Remediation Plan",
        "",
    ])

    for idx, rec in enumerate(audit_result.get("recommendations", []), 1):
        md.append(f"{idx}. {rec}")

    md.append("")
    return "\n".join(md)


def export_json_report(audit_result: Dict[str, Any]) -> str:
    """Generate formatted JSON report."""
    return json.dumps(audit_result, indent=2)
