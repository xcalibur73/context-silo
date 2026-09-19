"""
Semantic anchor text classification, vector contiguity scoring, and cannibalization detection for ContextSilo.
"""

import collections
import math
import re
from typing import Dict, Any, List, Set, Tuple, Optional

GENERIC_ANCHOR_PATTERNS = {
    "click here",
    "read more",
    "learn more",
    "here",
    "this",
    "link",
    "this link",
    "this page",
    "this post",
    "this article",
    "check it out",
    "more info",
    "view more",
    "find out more",
    "continue reading",
    "website",
    "source",
    "details",
    "visit",
    "see here",
    "download",
    "go here",
    "[empty anchor]",
}

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s",
    "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "you", "your", "yours", "yourself", "yourselves"
}


def tokenize_clean(text: str) -> List[str]:
    """Tokenize and filter stop words and punctuation."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def compute_cosine_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute cosine similarity between two bags of words."""
    if not tokens_a or not tokens_b:
        return 0.0

    count_a = collections.Counter(tokens_a)
    count_b = collections.Counter(tokens_b)

    all_words = set(count_a.keys()) | set(count_b.keys())
    dot_product = sum(count_a[w] * count_b[w] for w in all_words)

    norm_a = math.sqrt(sum(v * v for v in count_a.values()))
    norm_b = math.sqrt(sum(v * v for v in count_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


NAVIGATIONAL_ANCHORS = {
    "about",
    "about us",
    "contact",
    "contact us",
    "home",
    "homepage",
    "blog",
    "docs",
    "documentation",
    "pricing",
    "privacy",
    "privacy policy",
    "terms",
    "terms of service",
    "reviews",
    "articles",
    "tools",
    "resources",
}


def classify_anchor(
    anchor_text: str,
    target_title: str,
    target_h1: str,
    brand_name: str,
) -> str:
    """
    Classify anchor text into:
    generic, navigational, naked_url, image_alt, branded, exact_match, partial_match, descriptive.
    """
    cleaned = anchor_text.strip().lower()

    if not cleaned or cleaned == "[empty anchor]":
        return "generic"

    if cleaned.startswith("[image alt:"):
        return "image_alt"

    if cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("www."):
        return "naked_url"

    if cleaned in NAVIGATIONAL_ANCHORS:
        return "navigational"

    if cleaned in GENERIC_ANCHOR_PATTERNS or len(cleaned) <= 2:
        return "generic"

    clean_brand = brand_name.lower().replace(".", "")
    if clean_brand and clean_brand in cleaned:
        return "branded"

    anchor_tokens = tokenize_clean(cleaned)
    target_tokens = set(tokenize_clean(target_h1) + tokenize_clean(target_title))

    if not anchor_tokens:
        # If words existed but were all filtered as stopwords (e.g. "Who We Are"), it is descriptive
        words = re.findall(r"\b\w+\b", cleaned)
        if words:
            return "descriptive"
        return "generic"

    overlap = set(anchor_tokens) & target_tokens
    if len(anchor_tokens) >= 2 and len(overlap) == len(anchor_tokens):
        return "exact_match"
    elif len(overlap) > 0:
        return "partial_match"
    else:
        return "descriptive"


def generate_suggested_anchor(target_title: str, target_h1: str) -> str:
    """Generate concise, contextual anchor text replacement from target entity."""
    source = target_h1.strip() if target_h1 else target_title.strip()
    if not source:
        return "related guide"

    # Clean off trailing site names e.g. "Article Title | WebAudits.pro"
    cleaned = re.sub(r"\s*[-|:]\s*.*$", "", source).strip()
    # Shorten if too long
    words = cleaned.split()
    if len(words) > 6:
        return " ".join(words[:6])
    return cleaned


def analyze_anchor_network(crawl_cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform deep anchor text analysis, vector contiguity calculations,
    and cannibalization audits across the crawled link cluster.
    """
    links = crawl_cluster.get("links", [])
    pages_meta = crawl_cluster.get("pages_meta", {})
    base_domain = crawl_cluster.get("base_domain", "")

    brand_name = base_domain.split(".")[0]

    classified_links = []
    anchor_type_counts = collections.Counter()
    anchor_to_targets = collections.defaultdict(set)

    total_contiguity_score = 0.0
    evaluated_contiguity_count = 0
    generic_links = []
    weak_contiguity_links = []

    for link in links:
        src = link["source_url"]
        tgt = link["target_url"]
        anchor = link["anchor_text"]
        passage = link["surrounding_passage"]

        meta = pages_meta.get(tgt, {})
        tgt_title = meta.get("title", "")
        tgt_h1 = meta.get("h1", "")
        tgt_desc = meta.get("meta_description", "")

        anchor_type = classify_anchor(anchor, tgt_title, tgt_h1, brand_name)
        anchor_type_counts[anchor_type] += 1

        # Track for cannibalization
        clean_anchor = anchor.strip().lower()
        if anchor_type not in ("generic", "image_alt", "naked_url") and len(clean_anchor) > 3:
            anchor_to_targets[clean_anchor].add(tgt)

        # Vector Contiguity Analysis:
        # Vector A: Anchor + Surrounding Passage
        # Vector B: Target Title + H1 + Meta Description
        source_tokens = tokenize_clean(f"{anchor} {passage}")
        target_tokens = tokenize_clean(f"{tgt_h1} {tgt_title} {tgt_desc}")

        sim = compute_cosine_similarity(source_tokens, target_tokens)

        # Context contiguity rating
        if sim >= 0.40:
            contiguity_rating = "High Contiguity"
        elif sim >= 0.20:
            contiguity_rating = "Moderate Contiguity"
        else:
            contiguity_rating = "Topical Drift / Weak"

        total_contiguity_score += sim
        evaluated_contiguity_count += 1

        entry = {
            "source_url": src,
            "target_url": tgt,
            "anchor_text": anchor,
            "surrounding_passage": passage,
            "placement": link["placement"],
            "anchor_type": anchor_type,
            "vector_similarity": round(sim, 3),
            "contiguity_rating": contiguity_rating,
        }

        if anchor_type == "generic":
            suggested = generate_suggested_anchor(tgt_title, tgt_h1)
            entry["suggested_replacement"] = suggested
            generic_links.append(entry)

        if contiguity_rating == "Topical Drift / Weak" and link["placement"] == "content":
            weak_contiguity_links.append(entry)

        classified_links.append(entry)

    # Calculate Cannibalization Collisions
    # Same non-generic anchor text pointing to 2+ distinct targets
    cannibalization_collisions = []
    for anchor, targets in anchor_to_targets.items():
        if len(targets) > 1:
            cannibalization_collisions.append({
                "anchor_text": anchor,
                "conflicting_target_count": len(targets),
                "conflicting_urls": list(targets)[:4],
            })

    total_links = len(links)
    generic_count = anchor_type_counts["generic"]
    generic_ratio = round((generic_count / total_links) * 100, 1) if total_links else 0.0

    avg_contiguity = (
        round((total_contiguity_score / evaluated_contiguity_count) * 100, 1)
        if evaluated_contiguity_count
        else 100.0
    )

    # Anchor Diversity (unique non-generic anchors / total content links)
    unique_anchors = len(set(l["anchor_text"].strip().lower() for l in links))
    diversity_ratio = round((unique_anchors / total_links) * 100, 1) if total_links else 100.0

    return {
        "total_links_analyzed": total_links,
        "unique_anchors_count": unique_anchors,
        "anchor_diversity_ratio": diversity_ratio,
        "generic_anchor_count": generic_count,
        "generic_anchor_ratio_percent": generic_ratio,
        "average_vector_contiguity_percent": avg_contiguity,
        "anchor_type_distribution": dict(anchor_type_counts),
        "cannibalization_collisions_count": len(cannibalization_collisions),
        "cannibalization_collisions": cannibalization_collisions[:8],
        "generic_links": generic_links[:10],
        "weak_contiguity_links": weak_contiguity_links[:8],
        "sample_links": classified_links[:12],
    }
