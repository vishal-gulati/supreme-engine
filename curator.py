"""News curation, ranking, section layout, and editorial formatting module.
Transforms raw feed articles into an authentic newspaper broadsheet structure.
"""

import datetime
import random
import re
from typing import Dict, List, Optional
import yfinance as yf
from weather import get_live_weather

QUOTES = [
    {"quote": "Journalism is what we need to make an democracy work.", "author": "Walter Cronkite"},
    {"quote": "The press is the watchdog of society, not its cheerleader.", "author": "H.L. Mencken"},
    {"quote": "News is what somebody somewhere wants to suppress; all the rest is advertising.", "author": "Lord Northcliffe"},
    {"quote": "Freedom of the press is not just important to democracy, it is democracy.", "author": "Walter Cronkite"},
    {"quote": "In a free country there is much clamor with little suffering; in a despotic state there is little complaint with much misery.", "author": "Carnot"},
    {"quote": "To see what is in front of one's nose needs a constant struggle.", "author": "George Orwell"},
    {"quote": "Knowledge is of two kinds. We know a subject ourselves, or we know where we can find information upon it.", "author": "Samuel Johnson"},
    {"quote": "The truth is rarely pure and never simple.", "author": "Oscar Wilde"},
]

WORDS_OF_THE_DAY = [
    {"word": "Broadsheet", "pronunciation": "[brawd-sheet]", "type": "noun", "def": "A newspaper with a large format page size, historically associated with in-depth analysis and editorial rigor."},
    {"word": "Sesquipedalian", "pronunciation": "[ses-kwi-pi-dey-lee-uhn]", "type": "adjective", "def": "Given to using long words; characterized by long and polysyllabic vocabulary."},
    {"word": "Verisimilitude", "pronunciation": "[ver-uh-si-mil-i-tood]", "type": "noun", "def": "The appearance or semblance of truth; likelihood; probability in reporting."},
    {"word": "Chiaroscuro", "pronunciation": "[kee-ahr-uh-skyoor-oh]", "type": "noun", "def": "The distribution of light and shade in a picture; by extension, sharp contrast in viewpoints."},
    {"word": "Panoply", "pronunciation": "[pan-uh-plee]", "type": "noun", "def": "A wide-ranging and impressive array, display, or collection."},
    {"word": "Ephemeral", "pronunciation": "[ih-fem-er-uhl]", "type": "adjective", "def": "Lasting for a very short time; transient, like yesterday's wire dispatches."},
    {"word": "Perspicacious", "pronunciation": "[pur-spi-key-shuhs]", "type": "adjective", "def": "Having a ready insight into and understanding of things; discerning and astute."},
]

HISTORICAL_BITS = [
    "1704: The Boston News-Letter, the first continuously published newspaper in British North America, hits the presses.",
    "1844: Samuel Morse transmits the first electric telegraph message: 'What hath God wrought!'",
    "1903: Orville and Wilbur Wright make the first powered heavier-than-air airplane flight at Kitty Hawk.",
    "1969: The first message is transmitted over ARPANET, connecting UCLA and Stanford University.",
    "1977: The Voyager 1 spacecraft launches, carrying the Golden Record of Earth's sounds and images.",
    "1993: CERN announces that the World Wide Web technology will be freely available to anyone with no royalties.",
]


