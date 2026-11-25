"""RSS, Atom, and Web Feed Fetcher module.
Parses multi-format news feeds in parallel with robust error handling and HTML cleaning.
"""

import concurrent.futures
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (DailyChronicle/1.0)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


def clean_html_text(raw_html: str) -> str:
    """Strips HTML tags, collapses whitespace, unescapes entities."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header", "form"]):
        element.extract()
    text = soup.get_text(separator=" ")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_article_content(raw_html: str) -> str:
    """Cleans article HTML into readable multi-paragraph plain text, preserving paragraph breaks."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "header", "form", "aside", "figure", "noscript", "svg", "button"]):
        el.extract()

    # Convert block elements to newline markers
    for tag in soup.find_all(["p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]):
        tag.append("\n\n")

    text = soup.get_text()
    text = html.unescape(text)

    # Normalize paragraph breaks
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    paragraphs = []
    for line in lines:
        if line and len(line) > 30 and not any(junk in line.lower() for junk in ["click here to read", "advertisement", "all rights reserved", "terms of use", "subscribe now"]):
            paragraphs.append(line)

    if len(paragraphs) >= 2:
        return "\n\n".join(paragraphs)

    # Fallback to single text if paragraphs couldn't be cleanly segmented
    fallback = clean_html_text(raw_html)
    return fallback


def fetch_web_article_text(url: str, timeout: int = 5) -> str:
    """Attempts to scrape full multi-paragraph article body from webpage."""
    if not url or not url.startswith("http"):
        return ""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if not resp.ok:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button", "figure", "noscript"]):
            tag.extract()

        container = (
            soup.find("article")
            or soup.find(class_=re.compile(r"article[-_]body|story[-_]content|article[-_]content|story[-_]details|content[-_]area|post[-_]content|entry[-_]content", re.I))
            or soup.find(id=re.compile(r"article[-_]body|story[-_]content|articleContent", re.I))
            or soup.find("main")
        )

        target = container or soup.body
        if not target:
            return ""

        paragraphs = []
        for p in target.find_all("p"):
            p_text = clean_html_text(p.get_text())
            if len(p_text) > 45 and not any(bad in p_text.lower() for bad in ["cookie", "subscribe", "sign in", "all rights reserved", "newsletter", "advertisement"]):
                paragraphs.append(p_text)

        if len(paragraphs) >= 2:
            return "\n\n".join(paragraphs)
    except Exception:
        pass
    return ""


def clean_url(url: str) -> str:
    """Removes marketing/tracking query params from URL."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    clean_params = []
    tracking_prefixes = ("utm_", "fbclid", "gclid", "ref_", "mc_cid", "mc_eid")
    for key, val in urllib.parse.parse_qsl(parsed.query):
        if not any(key.lower().startswith(prefix) for prefix in tracking_prefixes):
            clean_params.append((key, val))
    clean_query = urllib.parse.urlencode(clean_params)
    return urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        parsed.fragment,
    ))


def extract_image_from_item(item_elem, raw_html=""):
    """Attempts to find article thumbnail from enclosures, media tags, or inline HTML."""
    # 1. Enclosure
    enclosure = item_elem.find("enclosure")
    if enclosure is not None and "image" in enclosure.get("type", ""):
        return enclosure.get("url")

    # 2. media:content or media:thumbnail
    for tag_name in ["{http://search.yahoo.com/mrss/}content", "{http://search.yahoo.com/mrss/}thumbnail", "media:content", "media:thumbnail"]:
        media = item_elem.find(tag_name)
        if media is not None and media.get("url"):
            return media.get("url")

    # 3. Inline img in description / content
    if raw_html:
        soup = BeautifulSoup(raw_html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            src = img.get("src")
            if src.startswith("http") and not any(x in src.lower() for x in ["pixel", "beacon", "stat", "tracker", "1x1"]):
                return src

    return None


def parse_feed_xml(xml_content: str, source_name: str, section: str, max_items: int = 5):
    """Parses standard RSS 2.0, Atom, or RDF feeds extracting full content and summaries."""
    articles = []

    # Helper to pick best content from an XML element or BS tag
    def get_full_and_summary(item_elem, bs_item=None):
        raw_full = ""
        raw_desc = ""

        if bs_item is not None:
            # Check content:encoded
            encoded = bs_item.find(["content:encoded", "encoded"])
            if encoded and encoded.get_text():
                raw_full = encoded.get_text()
            desc = bs_item.find(["description", "summary", "content"])
            if desc and desc.get_text():
                raw_desc = desc.get_text()
        elif item_elem is not None:
            # ElementTree
            for child in item_elem:
                tag_name = child.tag.lower().split("}")[-1]
                if tag_name in ("encoded", "content"):
                    raw_full = child.text or ""
                    break
            desc_elem = item_elem.find("description")
            if desc_elem is not None and desc_elem.text:
                raw_desc = desc_elem.text

        best_raw = raw_full if len(raw_full) > len(raw_desc) else (raw_desc or raw_full)
        full_content = clean_article_content(best_raw)
        
        # Summary is first paragraph or first 260 chars
        summary_clean = clean_html_text(raw_desc or best_raw)
        if len(summary_clean) > 280:
            summary = summary_clean[:277].rstrip() + "..."
        else:
            summary = summary_clean

        if not full_content:
            full_content = summary

        return full_content, summary, best_raw

    try:
        root = ET.fromstring(xml_content)
    except Exception:
        # Fallback to BeautifulSoup's xml parser
        try:
            soup = BeautifulSoup(xml_content, "xml")
            items = soup.find_all(["item", "entry"])
            for item in items[:max_items]:
                title = clean_html_text(item.find("title").get_text() if item.find("title") else "Untitled")
                link_tag = item.find("link")
                link = ""
                if link_tag:
                    link = link_tag.get("href") or link_tag.get_text()
                link = clean_url(link)

                full_content, summary, raw_best = get_full_and_summary(None, bs_item=item)

                author_tag = item.find(["author", "dc:creator"])
                author = clean_html_text(author_tag.get_text() if author_tag else source_name)
                if not author:
                    author = source_name

                pub_tag = item.find(["pubDate", "published", "updated", "dc:date"])
                pub_date = pub_tag.get_text().strip() if pub_tag else ""

                articles.append({
                    "title": title,
                    "link": link,
                    "content": full_content,
                    "summary": summary,
                    "author": author,
                    "date": pub_date,
                    "source": source_name,
                    "section": section,
                    "image": None,
                })
            return articles
        except Exception as e:
            print(f"Failed parsing feed {source_name}: {e}")
            return []

    # Check root tag
    tag_clean = root.tag.lower().split("}")[-1]

    # RSS 2.0 or 0.9x
    if tag_clean == "rss" or root.find("channel") is not None:
        channel = root.find("channel") or root
        items = channel.findall("item")
        for item in items[:max_items]:
            title_elem = item.find("title")
            title = clean_html_text(title_elem.text if title_elem is not None and title_elem.text else "Untitled")

            link_elem = item.find("link")
            link = clean_url(link_elem.text if link_elem is not None and link_elem.text else "")

            full_content, summary, raw_desc = get_full_and_summary(item, bs_item=None)

            author_elem = item.find("author")
            if author_elem is None:
                for child in item:
                    if child.tag.endswith("creator"):
                        author_elem = child
                        break
            author = clean_html_text(author_elem.text if author_elem is not None and author_elem.text else source_name)

            pub_elem = item.find("pubDate")
            pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

            image = extract_image_from_item(item, raw_desc)

            articles.append({
                "title": title,
                "link": link,
                "content": full_content,
                "summary": summary,
                "author": author or source_name,
                "date": pub_date,
                "source": source_name,
                "section": section,
                "image": image,
            })

    # Atom feed
    elif tag_clean == "feed":
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns) or root.findall("entry")
        for entry in entries[:max_items]:
            title_elem = entry.find("atom:title", ns) or entry.find("title")
            title = clean_html_text(title_elem.text if title_elem is not None and title_elem.text else "Untitled")

            link_elem = entry.find("atom:link", ns) or entry.find("link")
            link = ""
            if link_elem is not None:
                link = clean_url(link_elem.get("href", "") or (link_elem.text or ""))

            summary_elem = entry.find("atom:summary", ns) or entry.find("summary")
            content_elem = entry.find("atom:content", ns) or entry.find("content")
            
            raw_content = content_elem.text if content_elem is not None and content_elem.text else ""
            raw_summary = summary_elem.text if summary_elem is not None and summary_elem.text else ""
            
            best_raw = raw_content if len(raw_content) > len(raw_summary) else (raw_summary or raw_content)
            full_content = clean_article_content(best_raw)
            summary_clean = clean_html_text(raw_summary or best_raw)
            summary = summary_clean[:277].rstrip() + "..." if len(summary_clean) > 280 else summary_clean

            if not full_content:
                full_content = summary

            author_elem = entry.find("atom:author/atom:name", ns) or entry.find("author/name") or entry.find("author")
            author = clean_html_text(author_elem.text if author_elem is not None and author_elem.text else source_name)

            pub_elem = entry.find("atom:published", ns) or entry.find("atom:updated", ns) or entry.find("published") or entry.find("updated")
            pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

            articles.append({
                "title": title,
                "link": link,
                "content": full_content,
                "summary": summary,
                "author": author or source_name,
                "date": pub_date,
                "source": source_name,
                "section": section,
                "image": None,
            })

    return articles


def fetch_single_feed(source: dict, timeout: int = 8) -> list:
    """Fetches and parses a single RSS/Atom feed source."""
    url = source.get("url")
    name = source.get("name", "Unknown Source")
    section = source.get("section", "General")
    max_items = source.get("max_items", 5)

    if not url:
        return []

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        content = response.text
        return parse_feed_xml(content, name, section, max_items)
    except Exception as e:
        print(f"Error fetching feed {name} ({url}): {e}")
        return []


def fetch_all_feeds(sources: list, max_workers: int = 8) -> list:
    """Fetches all enabled feeds concurrently."""
    enabled_sources = [s for s in sources if s.get("enabled", 1)]
    if not enabled_sources:
        return []

    all_articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_source = {executor.submit(fetch_single_feed, src): src for src in enabled_sources}
        for future in concurrent.futures.as_completed(future_to_source):
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
            except Exception as e:
                src = future_to_source[future]
                print(f"Worker error on {src.get('name')}: {e}")

    return all_articles


PRESET_SOURCES = [
    # Front Page & Top Stories
    {"name": "Times of India Top Stories", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "section": "Front Page", "enabled": 1, "max_items": 10},
    {"name": "NDTV Top Stories", "url": "https://feeds.feedburner.com/ndtvnews-top-stories", "section": "Front Page", "enabled": 1, "max_items": 8},

    # India National & Politics
    {"name": "Times of India National", "url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "section": "India", "enabled": 1, "max_items": 10},
    {"name": "The Hindu (National)", "url": "https://www.thehindu.com/news/national/feeder/default.rss", "section": "India", "enabled": 1, "max_items": 8},
    {"name": "The Indian Express", "url": "https://indianexpress.com/section/india/feed/", "section": "India", "enabled": 1, "max_items": 8},

    # Markets & Stocks (Dalal Street & Equities)
    {"name": "CNBC TV18 Markets", "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml", "section": "Markets & Stocks", "enabled": 1, "max_items": 10},
    {"name": "Moneycontrol Markets", "url": "https://www.moneycontrol.com/rss/marketreports.xml", "section": "Markets & Stocks", "enabled": 1, "max_items": 10},
    {"name": "Moneycontrol Buzzing Stocks", "url": "https://www.moneycontrol.com/rss/buzzingstocks.xml", "section": "Markets & Stocks", "enabled": 1, "max_items": 8},
    {"name": "Business Standard Markets", "url": "https://www.business-standard.com/rss/markets-106.rss", "section": "Markets & Stocks", "enabled": 1, "max_items": 8},
    {"name": "LiveMint Markets", "url": "https://www.livemint.com/rss/markets", "section": "Markets & Stocks", "enabled": 1, "max_items": 8},

    # Economy & Policy
    {"name": "Moneycontrol Economy", "url": "https://www.moneycontrol.com/rss/economy.xml", "section": "Economy & Policy", "enabled": 1, "max_items": 8},
    {"name": "Business Standard Finance", "url": "https://www.business-standard.com/rss/finance-103.rss", "section": "Economy & Policy", "enabled": 1, "max_items": 8},
    {"name": "LiveMint Economy", "url": "https://www.livemint.com/rss/economy", "section": "Economy & Policy", "enabled": 1, "max_items": 8},

    # Business & Companies
    {"name": "CNBC TV18 Latest", "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/latest.xml", "section": "Business & Companies", "enabled": 1, "max_items": 10},
    {"name": "Moneycontrol Business", "url": "https://www.moneycontrol.com/rss/business.xml", "section": "Business & Companies", "enabled": 1, "max_items": 10},
    {"name": "Business Standard Top", "url": "https://www.business-standard.com/rss/home_page_top_stories.rss", "section": "Business & Companies", "enabled": 1, "max_items": 10},
    {"name": "Times of India Business", "url": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms", "section": "Business & Companies", "enabled": 1, "max_items": 8},
    {"name": "Economic Times (India)", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "section": "Business & Companies", "enabled": 1, "max_items": 8},
    {"name": "Bloomberg Markets", "url": "https://news.google.com/rss/search?q=when:24h+source:Bloomberg&hl=en-US&gl=US&ceid=US:en", "section": "Business & Companies", "enabled": 1, "max_items": 8},

    # Technology & AI
    {"name": "Hacker News Top", "url": "https://hnrss.org/frontpage", "section": "Technology & AI", "enabled": 1, "max_items": 10},
    {"name": "Times of India Tech", "url": "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms", "section": "Technology & AI", "enabled": 1, "max_items": 8},
    {"name": "Bloomberg Technology", "url": "https://news.google.com/rss/search?q=when:24h+source:Bloomberg+technology&hl=en-US&gl=US&ceid=US:en", "section": "Technology & AI", "enabled": 1, "max_items": 8},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "section": "Technology & AI", "enabled": 1, "max_items": 8},

    # Sports & Cricket
    {"name": "Times of India Sports", "url": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms", "section": "Sports & Cricket", "enabled": 1, "max_items": 10},
    {"name": "NDTV Sports", "url": "https://feeds.feedburner.com/ndtvsports-latest", "section": "Sports & Cricket", "enabled": 1, "max_items": 8},
    {"name": "Indian Express Sports", "url": "https://indianexpress.com/section/sports/feed/", "section": "Sports & Cricket", "enabled": 1, "max_items": 8},

    # Entertainment & Cinema
    {"name": "Times of India Entertainment", "url": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms", "section": "Entertainment & Cinema", "enabled": 1, "max_items": 10},
    {"name": "NDTV Movies", "url": "https://feeds.feedburner.com/ndtvmovies-latest", "section": "Entertainment & Cinema", "enabled": 1, "max_items": 8},
    {"name": "Indian Express Entertainment", "url": "https://indianexpress.com/section/entertainment/feed/", "section": "Entertainment & Cinema", "enabled": 1, "max_items": 8},

    # Opinion & Editorial
    {"name": "The Hindu Editorial", "url": "https://www.thehindu.com/opinion/editorial/feeder/default.rss", "section": "Opinion & Editorial", "enabled": 1, "max_items": 6},
    {"name": "Indian Express Opinion", "url": "https://indianexpress.com/section/opinion/feed/", "section": "Opinion & Editorial", "enabled": 1, "max_items": 6},
    {"name": "LiveMint Opinion", "url": "https://www.livemint.com/rss/opinion", "section": "Opinion & Editorial", "enabled": 1, "max_items": 6},

    # Science & Space
    {"name": "Times of India Science", "url": "https://timesofindia.indiatimes.com/rssfeeds/-2128672765.cms", "section": "Science & Space", "enabled": 1, "max_items": 8},
    {"name": "Nature News", "url": "https://www.nature.com/nature.rss", "section": "Science & Space", "enabled": 1, "max_items": 6},
    {"name": "NASA Breaking News", "url": "https://www.nasa.gov/news-release/feed/", "section": "Science & Space", "enabled": 1, "max_items": 6},

    # World Affairs
    {"name": "BBC World News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "section": "World Affairs", "enabled": 1, "max_items": 8},
    {"name": "Reuters World", "url": "https://news.google.com/rss/search?q=when:24h+source:Reuters&hl=en-US&gl=US&ceid=US:en", "section": "World Affairs", "enabled": 1, "max_items": 6},

    # Culture & Books
    {"name": "Aeon Magazine", "url": "https://aeon.co/feed.rss", "section": "Culture & Books", "enabled": 1, "max_items": 6},
]
