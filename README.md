# ContextSilo

The Semantic Anchor Text & Vector Contiguity Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Production](https://img.shields.io/badge/status-production-success.svg)](#)
[![Cloud Engine: WebAudits.pro](https://img.shields.io/badge/cloud-webaudits.pro-orange.svg)](https://webaudits.pro/tools/context-silo)

ContextSilo is a command-line utility and semantic audit engine that evaluates internal link anchor text profiles, computes passage-level vector contiguity, and uncovers keyword cannibalization collisions across multi-page website architectures. Modern search engines evaluate link networks as semantic vector graphs, where surrounding paragraph context and entity contiguity dictate topic authority.

Key capabilities:
- Surrounding Passage Context Extraction: Extracts the exact 25-50 word enclosing sentence and paragraph for every internal link to analyze surrounding co-occurrence signals.
- Semantic Vector Contiguity Scoring: Calculates token-level cosine similarity between the source passage context and the destination page's Title, primary H1, and Meta Description.
- Anchor Cannibalization Collision Detector: Pinpoints instances where identical anchor phrases link to multiple competing destination URLs, confusing search engine entity attribution.
- Generic Anchor Detection & Auto-Remediation: Identifies low-value anchor phrases ("click here", "read more", "learn more", "link") and synthesizes entity-rich drop-in replacements directly from target metadata.
- Anchor Distribution Profiler: Quantifies anchor portfolio health across Exact Match, Partial Match, Descriptive, Branded, Navigational, and Naked URL categories.
- Multi-format reporting: High-contrast terminal dashboard, Markdown audit summaries, and automated JSON pipelines.

---

## The Engineering Problem

Internal linking strategy has shifted dramatically from exact-match keyword stuffing to semantic topical networks:

1. **Topical Silo Contiguity Breakage**: When links bridge across disparate topics without contextual transition sentences, search engines treat the link as noise or algorithmic manipulation. High-performing silos maintain tight semantic contiguity between the linking sentence and the destination page.
2. **Anchor Cannibalization Collisions**: Large publishing sites frequently reuse identical descriptive anchors (e.g., "WordPress Speed Guide") across different articles, splitting ranking signals and triggering internal keyword cannibalization.
3. **The Generic Anchor Penalty**: Low-value anchors ("read more", "click here") waste valuable crawl equity and deprive neural search embeddings of entity disambiguation clues.

ContextSilo provides an automated, mathematical audit to detect and resolve these defects.

---

## Mathematical Architecture

ContextSilo computes vector contiguity between the linking passage and the destination document:

### 1. Vector Cosine Similarity

Given a source passage token vector S (composed of anchor text and surrounding sentence words) and a destination document vector D (composed of target Title, primary H1, and Meta Description):

```
Similarity(S, D) = (S . D) / (||S|| * ||D||)
```

Where token vectors filter language stop words and represent normalized term frequencies.

### 2. Contiguity Rating Scale

- `High Contiguity` (Similarity >= 0.40): Strong semantic overlap and natural contextual bridge.
- `Moderate Contiguity` (0.20 <= Similarity < 0.40): Acceptable topical relevance.
- `Topical Drift / Weak Contiguity` (Similarity < 0.20): Out-of-silo link or abrupt anchor insertion lacking semantic context.

### 3. Cannibalization Collision Heuristic

A collision is triggered when a non-branded, non-generic anchor phrase A satisfies:

```
|{ TargetURL_1, TargetURL_2, ... TargetURL_k }| >= 2
```

Indicating that the same semantic promise is directing search engines to multiple competing URLs.

---

## Installation

```bash
git clone https://github.com/xcalibur73/context-silo.git
cd context-silo
pip install -r requirements.txt
```

---

## Usage Guide

### 1. Audit Semantic Anchors (Default Multi-Page Cluster)

```bash
python run.py https://example.com
```

### 2. Deep Cluster Crawl (e.g. 20 Pages)

```bash
python run.py https://example.com --max-pages 20
```

### 3. Export Markdown Audit Report

```bash
python run.py https://example.com --output markdown --save anchor_audit.md
```

### 4. Export Structured JSON for Automated Pipelines

```bash
python run.py https://example.com --output json --save anchor_audit.json
```

---

## Benchmark Case Studies

See [BENCHMARKS.md](BENCHMARKS.md) for empirical anchor text studies across 12 production web properties, demonstrating that 66.7% of surveyed publishing sites suffer from internal keyword cannibalization collisions.

---

## Cloud Architecture

ContextSilo is maintained as part of the WebAudits.pro performance ecosystem. For instant browser-based semantic anchor audits without local Python dependencies, use the cloud engine at [webaudits.pro/tools/context-silo](https://webaudits.pro/tools/context-silo).

---

## License

MIT License. Copyright (c) 2026 xcalibur73.