def get_market_ticker() -> List[Dict]:
    """Retrieves quick market prices or returns graceful estimates."""
    symbols = {
        "^NSEI": ("NIFTY 50", "Indian Indices"),
        "^BSESN": ("SENSEX", "Indian Indices"),
        "^NSEBANK": ("BANK NIFTY", "Indian Indices"),
        "^GSPC": ("S&P 500", "US Indices"),
        "^IXIC": ("NASDAQ", "US Indices"),
        "^DJI": ("Dow Jones", "US Indices"),
        "BTC-USD": ("Bitcoin", "Crypto"),
        "ETH-USD": ("Ethereum", "Crypto"),
        "INR=X": ("USD/INR", "Forex"),
        "GC=F": ("Gold (oz)", "Commodities"),
        "SI=F": ("Silver (oz)", "Commodities"),
        "CL=F": ("Crude Oil", "Commodities"),
    }
    results = []
    try:
        tickers = yf.Tickers(" ".join(symbols.keys()))
        for sym, (label, category) in symbols.items():
            try:
                info = tickers.tickers[sym].fast_info
                price = info.last_price
                prev = info.previous_close
                change_pct = ((price - prev) / prev) * 100 if prev else 0.0
                change_val = price - prev if prev else 0.0
                day_high = getattr(info, "day_high", None)
                day_low = getattr(info, "day_low", None)

                results.append({
                    "symbol": label,
                    "ticker": sym,
                    "category": category,
                    "price": f"{price:,.2f}" if price > 10 else f"{price:,.4f}",
                    "raw_price": price,
                    "change": f"{change_pct:+.2f}%",
                    "change_val": f"{change_val:+,.2f}",
                    "up": change_pct >= 0,
                    "high": f"{day_high:,.2f}" if day_high else "—",
                    "low": f"{day_low:,.2f}" if day_low else "—",
                })
            except Exception:
                continue
    except Exception:
        pass

    if not results:
        # Fallback realistic ticker for offline / sandboxed execution
        results = [
            {"symbol": "NIFTY 50", "ticker": "^NSEI", "category": "Indian Indices", "price": "23,907.25", "raw_price": 23907.25, "change": "+0.54%", "change_val": "+128.30", "up": True, "high": "23,960.00", "low": "23,810.00"},
            {"symbol": "SENSEX", "ticker": "^BSESN", "category": "Indian Indices", "price": "79,117.11", "raw_price": 79117.11, "change": "+0.48%", "change_val": "+378.10", "up": True, "high": "79,240.00", "low": "78,920.00"},
            {"symbol": "BANK NIFTY", "ticker": "^NSEBANK", "category": "Indian Indices", "price": "51,240.80", "raw_price": 51240.80, "change": "+0.62%", "change_val": "+315.40", "up": True, "high": "51,350.00", "low": "50,980.00"},
            {"symbol": "USD/INR", "ticker": "INR=X", "category": "Forex", "price": "84.45", "raw_price": 84.45, "change": "-0.05%", "change_val": "-0.04", "up": False, "high": "84.52", "low": "84.38"},
            {"symbol": "S&P 500", "ticker": "^GSPC", "category": "US Indices", "price": "5,864.67", "raw_price": 5864.67, "change": "+0.42%", "change_val": "+24.50", "up": True, "high": "5,880.00", "low": "5,845.00"},
            {"symbol": "NASDAQ", "ticker": "^IXIC", "category": "US Indices", "price": "18,972.42", "raw_price": 18972.42, "change": "+0.68%", "change_val": "+128.10", "up": True, "high": "19,020.00", "low": "18,890.00"},
            {"symbol": "Dow Jones", "ticker": "^DJI", "category": "US Indices", "price": "43,450.20", "raw_price": 43450.20, "change": "+0.31%", "change_val": "+134.20", "up": True, "high": "43,550.00", "low": "43,320.00"},
            {"symbol": "Bitcoin", "ticker": "BTC-USD", "category": "Crypto", "price": "96,420.00", "raw_price": 96420.0, "change": "+1.85%", "change_val": "+1750.00", "up": True, "high": "97,200.00", "low": "94,800.00"},
            {"symbol": "Ethereum", "ticker": "ETH-USD", "category": "Crypto", "price": "3,410.50", "raw_price": 3410.5, "change": "+2.10%", "change_val": "+70.20", "up": True, "high": "3,450.00", "low": "3,330.00"},
            {"symbol": "Gold (oz)", "ticker": "GC=F", "category": "Commodities", "price": "2,714.50", "raw_price": 2714.5, "change": "-0.15%", "change_val": "-4.10", "up": False, "high": "2,725.00", "low": "2,705.00"},
            {"symbol": "Silver (oz)", "ticker": "SI=F", "category": "Commodities", "price": "31.42", "raw_price": 31.42, "change": "+0.80%", "change_val": "+0.25", "up": True, "high": "31.80", "low": "31.10"},
            {"symbol": "Crude Oil", "ticker": "CL=F", "category": "Commodities", "price": "74.20", "raw_price": 74.2, "change": "-0.40%", "change_val": "-0.30", "up": False, "high": "75.10", "low": "73.80"},
        ]
    return results


def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """Filters duplicate stories across feeds by link and headline tokens."""
    import urllib.parse
    seen_links = set()
    seen_token_sets = []
    deduped = []

    for art in articles:
        link = art.get("link", "").strip()
        parsed = urllib.parse.urlparse(link)
        has_deep_path = bool(parsed.path and parsed.path.strip("/"))
        if has_deep_path and link in seen_links:
            continue

        title = art.get("title", "")
        # Normalize headline tokens
        tokens = set(re.findall(r"\w{4,}", title.lower()))
        is_duplicate = False
        for prev_tokens in seen_token_sets:
            if not tokens or not prev_tokens:
                continue
            intersection = tokens.intersection(prev_tokens)
            smaller = min(len(tokens), len(prev_tokens))
            if smaller > 0 and len(intersection) / smaller > 0.7:
                is_duplicate = True
                break

        if not is_duplicate:
            if has_deep_path:
                seen_links.add(link)
            seen_token_sets.append(tokens)
            deduped.append(art)

    return deduped


