"""
HTML link, surrounding passage context, and metadata extraction engine for ContextSilo.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Set, Optional
import requests
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (ContextSilo/1.0.0)"
)


def get_base_domain(url: str) -> str:
    """Extract registered domain or hostname from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower().split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def normalize_url(url: str, base_url: str = "") -> Optional[str]:
    """Normalize URL, strip fragment, resolve relative paths."""
    if not url or not isinstance(url, str):
        return None

    cleaned = url.strip()
    lower = cleaned.lower()
    if (
        lower.startswith("javascript:")
        or lower.startswith("mailto:")
        or lower.startswith("tel:")
        or lower.startswith("data:")
        or lower.startswith("#")
    ):
        return None

    try:
        if base_url:
            resolved = urllib.parse.urljoin(base_url, cleaned)
        else:
            resolved = cleaned

        parsed = urllib.parse.urlparse(resolved)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return None

        netloc = parsed.netloc.lower()
        path = parsed.path or "/"

        if netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]

        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.scheme}://{netloc}{path}{query}"
    except Exception:
        return None


def is_internal_url(target_url: str, base_domain: str) -> bool:
    """Determine if a URL belongs to the target domain."""
    target_domain = get_base_domain(target_url)
    if not target_domain or not base_domain:
        return False
    return target_domain == base_domain or target_domain.endswith("." + base_domain)


def extract_page_metadata(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """Extract page title, primary H1, and meta description."""
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    h1 = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        h1 = h1_tag.get_text(separator=" ", strip=True)

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    return {
        "title": title,
        "h1": h1,
        "meta_description": meta_desc,
    }


def extract_internal_links_with_context(
    html: str, page_url: str, base_domain: str
) -> List[Dict[str, Any]]:
    """
    Extract all internal links along with their enclosing sentence and paragraph context,
    placement section, and rel attributes.
    """
    soup = BeautifulSoup(html, "html.parser")
    base_tag = soup.find("base", href=True)
    effective_base = base_tag["href"] if base_tag else page_url

    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        raw_href = a["href"]
        normalized = normalize_url(raw_href, effective_base)
        if not normalized or not is_internal_url(normalized, base_domain):
            continue

        # Skip self-links
        if normalized == page_url:
            continue

        anchor_text = a.get_text(separator=" ", strip=True)
        if not anchor_text:
            aria_label = a.get("aria-label", "").strip() if a.get("aria-label") else ""
            title_attr = a.get("title", "").strip() if a.get("title") else ""
            if aria_label:
                anchor_text = aria_label
            elif title_attr:
                anchor_text = title_attr
            else:
                img = a.find("img", alt=True)
                if img:
                    anchor_text = f"[Image Alt: {img['alt'].strip()}]"
                else:
                    anchor_text = "[Empty Anchor]"

        # Determine placement
        placement = "content"
        if a.find_parent(["header", "nav"]):
            placement = "navigation"
        elif a.find_parent("footer"):
            placement = "footer"
        elif a.find_parent("aside") or a.find_parent(class_=re.compile(r"sidebar", re.I)):
            placement = "sidebar"

        # Extract enclosing sentence / passage context
        passage = ""
        parent_block = a.find_parent(["p", "li", "blockquote", "td", "div"])
        if parent_block:
            raw_text = parent_block.get_text(separator=" ", strip=True)
            # Find the sentence containing the anchor
            sentences = re.split(r"(?<=[.!?])\s+", raw_text)
            for s in sentences:
                if anchor_text in s:
                    passage = s.strip()
                    break
            if not passage:
                passage = raw_text[:200].strip()
        else:
            passage = anchor_text

        rel = a.get("rel", [])
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)

        key = (normalized, anchor_text, placement)
        if key not in seen:
            seen.add(key)
            links.append({
                "source_url": page_url,
                "target_url": normalized,
                "anchor_text": anchor_text,
                "surrounding_passage": passage,
                "placement": placement,
                "rel": rel_str.lower(),
                "is_nofollow": "nofollow" in rel_str.lower(),
            })

    return links


def crawl_site_cluster(
    start_url: str,
    max_pages: int = 10,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """Crawl a cluster of internal pages to extract link network and passage contexts."""
    normalized_start = normalize_url(start_url)
    if not normalized_start:
        raise ValueError(f"Invalid target URL: {start_url}")

    base_domain = get_base_domain(normalized_start)
    req_session = session or requests.Session()
    req_session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    pages_meta: Dict[str, Dict[str, str]] = {}
    all_links: List[Dict[str, Any]] = []
    queue: List[str] = [normalized_start]
    visited: Set[str] = set()

    while queue and len(visited) < max_pages:
        current_url = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            resp = req_session.get(current_url, timeout=12)
            if resp.status_code != 200 or not resp.text:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            meta = extract_page_metadata(soup, current_url)
            pages_meta[current_url] = meta

            extracted_links = extract_internal_links_with_context(
                resp.text, current_url, base_domain
            )
            all_links.extend(extracted_links)

            # Enqueue internal targets
            for link in extracted_links:
                tgt = link["target_url"]
                if (
                    tgt not in visited
                    and tgt not in queue
                    and len(visited) + len(queue) < max_pages * 2
                ):
                    queue.append(tgt)
        except Exception:
            continue

    return {
        "start_url": normalized_start,
        "base_domain": base_domain,
        "pages_meta": pages_meta,
        "links": all_links,
        "total_pages_crawled": len(visited),
    }
