/**
 * The Daily Broadsheet - Interactive Newspaper Application
 */

const state = {
    edition: null,
    config: {},
    sources: [],
    presets: [],
    editions: [],
    markets: [],
    weather: null,
    viewMode: localStorage.getItem('newspaper_view_mode') || 'full',
    isGenerating: false,
};

// API Client
const api = {
    async get(endpoint) {
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
    async post(endpoint, data = {}) {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        return res.json();
    },
    async put(endpoint, data = {}) {
        const res = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
    async delete(endpoint) {
        const res = await fetch(endpoint, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
};

function slugify(text) {
    if (!text) return '';
    return text.toString().toLowerCase().replace(/\s+/g, '-').replace(/[^\w\-]+/g, '');
}

// Paragraph formatting and reading helpers
function formatParagraphs(text, dropCapFirst = false) {
    if (!text) return '<p>Story dispatch awaiting wire arrival.</p>';
    const paras = text.split(/\n+/).map(p => p.trim()).filter(Boolean);
    if (!paras.length) return `<p>${escapeHtml(text)}</p>`;
    return paras.map((p, idx) => {
        const cls = (idx === 0 && dropCapFirst) ? 'drop-cap' : '';
        return `<p class="${cls}">${escapeHtml(p)}</p>`;
    }).join('');
}

function estimateReadingTime(text) {
    if (!text) return '1 min read';
    const words = text.split(/\s+/).filter(Boolean).length;
    const minutes = Math.max(1, Math.round(words / 200));
    return `${minutes} min read (${words} words)`;
}

function formatLeadStoryBody(lead) {
    const text = lead.content || lead.summary || '';
    const paras = text.split(/\n+/).map(p => p.trim()).filter(Boolean);
    if (!paras.length) {
        return '<p class="drop-cap">Dispatches confirm that this development marks a noteworthy milestone for readers following contemporary affairs.<span class="printer-end-mark">∎</span></p>';
    }

    let html = '';
    const pullquoteText = lead.title.includes(':') ? lead.title.split(':').pop().trim() : lead.title;

    paras.forEach((para, idx) => {
        const cls = idx === 0 ? 'drop-cap' : '';
        const endMark = idx === paras.length - 1 ? '<span class="printer-end-mark" title="End of dispatch">∎</span>' : '';
        html += `<p class="${cls}">${escapeHtml(para)}${endMark}</p>`;
        // Place pull quote after paragraph 1 or 2 if multiple paragraphs exist
        if (idx === Math.min(1, Math.max(0, paras.length - 2)) && paras.length >= 2) {
            html += `<div class="lead-pullquote">“${escapeHtml(pullquoteText)}”</div>`;
        }
    });

    return html;
}

function renderSectionArticle(art, secTitle, artIdx, isFeatured = false) {
    const isFullMode = state.viewMode === 'full';
    const text = art.content || art.summary || 'Summary unavailable from feed.';
    const paras = text.split(/\n+/).map(p => p.trim()).filter(Boolean);
    const readTime = estimateReadingTime(text);

    const photoHtml = art.image ? `
        <figure class="newsprint-photo">
            <img src="${escapeHtml(art.image)}" alt="${escapeHtml(art.title)}" loading="lazy" onerror="this.parentElement.style.display='none'">
            <figcaption>${escapeHtml(art.source || 'Wire Photo')} — ${escapeHtml(art.date || 'Today')}</figcaption>
        </figure>
    ` : '';

    let contentHtml = '';
    if (isFullMode || paras.length <= 1) {
        contentHtml = `
            <div class="article-full-content">
                ${paras.map((p, idx) => {
                    const endMark = idx === paras.length - 1 ? '<span class="printer-end-mark">∎</span>' : '';
                    return `<p>${escapeHtml(p)}${endMark}</p>`;
                }).join('')}
            </div>
        `;
    } else {
        // Digest mode: show first paragraph with inline expander
        contentHtml = `
            <div class="article-summary">
                <p>${escapeHtml(paras[0])}</p>
                <div id="art_more_${secTitle}_${artIdx}" class="article-full-content" style="display: none; margin-top: 0.5rem;">
                    ${paras.slice(1).map((p, idx) => {
                        const endMark = idx === paras.length - 2 ? '<span class="printer-end-mark">∎</span>' : '';
                        return `<p>${escapeHtml(p)}${endMark}</p>`;
                    }).join('')}
                </div>
            </div>
            <button class="btn-inline-toggle" onclick="toggleArticleInline('${escapeHtml(secTitle)}', ${artIdx}, this)">
                Continue Dispatch ▾
            </button>
        `;
    }

    return `
        <article class="secondary-article ${isFeatured ? 'featured-col' : ''}">
            <h3 class="article-headline" onclick="openSectionArticleReader('${escapeHtml(secTitle)}', ${artIdx})">
                ${escapeHtml(art.title)}
            </h3>
            <div class="article-byline">
                <span class="source-tag">${escapeHtml(art.source || 'Wire')}</span>
                <span>${escapeHtml(art.author ? `By ${art.author}` : '')}</span>
                <span>• ${readTime}</span>
            </div>
            ${photoHtml}
            ${contentHtml}
            <div class="article-actions-bar">
                <span class="article-read-more" onclick="openSectionArticleReader('${escapeHtml(secTitle)}', ${artIdx})">
                    Read in Folio ›
                </span>
                ${art.link ? `<a href="${escapeHtml(art.link)}" target="_blank" rel="noopener noreferrer" class="btn-inline-toggle" style="text-decoration: none;">Source ↗</a>` : ''}
            </div>
        </article>
    `;
}

function toggleArticleInline(secTitle, artIdx, btn) {
    const el = document.getElementById(`art_more_${secTitle}_${artIdx}`);
    if (!el) return;
    if (el.style.display === 'none') {
        el.style.display = 'flex';
        btn.textContent = 'Collapse Story ▴';
    } else {
        el.style.display = 'none';
        btn.textContent = 'Read Full Story ▾';
    }
}

// DOM Elements
const elements = {
    marketTicker: document.getElementById('marketTicker'),
    newspaperSheet: document.getElementById('newspaperSheet'),
    btnGenerate: document.getElementById('btnGenerate'),
    btnEditorial: document.getElementById('btnEditorial'),
    btnArchives: document.getElementById('btnArchives'),
    btnPrint: document.getElementById('btnPrint'),
    btnViewMode: document.getElementById('btnViewMode'),
    viewModeIcon: document.getElementById('viewModeIcon'),
    viewModeText: document.getElementById('viewModeText'),
    themeSelect: document.getElementById('themeSelect'),
    fontSmaller: document.getElementById('fontSmaller'),
    fontLarger: document.getElementById('fontLarger'),

    // Modals
    editorialModal: document.getElementById('editorialModal'),
    archiveModal: document.getElementById('archiveModal'),
    readerModal: document.getElementById('readerModal'),

    // Editorial Desk Elements
    sourcesTableBody: document.getElementById('sourcesTableBody'),
    presetsGrid: document.getElementById('presetsGrid'),
    formNewSource: document.getElementById('formNewSource'),
    btnTestSource: document.getElementById('btnTestSource'),
    testFeedback: document.getElementById('testFeedback'),
    formBranding: document.getElementById('formBranding'),

    // Archives Elements
    archivesList: document.getElementById('archivesList'),

    // Reader Elements
    readerTitle: document.getElementById('readerTitle'),
    readerMeta: document.getElementById('readerMeta'),
    readerBody: document.getElementById('readerBody'),
    readerOriginalLink: document.getElementById('readerOriginalLink'),
};

// Initialize Application
async function init() {
    setupEventListeners();
    setupModals();

    // Load Theme
    const savedTheme = localStorage.getItem('newspaper_theme') || 'classic';
    document.body.dataset.theme = savedTheme;
    if (elements.themeSelect) elements.themeSelect.value = savedTheme;

    updateViewModeButton();

    // Load Initial Data
    try {
        await Promise.all([loadConfig(), loadSources(), loadLatestEdition()]);
    } catch (err) {
        console.error('Initialization error:', err);
    }

    // Start background live market polling (every 45 seconds)
    setInterval(() => {
        fetchLiveMarkets(true);
    }, 45000);
}

// Load Latest Edition
async function loadLatestEdition() {
    try {
        const res = await api.get('/api/editions/latest');
        if (res.success && res.edition) {
            state.edition = res.edition.content || res.edition;
            state.edition.db_id = res.edition.id;
            state.edition.edition_number = res.edition.edition_number;
            renderNewspaper(state.edition);
        }
    } catch (err) {
        console.warn('No existing edition found, generating inaugural edition...');
        generateNewspaper();
    }
}

// Load Config
async function loadConfig() {
    try {
        const res = await api.get('/api/config');
        if (res.success && res.config) {
            state.config = res.config;
            populateBrandingForm(state.config);
        }
    } catch (err) {
        console.error('Failed to load config:', err);
    }
}

// Load Sources
async function loadSources() {
    try {
        const [srcRes, preRes] = await Promise.all([
            api.get('/api/sources'),
            api.get('/api/sources/presets'),
        ]);
        if (srcRes.success) {
            state.sources = srcRes.sources;
            renderSourcesTable();
        }
        if (preRes.success) {
            state.presets = preRes.presets;
            renderPresetsGrid();
        }
    } catch (err) {
        console.error('Failed to load sources:', err);
    }
}

// Render Market Ticker Bar with Live Pulse & Weather Pill
function renderMarketTicker(markets, weather) {
    if (!elements.marketTicker) return;
    state.markets = markets || state.markets || [];
    state.weather = weather || state.weather || null;

    const weatherHtml = state.weather ? `
        <div class="ticker-weather-pill" title="Live Weather for ${escapeHtml(state.weather.city)}">
            <span>${state.weather.icon || '🌤️'}</span>
            <strong>${escapeHtml(state.weather.city.split(',')[0])}:</strong>
            <span>${state.weather.temp_c}°C (${state.weather.temp_f}°F)</span>
            <small style="opacity: 0.85;">${escapeHtml(state.weather.condition)}</small>
        </div>
    ` : '';

    const itemsHtml = state.markets.map(m => `
        <div class="ticker-item">
            <span class="symbol">${escapeHtml(m.symbol)}</span>
            <span class="price">${escapeHtml(m.price)}</span>
            <span class="change ${m.up ? 'up' : 'down'}">${m.up ? '▲' : '▼'} ${escapeHtml(m.change)}</span>
        </div>
    `).join('');

    elements.marketTicker.innerHTML = `
        <div class="ticker-left-wrap">
            <span class="live-pulse-dot" title="Live Feed Connected"></span>
            <span style="font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: #e5a93c; font-weight: 800;">LIVE INDICES</span>
            ${weatherHtml}
            <button class="ticker-refresh-btn" onclick="fetchLiveMarkets(false)" title="Fetch latest index prices">↻ Refresh</button>
        </div>
        <div class="ticker-scroll-content">
            ${itemsHtml}
        </div>
    `;
    elements.marketTicker.style.display = 'flex';
}

// Fetch Live Markets
async function fetchLiveMarkets(silent = true) {
    try {
        const res = await api.get('/api/markets');
        if (res.success && res.markets) {
            state.markets = res.markets;
            if (state.edition) {
                state.edition.markets = res.markets;
            }
            renderMarketTicker(state.markets, state.weather);
            updateAlmanacTable(state.markets);
            if (!silent) showToast('📈 Live market indices refreshed!');
        }
    } catch (err) {
        if (!silent) alert(`Could not refresh markets: ${err.message}`);
    }
}

function updateAlmanacTable(markets) {
    const tbody = document.getElementById('almanacTableBody');
    if (tbody && markets && markets.length) {
        tbody.innerHTML = renderAlmanacRows(markets);
    }
}

function renderAlmanacRows(markets) {
    if (!markets || !markets.length) {
        return '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1rem;">No market data available.</td></tr>';
    }
    return markets.map(m => `
        <tr>
            <td><strong>${escapeHtml(m.symbol)}</strong></td>
            <td><span class="badge-section" style="font-size: 0.68rem; padding: 0.1rem 0.35rem;">${escapeHtml(m.category || 'Index')}</span></td>
            <td class="text-right"><strong>${escapeHtml(m.price)}</strong></td>
            <td class="text-right ${m.up ? 'val-up' : 'val-down'}">${m.up ? '▲' : '▼'} ${escapeHtml(m.change)}</td>
            <td class="text-right ${m.up ? 'val-up' : 'val-down'}">${escapeHtml(m.change_val || '—')}</td>
            <td class="text-right" style="color: var(--text-muted);">${escapeHtml(m.high || '—')}</td>
            <td class="text-right" style="color: var(--text-muted);">${escapeHtml(m.low || '—')}</td>
        </tr>
    `).join('');
}

// Render Newspaper
function renderNewspaper(edition) {
    if (!edition || !elements.newspaperSheet) return;

    const weather = edition.weather || state.weather || {
        city: 'Bengaluru, India',
        temp_c: 26.5,
        temp_f: 79.7,
        condition: 'Mainly Clear',
        icon: '🌤️',
        humidity: '58%',
        wind: '11 km/h',
        high_c: 29.0,
        low_c: 19.5,
        poetic: 'Fair skies with gentle breeze across the avenues',
    };
    state.weather = weather;

    renderMarketTicker(edition.markets, weather);

    const paperName = edition.paper_name || state.config.paper_name || 'THE DAILY CHRONICLE';
    const motto = edition.motto || state.config.motto || "All the News Fit to Generate";
    const city = edition.city || state.config.city || 'India & Global Edition';
    const price = edition.price || state.config.price || 'Two Bits';
    const dateStr = edition.date_str || new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const volume = edition.volume || `Vol. ${edition.edition_number ? toRoman(edition.edition_number) : 'I'}, No. 1`;

    const lead = edition.lead_story || {
        title: 'Newsroom Awaits the Evening Wire',
        summary: 'No lead story dispatched yet. Add feeds in the Editorial Desk and press Generate.',
        author: 'Staff Reporter',
        source: 'Editorial Desk',
    };

    const quote = edition.quote || {
        quote: "To see what is in front of one's nose needs a constant struggle.",
        author: 'George Orwell',
    };

    const word = edition.word_of_the_day || {
        word: 'Broadsheet',
        pronunciation: '[brawd-sheet]',
        type: 'noun',
        def: 'A newspaper with a large format page size.',
    };

    const historyFact = edition.history_fact || 'The printing press changed the course of human knowledge forever.';
    const briefs = edition.briefs || [];
    const sections = edition.sections || {};

    const sectionEntries = Object.entries(sections).filter(([, arts]) => arts && arts.length);
    const sectionLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

    let html = `
        <!-- Newspaper Masthead -->
        <div class="newspaper-top-bar">
            <span>${escapeHtml(city)}</span>
            <span>◆ THE INDEPENDENT COMPENDIUM ◆</span>
            <span>${escapeHtml(price)}</span>
        </div>

        <div class="masthead-container">
            <div class="masthead-ear left">
                <div class="ear-title">Weather &amp; Almanac</div>
                <div style="font-weight: 700; font-size: 0.82rem;">${escapeHtml(weather.city || city)}</div>
                <div style="font-size: 1.25rem; font-weight: 900; margin: 0.15rem 0;">
                    ☀ ${weather.temp_c}°C <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">/ ${weather.temp_f}°F</span>
                </div>
                <div style="font-style: italic; font-size: 0.74rem;">${escapeHtml(weather.condition || 'Clear')}</div>
                <div style="font-size: 0.68rem; color: var(--text-muted); margin-top: 0.2rem; border-top: 1px dotted var(--border-light); padding-top: 0.15rem;">
                    H: ${weather.high_c}°C · L: ${weather.low_c}°C · Hum: ${weather.humidity || '58%'}
                </div>
            </div>
            <div class="masthead-center">
                <h1 class="newspaper-title">${escapeHtml(paperName)}</h1>
                <div class="newspaper-motto">“${escapeHtml(motto)}”</div>
            </div>
            <div class="masthead-ear right">
                <div class="ear-title">Press Registry</div>
                <div>${escapeHtml(volume)}<br><small>Strictly Verified</small></div>
            </div>
        </div>

        <div class="newspaper-dateline-bar">
            <span>${escapeHtml(dateStr)}</span>
            <span>DAILY MORNING BROADCAST</span>
            <span>EDITION NO. ${edition.edition_number || '1'}</span>
        </div>

        <!-- Section Navigation Index -->
        <nav class="section-nav-bar">
            <span style="color: var(--accent-color); font-weight: 800; letter-spacing: 0.1em;">EDITION INDEX:</span>
            ${sectionEntries.map(([sec, arts], idx) => `<a class="section-nav-link" href="#sec_${slugify(sec)}"><span class="section-nav-code">${sectionLetters[idx] || 'S'}1</span> ${escapeHtml(sec)} (${arts.length})</a>`).join(' · ')}
        </nav>

        <!-- Front Page Hero & Side Column -->
        <div class="lead-section-grid">
            <article class="lead-article">
                <span class="lead-kicker">◆ LEAD DISPATCH OF THE DAY</span>
                <h2 class="lead-headline" onclick="openArticleReader(0, true)">${escapeHtml(lead.title)}</h2>
                <div class="article-byline">
                    <span>By ${escapeHtml(lead.author || 'Staff')}</span>
                    <span>•</span>
                    <span class="source-tag">${escapeHtml(lead.source || 'Wire Service')}</span>
                    <span>•</span>
                    <span>${escapeHtml(lead.date || 'Today')}</span>
                </div>
                <div class="lead-article-body">
                    ${formatLeadStoryBody(lead)}
                </div>
                <div class="article-actions-bar">
                    <span class="article-reading-time">${estimateReadingTime(lead.content || lead.summary)}</span>
                    <span class="article-read-more" onclick="openArticleReader(0, true)">
                        Read in Folio ›
                    </span>
                    ${lead.link ? `<a href="${escapeHtml(lead.link)}" target="_blank" rel="noopener noreferrer" class="btn-inline-toggle" style="text-decoration: none;">Source ↗</a>` : ''}
                </div>
            </article>

            <aside class="side-column">
                <!-- Live Weather Almanac Box -->
                <div class="feature-box">
                    <div class="feature-box-title">
                        <span>Meteorological Dispatch</span>
                        <span>§</span>
                    </div>
                    <div class="weather-details-card">
                        <div class="weather-temp-hero">
                            <div class="weather-degrees">${weather.temp_c}°C <small style="font-size: 0.95rem; color: var(--text-muted); font-weight: 600;">(${weather.temp_f}°F)</small></div>
                            <div class="weather-icon-large" style="font-family: var(--font-headline);">☀</div>
                        </div>
                        <div style="font-family: var(--font-headline); font-size: 1.05rem; font-weight: 700;">${escapeHtml(weather.condition || 'Fair Weather')}</div>
                        <div style="font-size: 0.84rem; font-style: italic; color: var(--text-secondary); margin-bottom: 0.35rem;">“${escapeHtml(weather.poetic || 'Pleasant conditions prevailing.')}”</div>
                        <div class="weather-meta-row">
                            <span>High: ${weather.high_c}°C</span>
                            <span>Low: ${weather.low_c}°C</span>
                            <span>Wind: ${escapeHtml(weather.wind || '10 km/h')}</span>
                        </div>
                    </div>
                </div>

                <!-- Quote of the Day Box -->
                <div class="feature-box">
                    <div class="feature-box-title">
                        <span>Thought for the Day</span>
                        <span>📜</span>
                    </div>
                    <div class="quote-text">“${escapeHtml(quote.quote)}”</div>
                    <div class="quote-author">— ${escapeHtml(quote.author)}</div>
                </div>

                <!-- Word of the Day -->
                <div class="feature-box">
                    <div class="feature-box-title">
                        <span>The Lexicon</span>
                        <span>📖</span>
                    </div>
                    <div class="word-term">${escapeHtml(word.word)}</div>
                    <div class="word-meta">${escapeHtml(word.pronunciation)} · ${escapeHtml(word.type)}</div>
                    <div class="word-def">${escapeHtml(word.def)}</div>
                </div>

                <!-- On This Day -->
                <div class="feature-box">
                    <div class="feature-box-title">
                        <span>Historical Wire</span>
                        <span>⏳</span>
                    </div>
                    <div class="word-def" style="font-style: italic;">${escapeHtml(historyFact)}</div>
                </div>

                <!-- In Brief / Wire Dispatches -->
                ${briefs.length ? `
                <div class="feature-box" style="background: transparent;">
                    <div class="feature-box-title">
                        <span>Wire Briefs</span>
                        <span>◆</span>
                    </div>
                    <ul class="wire-briefs-list">
                        ${briefs.slice(0, 4).map((b, idx) => `
                            <li class="wire-brief-item">
                                <div class="wire-brief-title" onclick="openBriefReader(${idx})">${escapeHtml(b.title)}</div>
                                <div class="wire-brief-meta">${escapeHtml(b.source)} · ${escapeHtml(b.section)}</div>
                                <div class="wire-brief-summary">${escapeHtml(b.summary || '')}</div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                ` : ''}
            </aside>
        </div>

        <!-- Subtle Broadsheet Horizontal Fold Crease -->
        <div class="paper-fold-crease" aria-hidden="true"></div>

        <!-- Financial Markets & Live Index Almanac Table -->
        <div class="almanac-box">
            <div class="almanac-header">
                <span>§ Dalal Street &amp; Global Financial Almanac — Live Index Quotes</span>
                <button class="ticker-refresh-btn" onclick="fetchLiveMarkets(false)" style="font-size: 0.7rem; padding: 0.12rem 0.45rem; color: var(--text-primary); border-color: var(--border-color);">↻ Refresh Quotes</button>
            </div>
            <div style="overflow-x: auto;">
                <table class="almanac-table">
                    <thead>
                        <tr>
                            <th>Index / Asset</th>
                            <th>Category</th>
                            <th class="text-right">Price</th>
                            <th class="text-right">Change (%)</th>
                            <th class="text-right">Net Change</th>
                            <th class="text-right">Day High</th>
                            <th class="text-right">Day Low</th>
                        </tr>
                    </thead>
                    <tbody id="almanacTableBody">
                        ${renderAlmanacRows(edition.markets || state.markets)}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Render Categorized Sections with Physical Broadsheet Flags
    sectionEntries.forEach(([secTitle, articles], secIdx) => {
        const secCode = `${sectionLetters[secIdx] || 'S'}1`;
        const useFeaturedFirst = articles.length >= 2 && articles.length % 3 !== 0;

        html += `
            <div id="sec_${slugify(secTitle)}" class="section-divider-bar">
                <span class="section-title">
                    <span class="section-flag-code">SECTION ${secCode}</span>
                    <span>${escapeHtml(secTitle)}</span>
                </span>
                <span class="section-count-tag">${articles.length} Dispatches</span>
            </div>
            <div class="section-grid">
                ${articles.slice(0, 15).map((art, artIdx) => renderSectionArticle(art, secTitle, artIdx, useFeaturedFirst && artIdx === 0)).join('')}
            </div>
        `;
    });

    // Colophon / Footer
    html += `
        <div class="newspaper-colophon">
            Published & Printed Digitally for Personal Reading • The Daily Broadsheet Engine<br>
            All stories aggregated directly from user-selected RSS/Atom sources • Certified Edition No. ${edition.edition_number || '1'}
        </div>
    `;

    elements.newspaperSheet.innerHTML = html;
}

// Generate New Newspaper Edition
async function generateNewspaper() {
    if (state.isGenerating) return;
    state.isGenerating = true;

    if (elements.btnGenerate) {
        elements.btnGenerate.disabled = true;
        elements.btnGenerate.innerHTML = `<span class="spin">⏳</span> Printing New Edition...`;
    }

    try {
        const res = await api.post('/api/generate', {
            paper_name: state.config.paper_name,
            motto: state.config.motto,
            city: state.config.city,
        });

        if (res.success && res.edition) {
            state.edition = res.edition.content || res.edition;
            state.edition.db_id = res.edition.id;
            state.edition.edition_number = res.edition.edition_number;
            renderNewspaper(state.edition);

            window.scrollTo({ top: 0, behavior: 'smooth' });
            showToast('🗞️ Fresh newspaper edition successfully printed!');
        }
    } catch (err) {
        console.error('Generation error:', err);
        alert(`Error generating newspaper: ${err.message}`);
    } finally {
        state.isGenerating = false;
        if (elements.btnGenerate) {
            elements.btnGenerate.disabled = false;
            elements.btnGenerate.innerHTML = `<span>🗞️</span> Generate Fresh Edition`;
        }
    }
}

// Render Sources in Editorial Desk
function renderSourcesTable() {
    if (!elements.sourcesTableBody) return;
    if (!state.sources.length) {
        elements.sourcesTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #9ca3af; padding: 1.5rem;">No sources configured. Add one below or select from presets!</td></tr>`;
        return;
    }

    elements.sourcesTableBody.innerHTML = state.sources
        .map(
            (s) => `
        <tr>
            <td>
                <label class="toggle-switch">
                    <input type="checkbox" ${s.enabled ? 'checked' : ''} onchange="toggleSource(${s.id}, this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </td>
            <td>
                <strong>${escapeHtml(s.name)}</strong><br>
                <small style="color: #9ca3af; word-break: break-all;">${escapeHtml(s.url)}</small>
            </td>
            <td><span class="badge-section">${escapeHtml(s.section)}</span></td>
            <td>${s.max_items || 5} stories</td>
            <td>
                <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; color: #f43f5e;" onclick="deleteSource(${s.id})">
                    Delete
                </button>
            </td>
        </tr>
    `
        )
        .join('');
}

// Render Presets Grid
function renderPresetsGrid() {
    if (!elements.presetsGrid) return;
    const existingUrls = new Set(state.sources.map((s) => s.url.toLowerCase().trim()));

    elements.presetsGrid.innerHTML = state.presets
        .map((p) => {
            const isAdded = existingUrls.has(p.url.toLowerCase().trim());
            return `
            <div class="preset-card">
                <div>
                    <div class="preset-name">${escapeHtml(p.name)}</div>
                    <div class="preset-sec">Section: ${escapeHtml(p.section)}</div>
                </div>
                <button class="btn ${isAdded ? 'btn-secondary' : 'btn-primary'}" 
                        style="padding: 0.35rem 0.6rem; font-size: 0.78rem; width: 100%; margin-top: 0.5rem;"
                        ${isAdded ? 'disabled' : ''}
                        onclick="addPresetSource('${escapeHtml(p.name)}', '${escapeHtml(p.url)}', '${escapeHtml(p.section)}')">
                    ${isAdded ? '✓ Added' : '+ Add Feed'}
                </button>
            </div>
        `;
        })
        .join('');
}

// Source Management Actions
async function toggleSource(id, enabled) {
    try {
        await api.put(`/api/sources/${id}`, { enabled: enabled ? 1 : 0 });
        const src = state.sources.find((s) => s.id === id);
        if (src) src.enabled = enabled ? 1 : 0;
    } catch (err) {
        console.error('Failed to toggle source:', err);
    }
}

async function deleteSource(id) {
    if (!confirm('Are you sure you want to remove this source?')) return;
    try {
        await api.delete(`/api/sources/${id}`);
        state.sources = state.sources.filter((s) => s.id !== id);
        renderSourcesTable();
        renderPresetsGrid();
        showToast('Source removed.');
    } catch (err) {
        alert(`Failed to delete source: ${err.message}`);
    }
}

async function addPresetSource(name, url, section) {
    try {
        const res = await api.post('/api/sources', {
            name,
            url,
            section,
            enabled: 1,
            max_items: 5,
        });
        if (res.success) {
            state.sources = res.sources;
            renderSourcesTable();
            renderPresetsGrid();
            showToast(`Added ${name} to ${section}!`);
        }
    } catch (err) {
        alert(`Could not add preset: ${err.message}`);
    }
}

// Test Feed URL in Form
async function testFeedUrl() {
    const urlInput = document.getElementById('newSourceUrl');
    const url = urlInput ? urlInput.value.trim() : '';
    if (!url) {
        alert('Please enter a feed URL to test.');
        return;
    }

    elements.btnTestSource.disabled = true;
    elements.btnTestSource.textContent = 'Testing...';
    elements.testFeedback.textContent = 'Connecting to feed...';
    elements.testFeedback.style.color = '#9ca3af';

    try {
        const res = await api.post('/api/sources/test', { url });
        if (res.success) {
            elements.testFeedback.textContent = `✓ Success! Found ${res.count} articles. Feed is ready.`;
            elements.testFeedback.style.color = '#10b981';
            // Suggest title if name is empty
            const nameInput = document.getElementById('newSourceName');
            if (nameInput && !nameInput.value && res.sample && res.sample[0]) {
                nameInput.value = res.sample[0].source || 'Custom Feed';
            }
        }
    } catch (err) {
        elements.testFeedback.textContent = `✗ ${err.message}`;
        elements.testFeedback.style.color = '#f43f5e';
    } finally {
        elements.btnTestSource.disabled = false;
        elements.btnTestSource.textContent = 'Test URL';
    }
}

// Populate Branding Form
function populateBrandingForm(config) {
    if (!elements.formBranding) return;
    const nameEl = document.getElementById('brandPaperName');
    const mottoEl = document.getElementById('brandMotto');
    const cityEl = document.getElementById('brandCity');
    const weatherCityEl = document.getElementById('brandWeatherCity');
    const priceEl = document.getElementById('brandPrice');

    if (nameEl) nameEl.value = config.paper_name || '';
    if (mottoEl) mottoEl.value = config.motto || '';
    if (cityEl) cityEl.value = config.city || '';
    if (weatherCityEl) weatherCityEl.value = config.weather_city || 'Bengaluru';
    if (priceEl) priceEl.value = config.price || '';
}

// Save Branding Form
async function saveBranding(e) {
    e.preventDefault();
    const configUpdate = {
        paper_name: document.getElementById('brandPaperName').value.trim(),
        motto: document.getElementById('brandMotto').value.trim(),
        city: document.getElementById('brandCity').value.trim(),
        weather_city: (document.getElementById('brandWeatherCity') ? document.getElementById('brandWeatherCity').value.trim() : '') || 'Bengaluru',
        price: document.getElementById('brandPrice').value.trim(),
    };

    try {
        const res = await api.post('/api/config', configUpdate);
        if (res.success) {
            state.config = res.config;
            if (state.edition) {
                state.edition.paper_name = configUpdate.paper_name;
                state.edition.motto = configUpdate.motto;
                state.edition.city = configUpdate.city;
                state.edition.price = configUpdate.price;
                renderNewspaper(state.edition);
            }
            closeModal(elements.editorialModal);
            showToast('Newspaper branding updated!');
        }
    } catch (err) {
        alert(`Failed to save branding: ${err.message}`);
    }
}

// Archives List
async function openArchivesModal() {
    openModal(elements.archiveModal);
    elements.archivesList.innerHTML = `<p style="color: #9ca3af; text-align: center; padding: 2rem;">Loading archived editions...</p>`;

    try {
        const res = await api.get('/api/editions');
        if (res.success && res.editions) {
            state.editions = res.editions;
            if (!state.editions.length) {
                elements.archivesList.innerHTML = `<p style="color: #9ca3af; text-align: center; padding: 2rem;">No past editions in archive.</p>`;
                return;
            }

            elements.archivesList.innerHTML = state.editions
                .map(
                    (ed) => `
                <div style="background: #282a30; border: 1px solid #3b3f49; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 1rem; color: #f3f4f6;">Edition #${ed.edition_number}</strong>
                        <div style="font-size: 0.8rem; color: #9ca3af;">${escapeHtml(ed.date_str)} · Recorded at ${new Date(ed.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-primary" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;" onclick="loadSpecificEdition(${ed.id})">
                            Read Edition
                        </button>
                        <button class="btn btn-secondary" style="padding: 0.35rem 0.6rem; font-size: 0.8rem; color: #f43f5e;" onclick="deleteArchivedEdition(${ed.id})">
                            Delete
                        </button>
                    </div>
                </div>
            `
                )
                .join('');
        }
    } catch (err) {
        elements.archivesList.innerHTML = `<p style="color: #f43f5e;">Failed to load archives: ${err.message}</p>`;
    }
}

async function loadSpecificEdition(id) {
    try {
        const res = await api.get(`/api/editions/${id}`);
        if (res.success && res.edition) {
            state.edition = res.edition.content || res.edition;
            state.edition.db_id = res.edition.id;
            state.edition.edition_number = res.edition.edition_number;
            renderNewspaper(state.edition);
            closeModal(elements.archiveModal);
            window.scrollTo({ top: 0, behavior: 'smooth' });
            showToast(`Opened Edition #${res.edition.edition_number}`);
        }
    } catch (err) {
        alert(`Failed to load edition: ${err.message}`);
    }
}

async function deleteArchivedEdition(id) {
    if (!confirm('Delete this edition from the archive?')) return;
    try {
        await api.delete(`/api/editions/${id}`);
        openArchivesModal(); // Refresh list
    } catch (err) {
        alert(`Failed to delete edition: ${err.message}`);
    }
}

// Article Reader Modal
function openArticleReader(idx, isLead = false) {
    if (!state.edition) return;
    const article = isLead ? state.edition.lead_story : null;
    if (!article) return;
    displayArticleInModal(article);
}

function openSectionArticleReader(sectionName, idx) {
    if (!state.edition || !state.edition.sections || !state.edition.sections[sectionName]) return;
    const article = state.edition.sections[sectionName][idx];
    if (!article) return;
    displayArticleInModal(article);
}

function openBriefReader(idx) {
    if (!state.edition || !state.edition.briefs || !state.edition.briefs[idx]) return;
    const article = state.edition.briefs[idx];
    displayArticleInModal(article);
}

function updateViewModeButton() {
    if (!elements.viewModeText) return;
    if (state.viewMode === 'full') {
        elements.viewModeText.textContent = 'Full Articles';
        if (elements.viewModeIcon) elements.viewModeIcon.textContent = '📖';
    } else {
        elements.viewModeText.textContent = 'Digest Mode';
        if (elements.viewModeIcon) elements.viewModeIcon.textContent = '📑';
    }
}

function displayArticleInModal(article) {
    elements.readerTitle.textContent = article.title || 'Untitled Dispatch';
    const text = article.content || article.summary || 'Full article dispatch unavailable from feed.';
    const readTime = estimateReadingTime(text);
    elements.readerMeta.textContent = `${article.source || 'Wire'} • By ${article.author || 'Staff'} • ${article.date || 'Today'} • ${readTime}`;
    elements.readerBody.innerHTML = `
        <div class="article-full-content" style="font-size: 1.08rem; line-height: 1.8;">
            ${formatParagraphs(text, true)}
        </div>
    `;
    if (article.link) {
        elements.readerOriginalLink.href = article.link;
        elements.readerOriginalLink.style.display = 'inline-flex';
    } else {
        elements.readerOriginalLink.style.display = 'none';
    }
    openModal(elements.readerModal);
}

// Modal Handlers
function setupModals() {
    document.querySelectorAll('.modal-backdrop').forEach((backdrop) => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) closeModal(backdrop);
        });
    });

    document.querySelectorAll('.modal-close-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-backdrop');
            if (modal) closeModal(modal);
        });
    });

    // Modal Tabs
    document.querySelectorAll('.modal-tab-btn').forEach((tabBtn) => {
        tabBtn.addEventListener('click', () => {
            const targetId = tabBtn.dataset.tab;
            const container = tabBtn.closest('.modal-dialog');
            container.querySelectorAll('.modal-tab-btn').forEach((b) => b.classList.remove('active'));
            container.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));

            tabBtn.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
        });
    });
}

