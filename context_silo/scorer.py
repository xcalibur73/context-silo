"""
Scoring and remediation synthesis engine for ContextSilo.
"""

from typing import Dict, Any, List


def calculate_contiguity_score(avg_contiguity_percent: float) -> float:
    """Score semantic vector contiguity (0-100)."""
    # In practice, cosine similarity of token bags between passage and title/H1
    # ranges from 0.15 to 0.55 for related pages.
    if avg_contiguity_percent >= 30.0:
        return 100.0
    elif avg_contiguity_percent >= 22.0:
        return round(85.0 + ((avg_contiguity_percent - 22.0) * 1.8), 1)
    elif avg_contiguity_percent >= 15.0:
        return round(65.0 + ((avg_contiguity_percent - 15.0) * 2.8), 1)
    elif avg_contiguity_percent >= 10.0:
        return round(40.0 + ((avg_contiguity_percent - 10.0) * 5.0), 1)
    else:
        return max(10.0, round(avg_contiguity_percent * 4.0, 1))


def calculate_generic_prevention_score(generic_ratio: float) -> float:
    """Score generic anchor prevention (0-100)."""
    if generic_ratio <= 3.0:
        return 100.0
    elif generic_ratio <= 8.0:
        return round(100.0 - ((generic_ratio - 3.0) * 3.0), 1)
    elif generic_ratio <= 15.0:
        return round(85.0 - ((generic_ratio - 8.0) * 3.5), 1)
    elif generic_ratio <= 25.0:
        return round(60.0 - ((generic_ratio - 15.0) * 2.5), 1)
    else:
        return max(0.0, round(35.0 - ((generic_ratio - 25.0) * 1.5), 1))


def calculate_cannibalization_score(collision_count: int, total_links: int) -> float:
    """Score anchor collision and cannibalization prevention (0-100)."""
    if collision_count == 0:
        return 100.0
    elif collision_count <= 2:
        return 85.0
    elif collision_count <= 5:
        return 70.0
    elif collision_count <= 10:
        return 50.0
    else:
        return max(15.0, round(45.0 - (collision_count * 2.0), 1))


def calculate_diversity_score(diversity_ratio: float) -> float:
    """Score anchor text diversity (0-100)."""
    if diversity_ratio >= 60.0:
        return 100.0
    elif diversity_ratio >= 40.0:
        return round(80.0 + ((diversity_ratio - 40.0) * 1.0), 1)
    elif diversity_ratio >= 25.0:
        return round(60.0 + ((diversity_ratio - 25.0) * 1.3), 1)
    else:
        return max(20.0, round(diversity_ratio * 2.4, 1))


def score_anchor_network(network_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate composite Topical Silo Contiguity Score and synthesize remediation steps."""
    avg_contiguity = network_analysis.get("average_vector_contiguity_percent", 0.0)
    generic_ratio = network_analysis.get("generic_anchor_ratio_percent", 0.0)
    collision_count = network_analysis.get("cannibalization_collisions_count", 0)
    diversity_ratio = network_analysis.get("anchor_diversity_ratio", 100.0)
    total_links = network_analysis.get("total_links_analyzed", 0)

    contiguity_score = calculate_contiguity_score(avg_contiguity)
    generic_score = calculate_generic_prevention_score(generic_ratio)
    cannibalization_score = calculate_cannibalization_score(collision_count, total_links)
    diversity_score = calculate_diversity_score(diversity_ratio)

    composite = round(
        (contiguity_score * 0.35)
        + (generic_score * 0.30)
        + (cannibalization_score * 0.20)
        + (diversity_score * 0.15),
        1,
    )

    if composite >= 95:
        grade = "A+"
    elif composite >= 85:
        grade = "A"
    elif composite >= 75:
        grade = "B"
    elif composite >= 65:
        grade = "C"
    elif composite >= 50:
        grade = "D"
    else:
        grade = "F"

    # Actionable remediation synthesis
    recs = []
    generic_count = network_analysis.get("generic_anchor_count", 0)
    if generic_count > 0:
        recs.append(
            f"Replace {generic_count} generic anchor link(s) ('click here', 'read more', 'link'): "
            f"Generic anchors destroy semantic vector signaling. Update them to descriptive phrases "
            f"derived from the target page's primary H1 entity."
        )

    if collision_count > 0:
        recs.append(
            f"Resolve {collision_count} anchor cannibalization collision(s): Identical anchor text is linking "
            f"to multiple distinct URLs, triggering semantic ambiguity and keyword cannibalization across your topical clusters."
        )

    weak_count = len(network_analysis.get("weak_contiguity_links", []))
    if weak_count > 0:
        recs.append(
            f"Strengthen passage context for {weak_count} low-contiguity internal link(s): Surrounding sentences "
            f"lack semantic overlap with target page entities, signaling unnatural or out-of-silo linking."
        )

    dist = network_analysis.get("anchor_type_distribution", {})
    exact_count = dist.get("exact_match", 0)
    if total_links > 0 and (exact_count / total_links) > 0.40:
        recs.append(
            f"Diversify anchor text profile ({exact_count} exact-match links, {round((exact_count / total_links)*100)}% of total): "
            f"High exact-match concentrations can trigger algorithmic over-optimization filters. Intersperse long-tail variations."
        )

    if not recs:
        recs.append(
            "Internal anchor network demonstrates strong vector contiguity, healthy anchor diversity, and zero keyword cannibalization."
        )

    return {
        "overall_score": composite,
        "grade": grade,
        "component_scores": {
            "semantic_contiguity": contiguity_score,
            "generic_anchor_prevention": generic_score,
            "cannibalization_prevention": cannibalization_score,
            "anchor_diversity": diversity_score,
        },
        "recommendations": recs,
    }
