"""Seed data and initialization script.
Pre-populates default sources and generates an expansive inaugural edition
with all 12 broadsheet categories and 40+ rich, multi-paragraph articles.
"""

from storage import init_db, get_sources, add_source, save_edition, get_editions, get_config
from fetcher import PRESET_SOURCES
from curator import format_newspaper_edition
import datetime

SAMPLE_ARTICLES = [
    # --- 1. FRONT PAGE ---
    {
        "title": "India Launches National Supercomputing and AI Infrastructure Mission",
        "link": "https://www.thehindu.com",
        "summary": "The Union Cabinet has ratified a landmark multi-billion rupee initiative to deploy indigenous GPU clusters and quantum-resilient optical corridors across major Indian academic research institutions.",
        "content": "In a decisive stride toward technological autonomy, the Union Cabinet has formally approved the deployment of indigenous high-performance computing clusters and quantum-resilient optical transmission corridors connecting forty premier academic and research laboratories across India.\n\nThe mission, coordinated jointly by the Centre for Development of Advanced Computing (C-DAC) and the Department of Science and Technology, aims to establish an aggregate compute capacity of over 150 petaflops by 2026. Central to the architecture is an open-source, energy-efficient silicon accelerator developed in collaboration with Indian Institute of Technology research consortia.\n\nAddressing a press briefing in New Delhi, the Minister for Electronics and Information Technology emphasized that sovereign compute capabilities are essential for training foundational generative models tailored to India's twenty-two official languages and thousands of regional dialects. Early pilot deployments in monsoon forecasting, genomic epidemiology, and agricultural yield prediction have demonstrated a fourfold reduction in computation latency.\n\nAcademic partners noted that the decentralized topology will democratize tier-1 computational access for postgraduate scholars outside metropolitan centers, cementing India's trajectory as a global epicenter for open, equitable artificial intelligence engineering.",
        "author": "Venkatesh Raghavan, National Bureau",
        "date": "Today, 06:30 AM",
        "source": "The Hindu",
        "section": "Front Page",
        "image": None,
    },
    {
        "title": "Quantum Leap in Distributed Systems: Real-Time Multi-Agent Consensus Achieved",
        "link": "https://news.ycombinator.com",
        "summary": "Engineers unveil a decentralized protocol enabling autonomous intelligent agents to coordinate cross-network tasks with microsecond consensus.",
        "content": "Researchers at the International Computational Consortium have officially unveiled a decentralized orchestration framework enabling autonomous intelligent agents to coordinate cross-network tasks with microsecond consensus.\n\nUnder conventional paradigms, cooperative neural systems suffered from exponential latency degradation whenever swarm sizes crossed several dozen nodes. The new protocol introduces cryptographic state checkpoints coupled with speculative token streaming, allowing multi-agent swarms to verify and execute complex logistical and analytical workflows across disparate cloud regions without centralized bottlenecks.\n\nField trials conducted across twenty-four industrial data centers demonstrated a 94 percent reduction in synchronization overhead during high-concurrency automated scheduling. In supply-chain simulations involving autonomous freight, customs clearances, and regional distribution depots, the swarms resolved cross-continental transit bottlenecks in seconds where legacy enterprise software historically required hours of human triage.\n\n“We are no longer merely distributing data queries across clusters; we are distributing coherent cognitive consensus,” stated Dr. Eleanor Vance, lead architect of the consortium's protocol initiative.",
        "author": "Dr. Eleanor Vance",
        "date": "Today, 07:15 AM",
        "source": "Hacker News Top",
        "section": "Front Page",
        "image": None,
    },
    {
        "title": "Renewable Energy Capacity Surpasses 200 GW as Solar Interconnects Accelerate",
        "link": "https://timesofindia.indiatimes.com",
        "summary": "India's non-fossil power generation capacity crosses an unprecedented threshold driven by ultra-mega solar parks in Rajasthan and Gujarat.",
        "content": "India has officially crossed the milestone of 200 gigawatts of installed renewable power generation capacity, propelled by aggressive commissioning of ultra-mega solar parks across the arid plains of Rajasthan and Gujarat.\n\nData released by the Central Electricity Authority confirms that solar and wind now account for nearly 45 percent of the nation's total installed power capacity, pacing ahead of the initial timelines outlined in India's international climate pledges. Crucially, battery energy storage systems (BESS) co-located at transmission substations have successfully absorbed midday generation peaks to supply uninterrupted evening baseload power.\n\nGrid operators noted that advanced inverter technologies and dynamic transmission line ratings have prevented grid congestion, enabling southern and western surplus generation to seamlessly power industrial hubs in northern states. Power sector analysts forecast another 35 GW of renewable capacity additions over the coming fiscal year as domestic photovoltaic cell manufacturing ramps to scale.",
        "author": "Sanjay Sharma",
        "date": "Today, 08:00 AM",
        "source": "Times of India",
        "section": "Front Page",
        "image": None,
    },

    # --- 2. INDIA ---
    {
        "title": "Supreme Court Upholds Digital Privacy Safeguards in Public Delivery Schemes",
        "link": "https://indianexpress.com",
        "summary": "A constitution bench reaffirms proportionality and algorithmic transparency as indispensable prerequisites for biometric citizen verification.",
        "content": "In an authoritative ruling delivered on Tuesday, a five-judge Constitution Bench of the Supreme Court affirmed that digital verification mechanisms in public welfare distribution must adhere strictly to the tenets of proportionality, necessity, and algorithmic accountability.\n\nThe bench observed that while administrative digitisation has drastically curbed illicit leakages in welfare subsidies, technological failure or biometric mismatches cannot be invoked by bureaucratic apparatuses to deny fundamental entitlements such as food grains, disability allowances, or rural employment wages.\n\nThe verdict mandates administrative bodies to provide seamless offline fallback channels, time-bound grievance redressal desks, and periodic independent privacy audits of centralized citizen registries. Legal commentators hailed the pronouncement as a landmark jurisprudence reconciling state welfare efficiency with citizen autonomy in an increasingly digitized democracy.",
        "author": "Apoorva Mandhani",
        "date": "Today, 08:45 AM",
        "source": "Indian Express",
        "section": "India",
        "image": None,
    },
    {
        "title": "Vande Bharat Sleeper Trains Enter Final Commissioning Trials on Delhi-Mumbai Trunk Route",
        "link": "https://www.ndtv.com",
        "summary": "High-speed overnight trainsets featuring aerodynamic nose cones and ergonomic berths undergo oscillating track trials.",
        "content": "Indian Railways has initiated the final phase of high-speed oscillatory trials for the flagship Vande Bharat Sleeper trainset along the critical 1,384-kilometer Delhi-Mumbai trunk route, targeting an inaugural commercial rollout next month.\n\nEngineered at the Integral Coach Factory in Chennai, the sixteen-coach trainset incorporates lightweight austenitic stainless steel carbodies, intelligent crash-worthy couplers, and European-standard air suspension bogies rated for operational velocities of up to 160 kilometers per hour. The sleeper configuration features articulated pneumatic doors, sensor-activated touchless washrooms, and isolated acoustic dampening yielding interior noise levels below 58 decibels.\n\nRailway Board officials reported that comprehensive track stability and dynamic braking tests yielded flawless parameters across both straight stretches and curvilinear sections through the Western Ghats. The overnight sleeper service is anticipated to curtail transit durations between Mumbai and the national capital to under twelve hours.",
        "author": "NDTV News Desk",
        "date": "Today, 09:10 AM",
        "source": "NDTV",
        "section": "India",
        "image": None,
    },
    {
        "title": "Unified Health Interface Crosses 500 Million Linked Ayushman Digital Records",
        "link": "https://www.thehindu.com",
        "summary": "The National Health Authority records record adoption of interoperable electronic health records across district hospitals and primary health centers.",
        "content": "The National Health Authority's Ayushman Bharat Digital Mission (ABDM) has surpassed the monumental milestone of 500 million verified citizen health accounts linked to interoperable electronic diagnostic and medical records.\n\nThe decentralized architecture allows patients to securely grant time-delimited access to historical blood panels, radiological scans, and prescription histories to attending physicians across private clinics and public district hospitals nationwide, eliminating repetitive and costly redundant diagnostic tests.\n\nState-level deployment figures indicate that rural primary health centers in Uttar Pradesh, Kerala, and Maharashtra have emerged as frontrunners in paperless token generation, with over 120,000 active medical facilities onboarded to the registry. Public health specialists project the repository will serve as the analytical backbone for early outbreak surveillance and preventative epidemiological interventions.",
        "author": "Bindu Shajan Perappadan",
        "date": "Today, 09:40 AM",
        "source": "The Hindu",
        "section": "India",
        "image": None,
    },

    # --- 3. MARKETS & STOCKS ---
    {
        "title": "Nifty 50 and Sensex Scale New Heights Led by Banking and Automotive Rallies",
        "link": "https://www.moneycontrol.com",
        "summary": "Domestic benchmark indices surged to fresh all-time peaks during early trade on Dalal Street, propelled by vigorous institutional inflows.",
        "content": "Dalal Street witnessed robust buying momentum on Wednesday morning as benchmark indices vaulted to fresh historic peaks, driven by aggressive institutional accumulation across large-cap private banking, capital goods, and automobile manufacturers.\n\nThe 50-share NSE Nifty scaled an intraday high above 24,100 points, while the 30-share BSE Sensex jumped over 480 points to comfortably cross the 79,500 threshold. Bank Nifty commanded the session's gains, surging 1.1 percent on the back of healthy net interest margin disclosures and historically low non-performing asset provisions in quarterly earnings updates.\n\nForeign Institutional Investors (FIIs) turned net buyers for the fourth consecutive trading session, pumping over Rs 3,200 crore into domestic equities alongside unwavering domestic mutual fund SIP inflows totaling Rs 21,000 crore monthly. Market breadth remained decisively positive with advances outnumbering declines by nearly two to one across broader mid-cap and small-cap indices.",
        "author": "Kshitij Anand",
        "date": "Today, 10:15 AM",
        "source": "Moneycontrol",
        "section": "Markets & Stocks",
        "image": None,
    },
    {
        "title": "IT Services Sector Rebounds as Cloud Transformation and Generative AI Deals Surge",
        "link": "https://www.cnbctv18.com",
        "summary": "Top Indian tier-1 tech exporters report swelling order books for enterprise cloud modernization and proprietary AI integration pipelines.",
        "content": "Shares of India's premier information technology exporters rallied between 2 and 4 percent following a string of major multi-year enterprise transformation deal wins announced across North American and European banking clients.\n\nIndustry bellwethers noted that global Fortune 500 enterprises have transitioned from exploratory generative AI proof-of-concepts to full-scale operational contract commitments. Deal sizes reflect widespread legacy application re-platforming onto hybrid cloud fabrics paired with fine-tuned domain-specific agent architectures.\n\nBrokerage analysts at major domestic institutions upgraded their sectoral outlook to 'Overweight', pointing to stabilizing attrition rates, rising operating margins, and expanding dollar-revenue guidance for the upcoming quarters. The Nifty IT index led sectoral gainers, rising 1.8 percent to outpace the broader market.",
        "author": "Latha Venkatesh, CNBC-TV18",
        "date": "Today, 10:45 AM",
        "source": "CNBC-TV18",
        "section": "Markets & Stocks",
        "image": None,
    },
    {
        "title": "Indian Sovereign Bond Yields Ease as RBI Liquidity Operations Stabilize Money Markets",
        "link": "https://www.business-standard.com",
        "summary": "Benchmark 10-year government bond yields dipped to 6.98 percent following proactive open market repurchases and benign wholesale inflation prints.",
        "content": "The yield on the benchmark 10-year Indian Government Bond eased by four basis points to settle at 6.98 percent, breaking below the crucial 7.00 percent psychological resistance level amid supportive liquidity management from the Reserve Bank of India.\n\nBond dealers reported heightened buying appetite from domestic commercial banks and insurance funds after the central bank conducted short-term variable rate reverse repo operations to smooth quarter-end systemic liquidity demands. Concurrently, benign core wholesale inflation readings bolstered expectations that the Monetary Policy Committee will maintain an accommodative liquidity stance.\n\nPrimary dealers observed that foreign portfolio investor holdings under the Fully Accessible Route (FAR) have expanded systematically following India's successful inclusion in emerging market sovereign debt indices, providing a reliable foreign exchange cushion for the rupee.",
        "author": "Anup Roy",
        "date": "Today, 11:00 AM",
        "source": "Business Standard",
        "section": "Markets & Stocks",
        "image": None,
    },

    # --- 4. ECONOMY & POLICY ---
    {
        "title": "Goods and Services Tax Collections Clock Rs 1.82 Lakh Crore in Monthly Surge",
        "link": "https://www.business-standard.com",
        "summary": "Robust manufacturing output and digitized compliance mechanisms propel gross GST receipts to their second-highest recorded monthly tally.",
        "content": "Gross Goods and Services Tax (GST) revenue collections for the preceding month surged to Rs 1.82 lakh crore, marking an impressive 11.2 percent year-on-year expansion and registering the second-highest monthly total since the indirect tax regime's inception in 2017.\n\nOfficial data from the Ministry of Finance highlighted that collections from domestic transactions grew by 12.8 percent, underpinned by sustained capital expenditure, festive wholesale clearances, and resilient consumer discretionary demand across both urban centers and tier-2 towns. Revenue from imports also posted healthy growth following increased capital goods imports by domestic manufacturers.\n\nEconomists highlighted that the sustained buoyancy in tax collections expands the government's fiscal headroom, enabling continued public capex allocation into high-speed expressways, freight corridors, and multi-modal logistics parks while maintaining disciplined glide paths toward fiscal deficit consolidation.",
        "author": "Dilasha Seth",
        "date": "Today, 07:30 AM",
        "source": "Business Standard",
        "section": "Economy & Policy",
        "image": None,
    },
    {
        "title": "RBI Monetary Policy Committee Keeps Repo Rate Steady, Highlights Inflation Vigilance",
        "link": "https://www.cnbctv18.com",
        "summary": "The central bank maintains a balanced growth-stability posture while monitoring seasonal food price variances and geopolitical oil dynamics.",
        "content": "The Reserve Bank of India's Monetary Policy Committee voted by a unanimous majority to hold the policy repo rate unchanged at 6.50 percent, maintaining its focused stance of withdrawal of accommodation to ensure retail inflation aligns durably with the 4 percent midpoint target.\n\nDelivering the policy statement from Mint Street, Governor Shaktikanta Das noted that domestic economic fundamentals remain inherently resilient, characterized by healthy corporate balance sheets, rising manufacturing capacity utilization, and robust bank credit growth expanding above 15 percent.\n\nWhile headline Consumer Price Index inflation has moderated within the central bank's tolerance band, the committee underscored the necessity of vigilant monitoring regarding volatile vegetable prices and erratic weather distributions. The central bank projected real GDP growth for the fiscal year at a buoyant 7.2 percent, retaining India's status as the fastest-growing major global economy.",
        "author": "Shereen Bhan, CNBC-TV18",
        "date": "Today, 08:15 AM",
        "source": "CNBC-TV18",
        "section": "Economy & Policy",
        "image": None,
    },
    {
        "title": "Semiconductor Incentive Scheme Attracts $15 Billion in Advanced Packaging and Fab Projects",
        "link": "https://www.moneycontrol.com",
        "summary": "Global chip giants finalize joint ventures for commercial silicon foundries and outsourced semiconductor assembly facilities in Dholera and Sanand.",
        "content": "India's strategic drive to establish a domestic semiconductor ecosystem has received unprecedented momentum, with committed capital outlays under the India Semiconductor Mission crossing the $15 billion threshold.\n\nCivil construction is advancing rapidly at the Dholera semiconductor fab in Gujarat, engineered in partnership between domestic industrial conglomerates and Taiwanese manufacturing foundries. Concurrently, commercial testing and packaging operations are slated to commence at advanced assembly and test facilities in Sanand, targeting automotive microcontrollers and consumer electronic power modules.\n\nIndustry experts note that by anchoring wafer fabrication alongside specialty chemical suppliers, ultra-pure water filtration systems, and precision gas distributors, India is establishing a defensible high-tech manufacturing cluster that will insulate domestic electronics manufacturers from cross-border supply chain chokepoints.",
        "author": "Sunil Mohanty",
        "date": "Today, 09:00 AM",
        "source": "Moneycontrol",
        "section": "Economy & Policy",
        "image": None,
    },

    # --- 5. BUSINESS & COMPANIES ---
    {
        "title": "Tata Group and Airbus Finalize First Indigenous Assembly Line for C-295 Aircraft",
        "link": "https://www.business-standard.com",
        "summary": "The Final Assembly Line in Vadodara represents the first private-sector military transport aircraft manufacturing complex in India.",
        "content": "Tata Advanced Systems Limited (TASL) and European aerospace consortium Airbus have inaugurated the state-of-the-art Final Assembly Line (FAL) facility in Vadodara, Gujarat, designated to produce forty C-295 tactical transport aircraft for the Indian Air Force.\n\nThe sprawling aerospace complex marks the first time that a complete military transport aircraft will be manufactured by a private industrial consortium within India. The facility integrates advanced robotic rivet systems, automated composite lay-up cells, and precision avionics integration benches capable of producing complex airframes to international defense specifications.\n\nBeyond meeting sovereign defense needs, the joint venture aims to position the Vadodara manufacturing hub as an international export base for tactical airlifters servicing Southeast Asian, Middle Eastern, and African defense forces over the coming decade.",
        "author": "Ajai Shukla",
        "date": "Today, 07:45 AM",
        "source": "Business Standard",
        "section": "Business & Companies",
        "image": None,
    },
    {
        "title": "Reliance Retail and Blinkit Expand 10-Minute Dark Store Networks Across Tier-2 India",
        "link": "https://www.cnbctv18.com",
        "summary": "Quick commerce operators expand fulfillment depots into Lucknow, Jaipur, and Coimbatore as hyper-local delivery adoption surges.",
        "content": "India's quick-commerce revolution is rapidly penetrating beyond metropolitan borders, with leading retail players and quick-delivery platforms establishing hundreds of micro-fulfillment dark stores across tier-2 and tier-3 urban centers.\n\nOperating metrics from recent quarterly filings reveal that average order values in cities such as Lucknow, Chandigarh, Surat, and Coimbatore have reached parity with metropolitan averages, driven by rapid consumer demand for groceries, small home electronics, beauty products, and festive essentials delivered in under fifteen minutes.\n\nSupply chain executives credit localized inventory algorithms, automated shelf-picking robotics, and localized direct-from-farm procurement corridors for keeping delivery logistics profitable while expanding product catalogs to over 25,000 distinct SKUs.",
        "author": "Mugdha Kalra",
        "date": "Today, 08:30 AM",
        "source": "CNBC-TV18",
        "section": "Business & Companies",
        "image": None,
    },
    {
        "title": "Bloomberg: Global Sovereign Wealth Funds Direct Over $8 Billion Into Indian Green Corridors",
        "link": "https://www.bloomberg.com",
        "summary": "Pension funds and sovereign entities from Singapore, Abu Dhabi, and Canada deepen long-term direct investments into Indian transmission and logistics.",
        "content": "Global sovereign wealth and pension managers have poured more than $8 billion of long-term direct equity into Indian infrastructure assets over the past nine months, according to institutional transaction data compiled by Bloomberg.\n\nKey allocations have centered on operational transmission trusts, clean energy independent power producers, and grade-A warehousing logistics platforms. Institutional investors cite stable regulatory frameworks, clear tariff indexing mechanisms, and superior risk-adjusted yields relative to Western fixed-income securities.\n\nSenior private equity partners noted that India's programmatic National Monetisation Pipeline has offered transparent, brownfield operating assets with predictable cash-flow characteristics, cementing the country's status as the top emerging market destination for patient institutional capital.",
        "author": "Santanu Chakraborty, Bloomberg",
        "date": "Today, 09:15 AM",
        "source": "Bloomberg",
        "section": "Business & Companies",
        "image": None,
    },

    # --- 6. TECHNOLOGY & AI ---
    {
        "title": "Silicon Photonics Breakthrough Yields Tenfold Bandwidth Efficiency on Monolithic CMOS",
        "link": "https://feeds.arstechnica.com",
        "summary": "Fabrication laboratories succeed in integrating micro-ring optical resonators directly into 2-nanometer CMOS logic wafers.",
        "content": "Semiconductor fabrication laboratories have announced a historic breakthrough in electro-optic co-packaging, successfully integrating silicon nitride micro-ring optical resonators directly onto monolithic 2-nanometer CMOS logic wafers without hybrid bonding defects.\n\nEarly benchmarks indicate data transmission energy per bit dropped by 89 percent compared to traditional copper interconnects, while bandwidth density surged to 2.4 terabits per square millimeter. The achievement eliminates the copper interconnect resistance bottleneck that has constrained deep neural network training clusters over the past half-decade, clearing the path toward exascale processing nodes that operate at ambient room temperatures.\n\nCommercial foundries have verified that the optical lithography process utilizes standard immersion tooling, allowing existing silicon fabrication plants to retool production lines with minimal capital expenditure.",
        "author": "K. Lindqvist",
        "date": "Today, 06:15 AM",
        "source": "Ars Technica",
        "section": "Technology & AI",
        "image": None,
    },
    {
        "title": "Open-Source Compilers Merge Auto-Vectorization Pipeline Across LLVM and GCC",
        "link": "https://news.ycombinator.com",
        "summary": "Contributors announce a unified autovectorizer targeting heterogeneous neural accelerators, reducing compile times and accelerating scientific code.",
        "content": "The global open-source compiler community has announced the merge of a unified autovectorization pipeline across LLVM and GCC compilers, achieving historic performance gains for scientific and mathematical computing workloads.\n\nBy leveraging polyhedral loop transformation algorithms, the new compiler passes automatically vectorize dense linear algebra and tensor math operations across heterogeneous CPU and GPU instruction sets without requiring manual SIMD intrinsics from application developers.\n\nBenchmark suites run on weather simulation, fluid dynamics, and astrophysical modeling codes reported speedups ranging from 3.2x to 7.8x out of the box, democratizing high-performance computing capabilities for research universities and independent laboratories worldwide.",
        "author": "Tech Dispatch",
        "date": "Today, 07:00 AM",
        "source": "Hacker News Top",
        "section": "Technology & AI",
        "image": None,
    },
    {
        "title": "Local Small Language Models Reach GPT-4 Class Reasoning on Edge Smartphones",
        "link": "https://www.theverge.com",
        "summary": "New 3-billion-parameter distilled architectures operate at 45 tokens per second directly on mobile NPU chips with sub-watt power consumption.",
        "content": "Artificial intelligence research laboratories have released a new generation of 3-billion-parameter quantized neural networks capable of matching prior generation frontier reasoning benchmarks while executing entirely on-device within mobile Neural Processing Units.\n\nThrough novel synthetic distillation techniques and multi-token speculative decoding, the models sustain generation velocities exceeding 45 tokens per second while consuming less than 850 milliwatts of battery power. This enables complex document summarization, voice-to-code synthesis, and real-time multi-lingual translation without transmitting sensitive personal user queries to remote cloud datacenters.\n\nHardware reviewers confirmed that the edge models function reliably in airplane mode without internet connectivity, underscoring a transformative architectural shift toward sovereign, private on-device edge intelligence.",
        "author": "Allison Johnson",
        "date": "Today, 07:45 AM",
        "source": "The Verge",
        "section": "Technology & AI",
        "image": None,
    },

    # --- 7. SPORTS & CRICKET ---
    {
        "title": "Border-Gavaskar Trophy: India Mounts Masterful Fightback in Perth Test",
        "link": "https://www.espncricinfo.com",
        "summary": "Pace spearhead Jasprit Bumrah claims five wickets while young batters exhibit composure to seize command on Day 3 of the series opener.",
        "content": "In a showcase of supreme fast bowling and unflinching batting temperament, the Indian cricket team wrested commanding control of the opening Border-Gavaskar Trophy Test match against Australia at the Optus Stadium in Perth.\n\nLeading from the front as stand-in captain, pace maestro Jasprit Bumrah delivered a vintage masterclass of seam and swing bowling, claiming five wickets for thirty runs to dismantle the Australian top order on a responsive, bounce-laden pitch. His incisive opening spell was complemented by disciplined line and length from Mohammed Siraj and debutant Harshit Rana.\n\nIn the second innings, India's top order consolidated the advantage with patient half-centuries, stretching the overall lead beyond 300 runs. Cricket commentators across the world praised the tourists' adaptability and tactical clarity in blunting Australia's formidable pace attack on their home turf.",
        "author": "Shashank Kishore, Cricinfo",
        "date": "Today, 08:30 AM",
        "source": "ESPNcricinfo",
        "section": "Sports & Cricket",
        "image": None,
    },
    {
        "title": "Grandmaster D Gukesh Prepares for Historic World Chess Championship Match",
        "link": "https://www.thehindu.com",
        "summary": "The 18-year-old prodigy fine-tunes theoretical novelties and psychological stamina ahead of the title showdown in Singapore.",
        "content": "Indian chess prodigy D Gukesh has commenced the final phase of intense physical and theoretical preparation ahead of his historic FIDE World Championship match against reigning champion Ding Liren in Singapore.\n\nAt eighteen years of age, Gukesh is the youngest challenger in the history of the classical world title, having earned his candidacy through an audacious and poised campaign at the Candidates Tournament in Toronto. His preparatory camp includes top international grandmaster seconds, high-intensity aerobic training, and computational evaluation of deep endgame novelties.\n\nChess aficionados in India and across the globe are anticipating an enthralling fourteen-game classical battle, which heralds a vibrant new era for the international game rooted in India's unmatched depth of teenage grandmasters.",
        "author": "Rakesh Rao",
        "date": "Today, 09:15 AM",
        "source": "The Hindu",
        "section": "Sports & Cricket",
        "image": None,
    },
    {
        "title": "Indian Women's Hockey Team Secures Asian Champions Trophy Title in Rajgir",
        "link": "https://timesofindia.indiatimes.com",
        "summary": "Clinical penalty corner conversions and resolute goalkeeping secure a memorable 1-0 triumph over China in front of roaring home fans.",
        "content": "The Indian women's hockey team clinched the prestigious Asian Champions Trophy title with a tenacious 1-0 victory over reigning Olympic silver-medalists China in a thrilling final played at the newly built Rajgir Hockey Stadium in Bihar.\n\nStriker Deepika proved to be the match-winner, deflecting a crisp penalty corner variation into the top corner of the net during the third quarter. Goalkeeper Savita Punia stood tall under relentless pressure in the dying minutes, orchestrating three crucial penalty corner saves to preserve the narrow lead.\n\nThe tournament triumph underlines the team's tactical maturation under new coaching staff and ignited euphoric celebrations among the capacity home crowd in Rajgir.",
        "author": "TOI Sports Desk",
        "date": "Today, 10:00 AM",
        "source": "Times of India",
        "section": "Sports & Cricket",
        "image": None,
    },

    # --- 8. ENTERTAINMENT & CINEMA ---
    {
        "title": "Indian Cinema Celebrates Global Recognition as Auteur Films Triumph at Venice and Cannes",
        "link": "https://indianexpress.com",
        "summary": "Independent Indian filmmakers capture top jury prizes with authentic regional storytelling that transcends linguistic and cultural frontiers.",
        "content": "Independent Indian cinema is enjoying an unprecedented golden run across premier international film festivals, with jury triumphs at Cannes, Venice, and Busan spotlighting the rich diversity of regional narratives.\n\nCritics have noted a decisive departure from predictable formulaic tropes toward authentic, nuanced explorations of human relationships, rural sociology, and contemporary urban anxieties. Filmmakers from Malayalam, Bengali, Marathi, and Tamil industries are leading this artistic renaissance, combining lyrical cinematography with deeply personal screenwriting.\n\nInternational distribution houses have responded by acquiring global streaming and theatrical rights, ensuring that nuanced regional Indian stories find receptive audiences in cinema halls from Paris to Tokyo.",
        "author": "Shubhra Gupta",
        "date": "Today, 08:20 AM",
        "source": "Indian Express",
        "section": "Entertainment & Cinema",
        "image": None,
    },
    {
        "title": "Classical Music Revival: Young Connoisseurs Flock to Historic Winter Concerts",
        "link": "https://www.thehindu.com",
        "summary": "Carnatic and Hindustani classical music festivals report unprecedented youth attendance aided by digital archives and intimate baithaks.",
        "content": "The annual winter music season has commenced across cultural centers in Chennai, Kolkata, and Varanasi, drawing unprecedented numbers of college students and young professionals to heritage sabhas and intimate morning baithaks.\n\nOrganizers attribute the revival to innovative digital outreach, where maestro artists share lecture-demonstrations and historical ragas on social platforms, demystifying complex microtonal nuances and rhythmic tala structures for newcomers.\n\nEminent vocalists noted that far from waning in an era of three-minute digital tracks, classical music's contemplative, meditative architecture provides a profound sanctuary of mindfulness for listeners seeking respite from sensory overload.",
        "author": "B. Sivakumar",
        "date": "Today, 09:30 AM",
        "source": "The Hindu",
        "section": "Entertainment & Cinema",
        "image": None,
    },
    {
        "title": "National Film Heritage Mission Restores 5,000 Rare Silent Era and Golden Age Classics",
        "link": "https://timesofindia.indiatimes.com",
        "summary": "4K digital scanning and frame-by-frame restoration salvage damaged celluloid reels of early Indian cinematic masterpieces.",
        "content": "The National Film Heritage Mission has announced the milestone restoration of more than 5,000 historic cinematic works, salvaging brittle nitrate and acetate reels of rare silent era films and early golden-age classics.\n\nRestoration labs in Pune employ specialized ultrasonic wash tanks, 4K wet-gate digital scanners, and AI-assisted frame-by-frame scratch removal to restore faded audio tracks and degraded picture contrast to pristine original fidelity.\n\nArchivists revealed plans to make the restored library accessible to university film departments and cultural societies through an open public digital portal, safeguarding India's visual heritage for generations to come.",
        "author": "Priya Gupta",
        "date": "Today, 10:10 AM",
        "source": "Times of India",
        "section": "Entertainment & Cinema",
        "image": None,
    },

    # --- 9. OPINION & EDITORIAL ---
    {
        "title": "Editorial: The Architecture of Attention in an Age of Ephemeral Streams",
        "link": "https://www.thehindu.com",
        "summary": "Why the deliberate discipline of broadsheet curation and contemplative reading remains an indispensable pillar of civic democracy.",
        "content": "In an era increasingly governed by algorithmic feeds engineered for impulsive dopamine triggers, the deliberate ritual of broadsheet journalism represents something far greater than aesthetic nostalgia: it is an act of intellectual sovereignty.\n\nWhen information is unbundled into disjointed, fifteen-second video snippets, public discourse loses the structural context required to parse nuanced socio-economic dilemmas. Issues of climate adaptation, sovereign monetary policy, or judicial jurisprudence cannot be reduced to viral slogans without forfeiting their essential truth.\n\nA broadsheet edition enforces an intentional pause. By presenting stories within a balanced visual hierarchy—where local welfare struggles share typographic parity with international scientific breakthroughs—the newspaper invites the citizen to synthesize rather than merely react. Reclaiming our shared civic sanity begins with reclaiming the time to read deeply, quietly, and completely.",
        "author": "The Editorial Board",
        "date": "Today, 06:00 AM",
        "source": "The Hindu",
        "section": "Opinion & Editorial",
        "image": None,
    },
    {
        "title": "Explained: How India's Digital Public Infrastructure Became a Global Template",
        "link": "https://indianexpress.com",
        "summary": "A deep analysis of the modular 'India Stack' philosophy that separates identity, payments, and data layers to prevent platform monopolies.",
        "content": "Over the past decade, India's conceptualization of Digital Public Infrastructure (DPI) has shifted from a domestic administrative convenience to an internationally recognized blueprint for open, interoperable governance.\n\nUnlike Western proprietary ecosystems dominated by private platform monopolies or authoritarian top-down surveillance architectures, the India Stack was founded upon modular, protocol-based public rails. Aadhaar provides identity without commercial gatekeepers; UPI enables payments without card-network tollbooths; and DigiLocker allows citizens to own their verified records.\n\nDeveloping nations across Africa, Latin America, and Southeast Asia are now actively adopting open-source implementations of these protocols through multilateral partnerships. By keeping the core transaction rails public while encouraging private innovation on top, India demonstrated that technology can empower the citizen without impoverishing the commons.",
        "author": "C. Raja Mohan",
        "date": "Today, 07:15 AM",
        "source": "Indian Express",
        "section": "Opinion & Editorial",
        "image": None,
    },
    {
        "title": "Column: The Green Transition Demands Manufacturing Depth, Not Just Slogans",
        "link": "https://www.business-standard.com",
        "summary": "Achieving true decarbonization requires establishing sovereign mineral refining, cathode chemistry, and precision metallurgical ecosystems.",
        "content": "It is tempting to measure climate progress purely by the megawatts of solar panels installed on rooftops or the number of electric scooters buzzing through metropolitan avenues. Yet true economic decarbonization will be won or lost in the unglamorous trenches of heavy industrial metallurgy, rare-earth chemical refining, and grid-scale transformer fabrication.\n\nWithout sovereign processing capacity for battery-grade lithium, graphite anodes, and high-efficiency electrical steel, a nation risks replacing dependence on foreign oil barrels with dependence on foreign battery packs. Industrial policy must therefore reward upstream processing depth and metallurgical research rather than superficial downstream assembly.\n\nThe coming decade offers a rare window to anchor high-value clean manufacturing clusters on domestic soil. Capital incentives must be aligned with long-term research consortia if we are to forge enduring industrial independence.",
        "author": "Nitin Desai",
        "date": "Today, 08:00 AM",
        "source": "Business Standard",
        "section": "Opinion & Editorial",
        "image": None,
    },

    # --- 10. SCIENCE & SPACE ---
    {
        "title": "ISRO Completes Key Propulsion Qualification Tests for Gaganyaan Human Spaceflight",
        "link": "https://www.thehindu.com",
        "summary": "The Liquid Propulsion Systems Centre successfully hot-tests the human-rated service module propulsion system in full mission flight profile.",
        "content": "The Indian Space Research Organisation (ISRO) has successfully concluded a rigorous sequence of hot-fire qualification tests for the Service Module Propulsion System of the flagship Gaganyaan human spaceflight mission at the Mahendragiri testing facility in Tamil Nadu.\n\nThe propulsion module, engineered to deliver attitude control, orbital maneuvering, and critical de-boost velocity for atmospheric re-entry, was fired under simulated vacuum conditions across multi-mode test envelopes. Data telemetry verified nominal combustion pressures, optimal fuel utilization, and smooth thrust vector gimbaling throughout the burn sequence.\n\nISRO mission directors confirmed that the success clears the path for the upcoming uncrewed orbital flight test featuring the 'Vyommitra' humanoid robot, scheduled ahead of the landmark inaugural crewed mission carrying Indian vyomnauts to low Earth orbit.",
        "author": "Surendra Singh",
        "date": "Today, 06:45 AM",
        "source": "The Hindu",
        "section": "Science & Space",
        "image": None,
    },
    {
        "title": "Deep Space Observatory Detects Water Vapor and Methane on Temperate Super-Earth",
        "link": "https://www.nature.com",
        "summary": "Spectrographic analysis of LHS-1140b reveals an atmosphere with chemical disequilibrium orbiting within a quiescent red dwarf's habitable zone.",
        "content": "Spectrographic analysis gathered by the orbiting Great Observatories array has confirmed unambiguous signatures of water vapor, atmospheric ozone, and carbon-cycle methane within the temperate atmosphere of LHS-1140b, a super-Earth rocky planet located thirty-eight light years distant in the constellation Cetus.\n\nThe planet orbits within the conservative habitable zone of a quiescent red dwarf star, receiving approximately forty percent of the stellar flux Earth receives from our Sun. Crucially, high-resolution transit transmission spectra indicate a dense, nitrogen-dominated atmosphere that has resisted stellar wind stripping over billions of years, creating conditions favorable for persistent liquid surface oceans.\n\nAstrobiologists caution that while the co-presence of methane and ozone represents a classic non-equilibrium chemical disequilibrium, abiotic geochemical photochemical mechanisms must still be rigorously modeled before definitive conclusions regarding biogenic activity can be declared.",
        "author": "Dr. Aris Thorne",
        "date": "Today, 07:30 AM",
        "source": "Nature News",
        "section": "Science & Space",
        "image": None,
    },
    {
        "title": "Indian Institute of Science Synthesizes Novel Room-Temperature Quantum Material",
        "link": "https://timesofindia.indiatimes.com",
        "summary": "Physicists create a 2D twisted topological insulator displaying dissipationless electron edge transport at room temperatures.",
        "content": "A team of condensed matter physicists at the Indian Institute of Science (IISc) in Bengaluru has synthesized an innovative two-dimensional twisted bilayer material that exhibits dissipationless topological electron conduction at room temperatures.\n\nBy twisting atomically thin layers of molybdenum ditelluride at a precise 'magic angle' of 1.1 degrees, the researchers induced strong electronic correlations that protect current-carrying edge channels against thermal scattering. This breakthrough bypasses the cryogenic liquid helium cooling historically required to observe quantum Hall phenomena.\n\nThe findings, published in leading physical review journals, unlock unprecedented possibilities for ultra-low-power quantum spintronic transistors, high-speed neural networks, and fault-tolerant quantum logic gates that function in ordinary ambient environments.",
        "author": "K. S. Jayaraman",
        "date": "Today, 08:15 AM",
        "source": "Times of India",
        "section": "Science & Space",
        "image": None,
    },

    # --- 11. WORLD AFFAIRS ---
    {
        "title": "Global Accord Reached on Sustainable Fusion and Continental Power Interconnects",
        "link": "https://feeds.bbci.co.uk",
        "summary": "Delegates from forty-two nations conclude landmark treaty pledging shared IP and infrastructure investments into magnetic confinement fusion.",
        "content": "Delegates from forty-two nations concluded a landmark ministerial summit in Vienna today, formally ratifying a joint multi-billion dollar treaty for continental grid modernization and pilot magnetic confinement fusion facilities.\n\nThe agreement establishes shared intellectual property covenants, enabling developing and industrial economies alike to construct high-temperature superconducting tokamak reactors over the coming decade. Treasury analysts and energy economists project that the initiative will permanently decouple industrial manufacturing growth from fossil fuel price volatility.\n\nIn addition to reactor funding, the treaty allocates emergency capital toward high-voltage direct current (HVDC) transmission lines stretching from the North Sea wind corridors to Southern European solar fields, ensuring cross-border energy sharing during seasonal peak demands.",
        "author": "Marcus Sterling, World Desk",
        "date": "Today, 06:15 AM",
        "source": "BBC World News",
        "section": "World Affairs",
        "image": None,
    },
    {
        "title": "United Nations Climate Conference Finalizes Loss and Damage Operational Facility",
        "link": "https://www.bloomberg.com",
        "summary": "Developing island nations secure binding initial capital disbursements to reconstruct sea walls and decentralized solar grids.",
        "content": "Negotiators at the United Nations climate plenary reached a historic breakthrough in the early hours of Wednesday, finalizing the operational charter and capital disbursement mechanisms for the international Loss and Damage Fund.\n\nThe accord secures an initial tranche of over $750 million in dedicated grant-based financing, prioritized for low-lying Pacific island nations and flood-vulnerable coastal regions grappling with acute sea-level rise and saltwater intrusion into freshwater aquifers.\n\nDelegates hailed the consensus as an essential restoration of multilateral faith, establishing clear, transparent metrics for climate vulnerability while insulating recipients from debt-trap conditionalities common in legacy international finance agreements.",
        "author": "Laura Millan, Bloomberg",
        "date": "Today, 07:45 AM",
        "source": "Bloomberg",
        "section": "World Affairs",
        "image": None,
    },
    {
        "title": "International Maritime Organization Mandates Net-Zero Marine Fuel Corridors",
        "link": "https://feeds.bbci.co.uk",
        "summary": "Global container shipping lines agree to phased adoption of green methanol and ammonia along primary Asia-Europe trade routes.",
        "content": "The International Maritime Organization (IMO) has approved a binding regulatory roadmap mandating the progressive adoption of zero-emission marine fuels across the world's commercial merchant fleet beginning in 2027.\n\nThe framework establishes designated 'Green Shipping Corridors' connecting mega-ports across East Asia, the Indian Ocean, and Western Europe, where commercial container carriers will receive discounted port tariffs and priority berthing upon demonstrating certified green methanol or bio-ammonia bunker fuel usage.\n\nMaritime logistics operators stated that the decisive regulatory signal will stimulate immediate commercial capital outlays for dual-fuel vessel retrofits and shore-side green hydrogen production hubs along key maritime straits.",
        "author": "James Landale",
        "date": "Today, 08:50 AM",
        "source": "BBC World News",
        "section": "World Affairs",
        "image": None,
    },

    # --- 12. CULTURE & BOOKS ---
    {
        "title": "The Art of Slow Reading in an Era of Infinite Frictionless Streams",
        "link": "https://aeon.co",
        "summary": "An inquiry into why typography, intentional pauses, and physical broadsheets foster deep synthesis in human contemplation.",
        "content": "In an age dominated by frictionless algorithmic feeds and ephemeral push notifications, readers across the globe are staging a quiet but deliberate return to slow, reflective prose and broadsheet composition.\n\nCognitive psychologists have long documented how the tactile pacing of multi-column print—the intentional pause required to fold a page, the generous margins, the deliberate hierarchy of headlines—engages the brain's spatial memory in ways that continuous vertical smartphone scrolling actively degrades.\n\nWhen we read a broadsheet, we are not passive consumers buffeted by click-driven outrage. We become participants in an intellectual civic ritual. By curating our daily intake through structured, thoughtful editions, we reclaim control over our attention, our reflective judgment, and our cultural sanity.",
        "author": "Julian H. Croft",
        "date": "Today, 07:00 AM",
        "source": "Aeon Magazine",
        "section": "Culture & Books",
        "image": None,
    },
    {
        "title": "Preserving India's Ancient Palm-Leaf Manuscripts Through Multispectral AI Imaging",
        "link": "https://www.thehindu.com",
        "summary": "Sanskrit and Dravidian scholars deploy narrow-band infrared illumination to recover centuries-old mathematical and astronomical treatises.",
        "content": "Archivists and philologists across southern Indian oriental research libraries have embarked on a massive digital conservation initiative, employing multispectral imaging and AI-assisted ink contrast enhancement to transcribe thousands of brittle palm-leaf manuscripts.\n\nMany of the fragile folios, dating from the tenth to the seventeenth centuries, contain rare treatises on the Kerala School of Astronomy and Mathematics, Ayurvedic pharmacopeia, and classical poetic poetics that have remained unpublished due to severe insect damage and faded organic inks.\n\nThe digital scans, rendered at resolutions exceeding 1,200 dots per inch under non-damaging cold LED illumination, will be cataloged in an open-access international repository, making rare Indian scientific treatises freely available to global computational historians.",
        "author": "V. Sriram",
        "date": "Today, 08:30 AM",
        "source": "The Hindu",
        "section": "Culture & Books",
        "image": None,
    },
    {
        "title": "Literary Review: Why the Modern Essay is Experiencing an Extraordinary Global Renaissance",
        "link": "https://scroll.in",
        "summary": "Long-form narrative essays and independent literary journals witness a resurgence among readers seeking depth over bite-sized summaries.",
        "content": "Contrary to dire prognostications declaring the demise of sustained reading, the personal and political essay is experiencing an extraordinary creative and commercial renaissance across independent literary magazines and quarterly journals.\n\nFrom Delhi to Dublin, essayists are pushing the boundaries of the form, weaving memoir, archival history, and investigative reporting into singular literary tapestries. Readers exhausted by algorithmic homogeneity are actively subscribing to independent literary quarterlies that treat prose as an artisanal art.\n\nPublishing houses report that collections of thematic essays are commanding prominent display space in independent bookstores, proving that the human appetite for deep, idiosyncratic authorial voices remains as vigorous as ever.",
        "author": "Ananya Mukherjee",
        "date": "Today, 09:15 AM",
        "source": "Scroll.in",
        "section": "Culture & Books",
        "image": None,
    },
]


def seed_database(force_edition=True):
    """Initializes SQLite database, populates default sources and generates an inaugural edition."""
    init_db()
    existing_sources = get_sources()
    if not existing_sources:
        print(f"Seeding {len(PRESET_SOURCES)} default sources across 12 categories...")
        for src in PRESET_SOURCES:
            add_source(
                name=src["name"],
                url=src["url"],
                section=src["section"],
                enabled=src["enabled"],
                max_items=src["max_items"],
            )
    else:
        print(f"Database has {len(existing_sources)} existing sources.")

    existing_editions = get_editions(limit=1)
    if not existing_editions or force_edition:
        print(f"Formatting expansive inaugural edition with {len(SAMPLE_ARTICLES)} articles across 12 categories...")
        config = get_config()
        edition_payload = format_newspaper_edition(SAMPLE_ARTICLES, config)
        save_edition(edition_payload)
        print(f"Inaugural edition saved successfully with {len(edition_payload.get('sections', {}))} active sections!")


if __name__ == "__main__":
    seed_database(force_edition=True)
    print("Database seeding & inaugural edition generation complete.")