function openModal(modal) {
    if (modal) modal.classList.add('active');
}

function closeModal(modal) {
    if (modal) modal.classList.remove('active');
}

// Event Listeners
function setupEventListeners() {
    if (elements.btnGenerate) {
        elements.btnGenerate.addEventListener('click', generateNewspaper);
    }

    if (elements.btnEditorial) {
        elements.btnEditorial.addEventListener('click', () => {
            populateBrandingForm(state.config);
            renderSourcesTable();
            renderPresetsGrid();
            openModal(elements.editorialModal);
        });
    }

    if (elements.btnArchives) {
        elements.btnArchives.addEventListener('click', openArchivesModal);
    }

    if (elements.btnPrint) {
        elements.btnPrint.addEventListener('click', () => window.print());
    }

    if (elements.btnViewMode) {
        elements.btnViewMode.addEventListener('click', () => {
            state.viewMode = state.viewMode === 'full' ? 'digest' : 'full';
            localStorage.setItem('newspaper_view_mode', state.viewMode);
            updateViewModeButton();
            if (state.edition) {
                renderNewspaper(state.edition);
            }
            showToast(`View mode: ${state.viewMode === 'full' ? 'Full Articles' : 'Digest Mode'}`);
        });
    }

    if (elements.themeSelect) {
        elements.themeSelect.addEventListener('change', (e) => {
            const theme = e.target.value;
            document.body.dataset.theme = theme;
            localStorage.setItem('newspaper_theme', theme);
        });
    }

    // Font Size Controls
    let currentBaseFont = 16;
    if (elements.fontSmaller) {
        elements.fontSmaller.addEventListener('click', () => {
            if (currentBaseFont > 13) {
                currentBaseFont -= 1;
                document.documentElement.style.fontSize = `${currentBaseFont}px`;
            }
        });
    }
    if (elements.fontLarger) {
        elements.fontLarger.addEventListener('click', () => {
            if (currentBaseFont < 22) {
                currentBaseFont += 1;
                document.documentElement.style.fontSize = `${currentBaseFont}px`;
            }
        });
    }

    // Add Source Form
    if (elements.formNewSource) {
        elements.formNewSource.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('newSourceName').value.trim();
            const url = document.getElementById('newSourceUrl').value.trim();
            const section = document.getElementById('newSourceSection').value;
            const maxItems = parseInt(document.getElementById('newSourceMax').value, 10) || 5;

            if (!name || !url) return;

            try {
                const res = await api.post('/api/sources', {
                    name,
                    url,
                    section,
                    enabled: 1,
                    max_items: maxItems,
                });
                if (res.success) {
                    state.sources = res.sources;
                    renderSourcesTable();
                    renderPresetsGrid();
                    elements.formNewSource.reset();
                    if (elements.testFeedback) elements.testFeedback.textContent = '';
                    showToast(`Added source: ${name}`);
                }
            } catch (err) {
                alert(`Error adding source: ${err.message}`);
            }
        });
    }

    if (elements.btnTestSource) {
        elements.btnTestSource.addEventListener('click', testFeedUrl);
    }

    if (elements.formBranding) {
        elements.formBranding.addEventListener('submit', saveBranding);
    }
}

// Toast helper
function showToast(msg) {
    const existing = document.querySelector('.app-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'app-toast';
    toast.textContent = msg;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #1e293b;
        color: #fff;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        font-family: var(--font-ui);
        font-size: 0.88rem;
        font-weight: 500;
        z-index: 9999;
        border: 1px solid #334155;
        animation: toastIn 0.2s ease-out;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function toRoman(num) {
    const lookup = { M: 1000, CM: 900, D: 500, CD: 400, C: 100, XC: 90, L: 50, XL: 40, X: 10, IX: 9, V: 5, IV: 4, I: 1 };
    let roman = '';
    for (let i in lookup) {
        while (num >= lookup[i]) {
            roman += i;
            num -= lookup[i];
        }
    }
    return roman || 'I';
}

// Boot
window.addEventListener('DOMContentLoaded', init);
