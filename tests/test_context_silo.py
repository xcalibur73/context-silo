"""
Comprehensive unit tests for ContextSilo: link extraction, passage context, vector similarity, and scoring.
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from context_silo.extractor import (
    normalize_url,
    is_internal_url,
    extract_page_metadata,
    extract_internal_links_with_context,
)
from context_silo.vector_analyzer import (
    tokenize_clean,
    compute_cosine_similarity,
    classify_anchor,
    generate_suggested_anchor,
    analyze_anchor_network,
)
from context_silo.scorer import (
    calculate_contiguity_score,
    calculate_generic_prevention_score,
    calculate_cannibalization_score,
    score_anchor_network,
)
from context_silo.report_generator import export_markdown_report, export_json_report
from bs4 import BeautifulSoup


class TestContextSiloExtractor(unittest.TestCase):

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("/docs/quickstart#section", "https://example.com/"),
            "https://example.com/docs/quickstart",
        )

    def test_is_internal_url(self):
        self.assertTrue(is_internal_url("https://example.com/guide", "example.com"))
        self.assertTrue(is_internal_url("https://sub.example.com/guide", "example.com"))
        self.assertFalse(is_internal_url("https://google.com", "example.com"))

    def test_extract_page_metadata(self):
        html = """
        <html>
            <head>
                <title>Best Core Web Vitals Plugins 2026</title>
                <meta name="description" content="Detailed benchmark of WordPress performance plugins.">
            </head>
            <body>
                <h1>5 Best WordPress Speed Plugins for 2026</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        meta = extract_page_metadata(soup, "https://example.com/article")
        self.assertEqual(meta["title"], "Best Core Web Vitals Plugins 2026")
        self.assertEqual(meta["h1"], "5 Best WordPress Speed Plugins for 2026")
        self.assertEqual(meta["meta_description"], "Detailed benchmark of WordPress performance plugins.")

    def test_extract_internal_links_with_context(self):
        html = """
        <html>
            <body>
                <p>When auditing server performance, you should configure <a href="/litespeed-cache">LiteSpeed Cache</a> to minimize TTFB.</p>
                <nav><a href="/about">About Us</a></nav>
            </body>
        </html>
        """
        links = extract_internal_links_with_context(html, "https://example.com/blog", "example.com")
        self.assertEqual(len(links), 2)

        lscache_link = next(l for l in links if "/litespeed-cache" in l["target_url"])
        self.assertEqual(lscache_link["anchor_text"], "LiteSpeed Cache")
        self.assertEqual(lscache_link["placement"], "content")
        self.assertIn("When auditing server performance", lscache_link["surrounding_passage"])


class TestContextSiloVectorAnalyzer(unittest.TestCase):

    def test_tokenize_clean(self):
        tokens = tokenize_clean("The quick brown fox jumps over the lazy dog.")
        self.assertIn("quick", tokens)
        self.assertIn("brown", tokens)
        self.assertNotIn("the", tokens)

    def test_compute_cosine_similarity(self):
        toks1 = ["wordpress", "speed", "optimization", "plugins"]
        toks2 = ["wordpress", "speed", "cache", "performance"]
        sim = compute_cosine_similarity(toks1, toks2)
        self.assertGreater(sim, 0.4)

    def test_classify_anchor_generic(self):
        res = classify_anchor("click here", "How to Optimize INP", "INP Guide", "brand")
        self.assertEqual(res, "generic")

        res2 = classify_anchor("read more", "Title", "H1", "brand")
        self.assertEqual(res2, "generic")

    def test_classify_anchor_exact_match(self):
        res = classify_anchor("how to optimize inp", "How to Optimize INP", "How to Optimize INP", "brand")
        self.assertEqual(res, "exact_match")

    def test_generate_suggested_anchor(self):
        suggested = generate_suggested_anchor(
            "WordPress Cache Guide | WebAudits.pro",
            "WordPress Cache Configuration Guide",
        )
        self.assertEqual(suggested, "WordPress Cache Configuration Guide")

    def test_cannibalization_detection(self):
        mock_cluster = {
            "base_domain": "example.com",
            "pages_meta": {
                "https://example.com/post-a": {"title": "Post A", "h1": "Post A", "meta_description": ""},
                "https://example.com/post-b": {"title": "Post B", "h1": "Post B", "meta_description": ""},
            },
            "links": [
                {
                    "source_url": "https://example.com/",
                    "target_url": "https://example.com/post-a",
                    "anchor_text": "speed optimization",
                    "surrounding_passage": "Learn about speed optimization.",
                    "placement": "content",
                },
                {
                    "source_url": "https://example.com/about",
                    "target_url": "https://example.com/post-b",
                    "anchor_text": "speed optimization",
                    "surrounding_passage": "Check our speed optimization services.",
                    "placement": "content",
                },
            ],
        }
        res = analyze_anchor_network(mock_cluster)
        self.assertEqual(res["cannibalization_collisions_count"], 1)
        self.assertEqual(res["cannibalization_collisions"][0]["anchor_text"], "speed optimization")


class TestContextSiloScorer(unittest.TestCase):

    def test_calculate_contiguity_score(self):
        self.assertEqual(calculate_contiguity_score(35.0), 100.0)
        self.assertLess(calculate_contiguity_score(8.0), 40.0)

    def test_calculate_generic_prevention_score(self):
        self.assertEqual(calculate_generic_prevention_score(1.0), 100.0)
        self.assertLess(calculate_generic_prevention_score(20.0), 50.0)

    def test_score_anchor_network_grade(self):
        mock_network = {
            "average_vector_contiguity_percent": 32.0,
            "generic_anchor_ratio_percent": 2.0,
            "cannibalization_collisions_count": 0,
            "anchor_diversity_ratio": 75.0,
            "total_links_analyzed": 15,
            "generic_anchor_count": 0,
            "weak_contiguity_links": [],
            "anchor_type_distribution": {"partial_match": 10, "descriptive": 5},
        }
        scores = score_anchor_network(mock_network)
        self.assertIn(scores["grade"], ("A+", "A"))
        self.assertGreaterEqual(scores["overall_score"], 90.0)


class TestContextSiloReports(unittest.TestCase):

    def test_markdown_export(self):
        audit_res = {
            "url": "https://example.com",
            "overall_score": 94.0,
            "grade": "A",
            "component_scores": {
                "semantic_contiguity": 100.0,
                "generic_anchor_prevention": 100.0,
                "cannibalization_prevention": 100.0,
                "anchor_diversity": 85.0,
            },
            "network_analysis": {
                "total_links_analyzed": 20,
                "average_vector_contiguity_percent": 34.5,
                "generic_anchor_ratio_percent": 0.0,
                "generic_anchor_count": 0,
                "cannibalization_collisions_count": 0,
                "anchor_diversity_ratio": 80.0,
                "anchor_type_distribution": {"partial_match": 12, "descriptive": 8},
            },
            "recommendations": ["Internal anchor network is healthy."],
        }
        md = export_markdown_report(audit_res)
        self.assertIn("# ContextSilo Semantic Anchor Text Audit", md)
        self.assertIn("Silo Contiguity Score", md)

        js = export_json_report(audit_res)
        self.assertIn("overall_score", js)


if __name__ == "__main__":
    unittest.main()
