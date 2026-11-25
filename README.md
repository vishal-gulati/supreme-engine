# The Daily Broadsheet 🗞️

A personalized digital newspaper generator that curates, synthesizes, and formats news from user-defined sources into an authentic, printable broadsheet newspaper.

![Newspaper Preview](https://img.shields.io/badge/Aesthetic-Authentic_Broadsheet-gold)
![Dependencies](https://img.shields.io/badge/Dependencies-Standard_Python_3-brightgreen)
![Print](https://img.shields.io/badge/Export-Print_%26_PDF_Ready-blue)

---

## ✨ Features

- **Authentic Broadsheet Typography & Layout**:
  - Classic masthead with customizable paper title, Latin/English motto, date line, and forecast ear boxes.
  - Front-page lead story with prominent headline, byline, drop-caps, pull quotes, and 2-column editorial styling.
  - Categorized interior sections: **Front Page**, **Technology**, **Business**, **Science**, **World**, and **Culture**.
  - **The Lexicon** (Word of the Day), **Thought for the Day** (Quotes), and **Historical Wire** (On this day in history).
  - **Live Market Ticker Tape**: Pulls real-time financial quotes (S&P 500, NASDAQ, Bitcoin, Gold, Crude Oil) or estimates.
  - **Wire Briefs**: Fast bullet dispatches for secondary stories.

- **4 Authentic Newspaper Themes**:
  1. **Classic Broadsheet**: Warm cream paper with deep black ink and double hairline rules.
  2. **Vintage 1920s**: Aged parchment paper with sepia ink, ornamental accents, and vintage warmth.
  3. **Financial Times Salmon**: Iconic salmon-pink broadsheet with slate typography and editorial styling.
  4. **Midnight Edition**: Sleek modern dark mode broadsheet with silver text.

- **Custom Source Management ("Editorial Desk")**:
  - **Add Any RSS / Atom Feed**: Add any blog, publication, Substack, or news feed URL.
  - **Instant Feed Tester**: Test any feed URL live before adding, verifying reachability and previewing article count.
  - **Preset Library**: 1-click toggles for top feeds (Hacker News, BBC, NPR, Ars Technica, Nature, NASA, CNBC, Aeon).
  - **Section Assignment**: Direct specific feeds to specific newspaper sections.
  - **Story Cap**: Set maximum stories to pull per source.

- **Physical Print & PDF Export**:
  - Click **Print / PDF** to open the browser print dialog.
  - Includes dedicated `@media print` CSS that strips UI controls, buttons, and ticker bars, cleanly formatting the multi-column broadsheet onto physical letter/A4 pages.

- **Archives & Past Editions**:
  - Every generated edition is stored in local SQLite (`data/newspaper.db`).
  - Browse past editions by date, reload them with 1 click, or delete old ones.

- **Interactive Article Reader**:
  - Click any headline or wire brief to read the complete story in a distraction-free modal, with a direct link to the original publisher.

---

## 🚀 Quick Start

### 1. Run the App

No heavy frameworks (No React build steps or external web servers required). Uses standard Python:

```bash
# Using the run script
./run.sh

# Or directly with python3
python3 app.py 8080
```

### 2. Open in Browser

Open your browser to:
**[http://localhost:8080](http://localhost:8080)**

---

## 🛠️ Project Structure

```
.
├── app.py              # HTTP Server & REST API endpoints
├── fetcher.py          # Parallel multi-threaded RSS/Atom feed parser
├── curator.py          # News curation, lead selection, deduplication, markets
├── storage.py          # SQLite database storage (config, sources, editions)
├── seed_data.py        # Default sources and inaugural edition generator
├── run.sh              # One-line startup script
├── static/
│   ├── index.html      # Broadsheet web application interface
│   ├── css/
│   │   └── newspaper.css # Authentic broadsheet & theme styling + print rules
│   └── js/
│       └── app.js      # Frontend controller, API client, reader modals
└── README.md
```

---

## ⚙️ REST API Endpoints

- `GET /api/config` / `POST /api/config`: Read & update paper branding (name, motto, city, price).
- `GET /api/sources`: List all configured sources.
- `POST /api/sources`: Add a new feed source.
- `PUT /api/sources/<id>`: Toggle or update a source.
- `DELETE /api/sources/<id>`: Remove a source.
- `GET /api/sources/presets`: List curated feed presets.
- `POST /api/sources/test`: Test feed reachability and article parsing.
- `POST /api/generate`: Pull latest stories from enabled sources and print a new edition.
- `GET /api/editions`: Retrieve archived editions list.
- `GET /api/editions/<id>`: Retrieve specific edition content.
- `DELETE /api/editions/<id>`: Delete an edition from the archive.
- `GET /api/markets`: Get live market prices.
