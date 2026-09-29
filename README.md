# 🛰️ Sentinel // Advanced Telegram OSINT & Finder Bot (50+ Features)

![Python](https://img.shields.io/badge/Python-3.10%20--%203.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.30+-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-MTProto-0088cc?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Async%20aiosqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Sentinel** is an enterprise-grade, asynchronous Telegram bot built with **Python**, **Aiogram 3**, and **Telethon MTProto**. It provides deep **User Intelligence**, **Public Channel & Group Discovery**, **Forward Header Forensics**, **Data Center (DC) Mapping**, and **50+ Real, Tested Features** with a **Cyberpunk / Dark-Tech UI/UX**.

> **100% Real Telegram Data Guarantee:** All discovery queries, member counters, profile avatars, verification checks, and description parsing fetch **actual, live data directly from Telegram's servers** (via official Bot API, MTProto protocol, and live web preview endpoints).

---

## 📑 Table of Contents
- [Architecture & Real Data Pipeline](#-architecture--real-data-pipeline)
- [Complete 50+ Features Catalog](#-complete-50-features-catalog)
- [Visual Themes & UI/UX](#-visual-themes--uiux)
- [Project Directory Layout](#-project-directory-layout)
- [Installation & Setup](#-installation--setup)
- [Configuration (.env)](#-configuration-env)
- [Bot Commands & Inline Mode](#-bot-commands--inline-mode)
- [Testing & Verification](#-testing--verification)

---

## ⚡ Architecture & Real Data Pipeline

```
                              [ User Query ]
                                    │
                                    ▼
                         [ Sentinel Router Engine ]
                                    │
    ┌───────────────────────────────┼──────────────────────────────┐
    │                               │                              │
    ▼                               ▼                              ▼
[ Official Bot API ]      [ Telethon MTProto ]          [ Live Telegram Preview ]
• bot.get_chat()          • contacts.SearchRequest      • https://t.me/s/{channel}
• get_chat_member_count   • GetFullUserRequest          • Real member & subscriber count
• get_user_profile_photos • GetFullChannelRequest       • Live online counts
• decode_file_id_dc()     • Global username resolver    • Official verified checkmark
    │                               │                              │
    └───────────────────────────────┼──────────────────────────────┘
                                    ▼
                       [ Unified Entity Resolver ]
                                    │
    ┌───────────────────────────────┼──────────────────────────────┐
    │                               │                              │
    ▼                               ▼                              ▼
[ Regression Age Engine ]    [ OSINT Text Auditor ]     [ Pillow / ReportLab Export ]
• Chronological Epochs       • Email & link extraction  • High-res Cyberpunk ID Card
• Piecewise interpolation    • Phishing threat scoring  • OSINT PDF Dossier
• DC1 to DC5 Mapping         • Script classification    • Custom Styled QR Code
```

---

## 📋 Complete 50+ Features Catalog

### 1. User Forensics & Profile Intelligence (1 – 12)
1. **Direct User Lookup by @Username:** Live extraction of profile name, username, bio, and numeric ID.
2. **Lookup by Numeric Telegram ID:** Queries profile data even when user has changed their username.
3. **Forward Header Forensics:** Extracts sender User ID, original date, message ID, and detects hidden sender privacy.
4. **Data Center (DC) Identifier:** Identifies DC1 (Miami), DC2 (Amsterdam), DC3 (Miami), DC4 (Amsterdam), DC5 (Singapore).
5. **Account Registration Date Estimator:** Mathematical piecewise regression over Telegram's 64-bit ID space from 2013 to 2026.
6. **Telegram Premium Detector:** Detects active Telegram Premium status and custom emoji badges.
7. **Official Scam & Fake Flag Detection:** Identifies accounts marked with Telegram official fraud warnings.
8. **Bot Capability & Permission Check:** Analyzes bot entities, group join rights, and inline query support.
9. **Official Verified Badge Check:** Identifies verified organizations, celebrities, and public figures.
10. **Profile Photo Downloader & Inspector:** Downloads full-resolution avatar images directly from Telegram CDN.
11. **Profile Photo History & Count:** Inspects total avatar history count and server node.
12. **Identity & Alias Change History:** Logs past seen names and usernames into SQLite to detect account rebranding.

### 2. Channel & Group Discovery Engine (13 – 26)
13. **Channel Live Intelligence:** Real-time subscriber count, channel title, description, and custom invite links.
14. **Supergroup / Group Inspector:** Live member count, active online count, slowmode intervals, and forum status.
15. **Invite Link Analyzer:** Resolves `t.me/+hash` and `t.me/joinchat/...` invite structures.
16. **Live Telegram Keyword Search Engine:** Searches live Telegram channels & groups across global index for any keyword.
17. **Entity Type Classifier:** Automatically distinguishes between Private User, Bot, Channel, Supergroup, and Forum.
18. **Chat Administrator Matrix:** Lists administrators, custom titles, and admin permissions.
19. **Chat Permissions Matrix:** Displays permissions for messages, media, polls, link embedding, and pins.
20. **Slowmode & Anti-Spam Inspector:** Detects if slowmode delay is active and interval duration.
21. **Forum Topics Inspector:** Identifies whether a group has forum topic mode enabled.
22. **Linked Chat Finder (Channel ↔ Discussion):** Detects linked discussion supergroups for broadcast channels.
23. **Public Username Availability Checker:** Validates format and checks if a handle is active or available.
24. **Fragment NFT / Collectible Inspector:** Inspects usernames and anonymous numbers on Fragment.com.
25. **Post Link Synthesizer:** Generates direct links to specific message IDs (`t.me/c/...`).
26. **Platform Restriction Auditor:** Inspects platform-specific content restrictions (iOS/Android/regional).

### 3. Forensic Exports, Utilities & OSINT (27 – 38)
27. **Permanent User ID Link Generator:** Generates `tg://user?id=...` permanent protocol links.
28. **Telegram Deep Links Suite:** Generates `tg://resolve?domain=...`, `t.me/share/url`, and direct app protocols.
29. **Digital Graphic ID Card (PNG Image):** Renders high-resolution 1080x600 dark cyberpunk identity card with avatar and badges.
30. **Interactive Styled QR Code Generator:** Generates branded QR code image with rounded modules for any profile.
31. **OSINT Dossier PDF Generator (ReportLab):** Generates multi-page, formatted PDF intelligence report ready to share.
32. **Raw JSON Dumper:** Provides complete raw Telegram API Update / Chat JSON structure for developers.
33. **vCard (.vcf) Contact Exporter:** Generates virtual contact card file for 1-tap phonebook import.
34. **Bio Word & Link Extractor:** Regex extractor for URLs, domains, email addresses, and @mentions.
35. **Language & Script Detector:** Identifies Cyrillic, Arabic, Devanagari, East Asian (CJK), and Latin scripts.
36. **Bot Token Checker & Validator:** Validates bot tokens via Bot API, testing `getMe` and permissions.
37. **Webhook Status Inspector:** Inspects webhook URL, pending update count, and last error timestamp.
38. **Phishing & Scam Text Auditor:** Evaluates investment scam triggers, pump & dump signals, and suspicious URLs.

### 4. Curated Directory & Community Discovery (39 – 44)
39. **Curated 12-Topic Directory:** Pre-indexed database across Technology, AI/ML, Coding, CyberSec, Crypto, News, Design, etc.
40. **Interactive Pagination Controls:** Multi-page inline keyboard navigator (Prev, Next, Page X/Y).
41. **Community Roulette (Discover Random):** 1-click random discovery of interesting verified communities.
42. **Community Suggestion / Submission System:** Allows users to submit new channels/groups for inclusion.
43. **Admin Moderation Approval Queue:** Admins can approve or reject submitted communities with 1 click.
44. **Trending & Top Channels Leaderboard:** Displays top-rated channels in the catalog.

### 5. Bot Management, UX & Security (45 – 53)
45. **Favorites & Bookmarks System:** Save channels, groups, or users to personal favorites for quick access.
46. **Search History Log:** View recent lookups with 1-click re-query buttons and clear history function.
47. **Multiple Export Formats:** One-click export to PNG ID Card, PDF Dossier, QR Code, VCF, or JSON.
48. **Customizable Themes:** Switch between **Cyberpunk Neo**, **Minimalist Clean**, and **Detailed OSINT**.
49. **Multi-Language Support (i18n):** Native support for English, Spanish, Hindi, Russian, and Arabic.
50. **Anti-Flood & Rate Limiting:** Sliding-window rate limiter prevents spamming and Telegram API 429 bans.
51. **Admin Broadcast System:** Dispatch formatted announcements to all bot users with delivery metrics.
52. **Admin Real-time Analytics:** Database statistics, total users, query volume, and memory usage.
53. **Inline Query Mode:** Search and share entity cards in any chat via `@YourBot <query>`.

---

## 🎨 Visual Themes & UI/UX

### 1. Cyberpunk Neo (Default)
Neon accents, ASCII dividers, status badges (`PREMIUM`, `VERIFIED`, `DC2`), and copyable monospace IDs.

### 2. Minimalist Clean
Concise, elegant, whitespace-focused layout providing essential attributes without visual noise.

### 3. Detailed OSINT
Forensic dossier format with server node IPs, registration epoch regression confidence, script analysis, and threat scores.

---

## 📁 Project Directory Layout

```
UserInfoBotTelegram/
├── config.py                 # Configuration loader (dotenv, defaults, paths)
├── database.py               # Async SQLite database (Users, History, Favorites, Identity)
├── main.py                   # Central launcher, router & middleware registration
├── tests_verify.py           # Automated test suite verifying all 8 core subsystems
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Active environment configuration
├── core/
│   ├── dc_resolver.py        # Telegram Data Center (DC1 to DC5) mapping
│   ├── reg_date_estimator.py # Chronological piecewise regression for account age
│   ├── card_generator.py     # Pillow high-res ID Card & Banner generator
│   ├── qr_generator.py       # Branded QR code generator
│   ├── pdf_generator.py      # ReportLab PDF dossier generator
│   ├── vcard_generator.py    # VCard (.vcf) contact card generator
│   ├── osint_analyzer.py     # Regex extractor, script detector, scam auditor
│   ├── directory_data.py     # Curated 12-category communities catalog
│   ├── bot_checker.py        # Bot token & webhook inspector
│   ├── telethon_engine.py    # Optional Telethon MTProto client engine
│   └── telegram_discovery.py # Live Telegram scraper & global search engine
├── ui/
│   ├── keyboards.py          # Interactive inline keyboards & pagination
│   ├── formatters.py         # Cyberpunk, Minimalist & OSINT HTML report formats
│   └── locales.py            # Multi-language string catalogs (EN, ES, HI, RU, AR)
├── middlewares/
│   ├── throttling.py         # Anti-flood sliding-window rate limiter
│   └── tracking.py           # User session & query tracking middleware
├── handlers/
│   ├── start.py              # /start, /help, /features & main navigation
│   ├── user_info.py          # User lookup (by @username, ID, contact, reply)
│   ├── channel_finder.py     # Channel search & statistics
│   ├── group_finder.py       # Group search & permissions matrix
│   ├── forward_inspector.py  # Forward header analyzer (hidden senders)
│   ├── directory.py          # Curated directory browser with pagination
│   ├── tools.py              # OSINT & Dev tools (Bot check, DC map, QR, Fragment)
│   ├── export.py             # Export handlers (ID Card, PDF, QR, VCF, JSON)
│   ├── favorites.py          # Bookmarks management
│   ├── history.py            # Personal search history
│   ├── submission.py         # Community submission queue
│   ├── settings.py           # Theme & language switcher
│   ├── admin.py              # Control panel, broadcast, and metrics
│   └── inline_mode.py        # In-chat inline query handler
└── data/
    ├── bot_database.sqlite3  # SQLite database file
    ├── avatars/              # Cached profile avatars
    └── exports/              # Generated ID cards, PDFs, and QR codes
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone / Open Directory
```bash
cd c:\Users\NaushadAlam\Desktop\UserInfoBotTelegram
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Edit the `.env` file and insert your bot token:
```env
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
ADMIN_IDS=123456789
```

*(Optional)* To unlock deep MTProto global search and raw channel member inspection, get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org):
```env
API_ID=12345678
API_HASH=abcdef0123456789abcdef0123456789
```

### 5. Run Verification Diagnostics
Verify that all subsystems (database, Pillow ID cards, PDF dossiers, and live Telegram scraping) pass:
```bash
python tests_verify.py
```

### 6. Launch the Bot
```bash
python main.py
```

---

## 💬 Bot Commands & Inline Mode

| Command | Description |
|---|---|
| `/start` | Launch main interactive dashboard |
| `/id` | View your own profile card and numeric ID |
| `/info <@user or ID>` | Inspect any public user, channel, or group |
| `/channel <keyword>` | Search and discover public Telegram channels |
| `/group <keyword>` | Search and discover active public supergroups |
| `/directory` | Browse curated 12-category community catalog |
| `/tools` | Access Bot token checker, DC map, QR tool, etc. |
| `/token <bot_token>` | Test and validate a Telegram Bot Token & Webhook |
| `/fragment <handle>` | Check username auction and collectible status |
| `/qr <url or text>` | Generate a custom Telegram-styled QR code |
| `/audit <text>` | Scan text for phishing and investment scam triggers |
| `/favorites` | View and manage saved bookmarks |
| `/history` | View recent search history with 1-click re-query |
| `/settings` | Switch language (EN, ES, HI, RU, AR) or theme |
| `/features` | View complete 50+ features audit list |
| `/help` | Detailed operator user guide |
| `/admin` | Administrative panel & metrics (Admins only) |
| `/broadcast <msg>` | Global announcement dispatch (Admins only) |

### Inline Query Usage:
In any chat or channel, simply type:
```
@YourBot durov
@YourBot python
@YourBot crypto
```
Select any live preview card to share comprehensive statistics directly into the conversation!

---

## 🛡️ License & Credits
Developed with modern async Python standards. All public data is retrieved in compliance with official Telegram API specifications and public web protocols.