def format_newspaper_edition(raw_articles: List[Dict], config: Dict) -> Dict:
    """Organizes articles into broadsheet sections, lead editorial story, and columns."""
    cleaned = deduplicate_articles(raw_articles)

    paper_name = config.get("paper_name", "THE DAILY CHRONICLE")
    motto = config.get("motto", "All the News Fit to Generate")
    city = config.get("city", "Global Edition")
    price = config.get("price", "Two Bits")

    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    roman_num = "XLII"  # Classic Roman numeral style

    # Categorize by section
    sections: Dict[str, List[Dict]] = {
        "Front Page": [],
        "India": [],
        "Markets & Stocks": [],
        "Economy & Policy": [],
        "Business & Companies": [],
        "Technology & AI": [],
        "Sports & Cricket": [],
        "Entertainment & Cinema": [],
        "Opinion & Editorial": [],
        "Science & Space": [],
        "World Affairs": [],
        "Culture & Books": [],
    }

    # Normalize category names if feeds used older aliases
    section_aliases = {
        "business": "Business & Companies",
        "technology": "Technology & AI",
        "science": "Science & Space",
        "world": "World Affairs",
        "culture": "Culture & Books",
        "markets": "Markets & Stocks",
        "economy": "Economy & Policy",
        "sports": "Sports & Cricket",
        "entertainment": "Entertainment & Cinema",
        "opinion": "Opinion & Editorial",
    }

    for art in cleaned:
        raw_sec = art.get("section", "Front Page").strip()
        sec = section_aliases.get(raw_sec.lower(), raw_sec)
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(art)

    # Choose lead story (first article from Front Page, India, Markets, or Business)
    lead_story = None
    priority_order = [
        "Front Page",
        "India",
        "Markets & Stocks",
        "Business & Companies",
        "Economy & Policy",
        "Technology & AI",
        "Sports & Cricket",
        "Entertainment & Cinema",
        "Opinion & Editorial",
        "Science & Space",
        "World Affairs",
        "Culture & Books",
    ]
    for sec_name in priority_order:
        if sections.get(sec_name):
            lead_story = sections[sec_name].pop(0)
            break

    if not lead_story and cleaned:
        lead_story = cleaned[0]

    # Quick Wire Dispatches (In Brief) - only pop if section exceeds 12 articles
    briefs = []
    for sec_name, items in sections.items():
        while len(items) > 12:
            b_item = items.pop()
            briefs.append({
                "title": b_item.get("title"),
                "link": b_item.get("link"),
                "source": b_item.get("source"),
                "author": b_item.get("author", "Staff"),
                "date": b_item.get("date", "Today"),
                "section": sec_name,
                "summary": b_item.get("summary", "")[:160] + ("..." if len(b_item.get("summary", "")) > 160 else ""),
                "content": b_item.get("content", b_item.get("summary", "")),
            })

    # Pick daily features
    quote_data = random.choice(QUOTES)
    word_data = random.choice(WORDS_OF_THE_DAY)
    history_fact = random.choice(HISTORICAL_BITS)
    markets = get_market_ticker()

    # Weather: Fetch live temperature & conditions for the configured city
    weather_city = config.get("weather_city") or config.get("city") or "Bengaluru"
    live_weather = get_live_weather(weather_city)
    weather_ear = live_weather.get("broadsheet_ear", "Fair skies over the presses.")

    # Filter out empty sections
    active_sections = {k: v for k, v in sections.items() if v}

    return {
        "paper_name": paper_name,
        "motto": motto,
        "city": city,
        "price": price,
        "date_str": date_str,
        "volume": f"Vol. {roman_num}",
        "weather_ear": weather_ear,
        "weather": live_weather,
        "lead_story": lead_story,
        "sections": active_sections,
        "briefs": briefs[:8],
        "markets": markets,
        "quote": quote_data,
        "word_of_the_day": word_data,
        "history_fact": history_fact,
        "article_count": len(cleaned),
        "generated_at": now.isoformat(),
    }
