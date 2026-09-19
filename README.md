# ContextSilo

Semantic anchor text and vector contiguity auditor.

Part of the [WebAudits.pro](https://webaudits.pro) technical intelligence platform.

---

## What it does

ContextSilo audits internal linking architecture by analyzing the semantic alignment between anchor text, surrounding passage context, and destination pages. It evaluates:
- Generic anchor text ratios (identifying vague phrases like "click here", "read more", "this post", and naked URLs).
- Passage-level vector contiguity (calculating token cosine similarity between source context windows and destination content).
- Keyword cannibalization collisions (multiple conflicting destination URLs competing for identical descriptive anchor text).
- Topical silo consistency (verifying that internal links reinforce categorical topical clusters rather than leaking authority across unrelated categories).

---

## Why it exists

Modern search engines analyze internal links as contextual vector bridges rather than simple keyword matches:
- An anchor link embedded in a semantically relevant sentence transfers far more topical authority than an isolated link in a generic navigation footer.
- When two different URLs on the same domain receive internal links with the exact same focus anchor text, search engines struggle to disambiguate the canonical authority, causing ranking volatility.

ContextSilo extracts the enclosing paragraph passage for every internal link and audits semantic contiguity across the domain.

---

## Key features

- **Context Window Extraction:** Extracts the enclosing 150-word sentence window surrounding every internal link in the body copy.
- **Vector Contiguity Engine:** Computes token frequency cosine similarity between the source passage and destination page title, H1, and lead paragraph.
- **Cannibalization Collision Detector:** Identifies duplicate anchor strings targeting different internal URLs and ranks them by severity.
- **Generic Anchor Classifier:** Scans against a curated dictionary of over 80 non-descriptive anchor phrases.
- **Multiple Output Formats:** Formatted terminal reports via Rich, comprehensive Markdown documents, and machine-readable JSON.

---

## Architecture

```text
[Origin URL or Domain Root]
              |
              v
     [HTML Page Crawler] -------------> Extract Internal <a> Tags
              |
              +---> Extract Enclosing Sentence / Passage Window
              +---> Fetch Destination Page Title & H1 Headings
              |
              v
[Semantic Analysis Engine]
              |
              +---> Generic Anchor Matcher
              +---> Token Vectorizer & Cosine Similarity Calculator
              +---> Anchor Collision / Cannibalization Indexer
              |
              v
   [Silo Scoring Model] --------------> 5-Factor Weighted Contiguity Score
              |
              +---> Terminal Report (Rich Table)
              +---> Markdown Document / JSON Pipeline Output
```

ContextSilo operates in three modules:
1. `crawler.py`: Discovers and crawls internal pages up to a user-defined threshold, capturing anchor text and surrounding passage markup.
2. `vector_engine.py`: Normalizes text, removes stopwords, constructs term vectors, and computes cosine similarity between source passages and destination headings.
3. `scorer.py`: Evaluates silo health across five dimensions: Generic Anchor Elimination, Vector Contiguity, Cannibalization Prevention, Context Density, and Anchor Length Distribution.

---

## Installation

### Prerequisites
- Python 3.10 or higher

### Install from Source
```bash
git clone https://github.com/xcalibur73/context-silo.git
cd context-silo
pip install -r requirements.txt
pip install -e .
```

---

## Usage

### Basic CLI Invocation
```bash
# Audit an origin domain (up to 10 pages)
context-silo https://webaudits.pro

# Audit up to 25 pages across a specific topical subfolder
context-silo https://example.com/blog --max-pages 25

# Export JSON report for CI/CD content quality gates
context-silo https://example.com --output json --save silo-report.json

# Check installed version
context-silo --version
```

---

## Example output

```text
+-------------------------------------------------------------------------------+
| ContextSilo: Semantic Anchor Text & Vector Contiguity Auditor                 |
| Target Origin: https://webaudits.pro                                          |
| Silo Contiguity Score: 94.2/100 (Grade: A)                                    |
| Links Analyzed: 40 | Generic Anchors: 0 (0.0%) | Avg Vector Contiguity: 88.5% |
+-------------------------------------------------------------------------------+

Component Scores:
+---------------------------------+--------+------------+
| Dimension                       | Weight | Score      |
+---------------------------------+--------+------------+
| Generic Anchor Elimination      | 30%    | 100.0/100  |
| Vector Contiguity Quality       | 25%    | 88.5/100   |
| Cannibalization Collision Risk  | 25%    | 100.0/100  |
| Contextual Density              | 10%    | 90.0/100   |
| Anchor Length Distribution      | 10%    | 92.5/100   |
+---------------------------------+--------+------------+

Anchor Text Health Summary:
- Zero generic anchor strings ("click here", "read more") detected.
- Zero internal keyword cannibalization collisions found.
```

---

## Benchmark / methodology

### Empirical 12-Site Semantic Anchor Study
- **Dataset:** 12 production publishing and e-commerce websites across technical, consumer, and media verticals.
- **Command Used:** `python run.py <url> --max-pages 15 --output json`
- **Tool Version:** ContextSilo v1.0.0
- **Environment:** Windows 11 / Ubuntu 22.04, Python 3.12, unthrottled fiber network.
- **Mathematical Calculation:**
  - Cosine similarity: `dot(vecA, vecB) / (norm(vecA) * norm(vecB))` on tokenized, stopword-filtered passages.
  - Generic anchor ratio: `(generic_anchors_count / total_links_analyzed) * 100`.
- **Results:**
  - 66.7% of surveyed publishing sites exhibited internal keyword cannibalization collisions where identical anchor phrases targeted conflicting destination URLs.
  - Complete study dataset: [BENCHMARKS.md](BENCHMARKS.md).

---

## Limitations

- **Experimental Vector Heuristic:** Vector Contiguity is computed using localized term frequency token vectors. It provides an empirical lexical similarity metric but does not represent deep neural semantic embeddings (such as Google RankBrain or Gemini embeddings).
- **Context Boundaries:** Extracts the parent paragraph or sentence container. In complex multi-column layouts or nested table structures, extracted context may occasionally include adjacent metadata text.
- **Client-Rendered Anchors:** Uses standard HTTP parsing; links injected purely through client-side JavaScript interaction events require pairing with a headless browser runner.

---

## Accuracy / standards

ContextSilo categorizes its diagnostic metrics as follows:

| Metric / Check | Classification | Authority / Standard |
|:---|:---|:---|
| URL Parsing & Normalization | Web Standard | RFC 3986 |
| Generic Anchor Phrase Detection | Project-Derived Heuristic | Curated registry of 80+ non-descriptive phrases |
| Cannibalization Collision Index | Project-Derived Heuristic | Exact-string collision against destination URLs |
| Vector Contiguity Quality | Experimental Metric | Term frequency cosine similarity formula |
| Silo Contiguity Composite Score | Project-Derived Heuristic | 5-factor weighted semantic formula |

---

## Testing

ContextSilo includes unit tests covering vector similarity, text tokenization, collision detection, and scoring models:

```bash
# Run unit test suite
python -m unittest discover -s tests

# Test execution output
# Ran 14 tests in 0.002s
# OK
```

Continuous integration runs automatically on every commit and pull request via GitHub Actions across Linux and Windows environments.

---

## Roadmap

- [x] Initial release with token vectorizer and cannibalization collision detector.
- [x] PEP 621 packaging, CLI `--version`, and Windows cp1252 encoding hardening.
- [ ] Integration with local embedding models (sentence-transformers / miniLM) for dense semantic vector comparison.
- [ ] Automated internal anchor text optimization suggestions.
- [ ] WebAudits.pro continuous anchor health tracking.

---

## License

MIT License. See [LICENSE](LICENSE) for full details.
