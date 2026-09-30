# MapCompete - Google Maps Competitor Intelligence Platform

An end-to-end competitive intelligence platform for monitoring Google Maps business updates, analyzing competitor content with AI, and generating high-performing Google Maps posts.

## Overview

MapCompete automates the full pipeline from competitor discovery to content generation:

1. **Project & Competitor Management** - Create projects, define primary business, track competitors
2. **Google Maps Discovery** - Search and resolve real Google Maps places with canonical identity
3. **Updates Scraping** - Extract Google Maps Updates/Posts with 1-year (first scrape) / 6-month (incremental) windows
4. **Persistent Storage** - Canonical place identity, project relationships, posts, scraping logs
5. **AI Analysis** - Deep competitor intelligence: topics, keywords, content types, CTAs, offers, frequency, patterns, gaps, trends
6. **Content Generation** - AI-powered Google Maps update ideas and complete posts with keywords, CTAs, image concepts
7. **Dashboard & Analytics** - Real-time metrics, charts, geographic map, source explorer, market gaps

## Architecture

Production (target):

```
Vercel (frontend, static + /api rewrite)
   └──> Render Web Service (Flask + Gunicorn + Selenium/Chromium, Docker)
            └──> MongoDB Atlas (all application data)
```

```
├── backend/
│   ├── api.py              # Flask REST API (46 endpoints, gunicorn-ready)
│   ├── database.py         # MongoDB (PyMongo) persistence layer - same API
│   │                       #   as the old SQLite DatabaseManager
│   ├── scraper.py          # Selenium Google Maps scraper (on-demand only)
│   ├── ai_service.py       # AI providers (Groq, Gemini) with fallbacks
│   └── place_identity.py   # Canonical Google Maps identity resolution
│
├── frontend/
│   ├── index.html          # Single-page application
│   ├── vercel.json         # /api/* rewrite -> Render backend
│   └── js/
│       ├── app.js          # Main app router
│       └── components/     # Dashboard, Competitors, Posts, Analytics, Ideas
│
├── docker-compose.yml      # optional local full-stack run
├── render.yaml             # Render blueprint (Docker web service)
└── DEPLOYMENT.md           # step-by-step Vercel + Render + Atlas guide
```

There is **no local database file**: MongoDB Atlas is the only store, and a
fresh deployment starts with an empty database (no seed/demo data).

## Key Features

### Canonical Place Identity
- Every business resolves to one canonical `place` record keyed by Google Maps identity (hex pair, place_id, CID, kgmid)
- Projects link to places via `project_places` (primary business + competitors)
- Deduplication across projects using strongest available identity

### Smart Scraping
- **First scrape**: 365-day window, continuous scrolling until 1-year cutoff
- **Incremental**: 180-day window, only new posts inserted
- Deduplication via content hash (URL + text + date + competitor)
- Status handling: `SUCCESS`, `NO_POSTS`, `CAPTCHA_REQUIRED`, `TIMEOUT`, `FAILED`

### AI Competitive Intelligence
- **Topics & Sub-topics** with competitor mapping
- **Content Types**: Offer/Promo, New Arrival, Educational, Event
- **CTA Analysis** with effectiveness rating
- **Offer/Promotion Patterns** with examples
- **Competitor Publishing Patterns** per competitor
- **Gaps & Opportunities** with impact assessment
- **Unique Insights** with evidence + actionable recommendations

### Content Generation
- **Ideas**: Multiple unique Google Maps update ideas with keywords, CTA, image concept
- **Complete Update**: Ready-to-post text, keywords, CTA, image concept, suggested posting time
- **Duplicate Prevention** against existing generated ideas

## Quick Start (local development)

### Prerequisites
- Python 3.11+
- A **MongoDB Atlas** cluster (free M0) and its `mongodb+srv://` URI
- Chrome/Chromium (for Selenium; on Windows a local Chrome is auto-detected)
- Node.js (optional, for frontend dev server)

### Installation

```bash
# Clone and enter project
cd mapcompete

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies (includes pymongo)
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set MONGODB_URI (Atlas SRV string) and GROQ_API_KEY at minimum
```

### Run

```bash
# Backend (API on http://localhost:10000 by default, PORT is configurable)
python backend/api.py

# Frontend — recommended: serves frontend/ and proxies /api/* to a working
# backend (no CORS, no port guessing, works even if Atlas blocks this machine)
python serve_local.py
# -> open http://localhost:3000

# or any static server; the page then auto-detects the local API itself
python -m http.server 3000 --directory frontend
```

Optional full stack with Docker (backend + nginx frontend):

```bash
docker compose up --build   # API http://localhost:5000 (proxied), frontend :3000
```

### Access
- Frontend: http://localhost:3000
- API: http://localhost:10000 (or :5000 through the Docker proxy)
- Health check: http://localhost:10000/api/health

The frontend resolves the API automatically — `/api` (Vercel rewrite → Render)
in production, and the first healthy local backend on localhost. The browser
console prints the chosen URL as `[MapCompete] API: <url>`. Verify the whole
wiring with `python verify_deployment.py --local`.

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project
- `GET /api/projects/<id>` - Get project with primary business
- `GET /api/projects/<id>/places` - Get project's canonical places

### Competitors
- `GET /api/projects/<id>/competitors` - List project competitors
- `POST /api/projects/<id>/competitors` - Add competitor (with verification)
- `PUT /api/competitors/<id>` - Update competitor
- `DELETE /api/competitors/<id>` - Remove from project

### Discovery
- `POST /api/projects/<id>/discover-competitors` - Discover competitors
- `POST /api/places/search` - Search places near location
- `POST /api/places/resolve` - Resolve place identity
- `POST /api/competitors/verify` - Verify competitor before adding

### Scraping
- `POST /api/projects/<id>/scrape` - Scrape all project competitors
- `POST /api/competitors/<id>/scrape` - Scrape single competitor
- `GET /api/projects/<id>/scraping-logs` - Get scraping history

### Posts & Analytics
- `GET /api/posts` - Get posts (with filters)
- `GET /api/projects/<id>/analyze` - Run AI analysis
- `GET /api/projects/<id>/analytics/topics` - Topic frequency
- `GET /api/projects/<id>/analytics/keywords` - Keyword frequency
- `GET /api/projects/<id>/scraping-logs` - Scraping history

### AI & Content Generation
- `POST /api/projects/<id>/analyze` - Run AI competitive analysis
- `POST /api/projects/<id>/ideas` - Generate content ideas
- `POST /api/projects/<id>/complete-update` - Generate complete update
- `GET /api/projects/<id>/generated-ideas` - List generated ideas

## Database Collections (MongoDB Atlas)

| Collection | Purpose |
|------------|---------|
| `projects` | Project metadata, primary business |
| `places` | Canonical Google Maps places (unique `place_key`) |
| `competitors` | Project-specific competitor tracking |
| `posts` | Scraped Google Maps posts/updates (unique `content_hash`) |
| `post_competitors` | Post ↔ competitor share links (dedup across projects) |
| `reviews` | Scraped Google Maps reviews (unique content hash) |
| `keywords` | Project keywords |
| `generated_ideas` | AI-generated content ideas |
| `scraping_logs` | Persistent scraping run records |
| `counters` | Atomic numeric-id allocation (application-level `id`s) |

Indexes are created idempotently at startup. `project_places` from the old
schema is derived on the fly (competitors with a `place_id`).

## AI Providers

- **Groq** (primary) - llama-3.1-8b-instant, llama-3.3-70b-versatile
- **Gemini** (fallback) - gemini-1.5-flash, gemini-1.5-pro
- **Fallback** - Rule-based analysis when no API keys available

## Environment Variables

```env
# Required - MongoDB Atlas connection (never commit the real value)
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/
MONGODB_DATABASE=competitor_intelligence

# Required for AI features
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Server
PORT=10000                     # Render injects its own $PORT
CORS_ORIGINS=*                 # production: https://your-app.vercel.app

# Optional
FLASK_ENV=development
```

## Testing

```bash
# Offline unit tests for the MongoDB persistence layer (in-memory mongomock)
pip install mongomock
python backend/test_database_mongo.py

# Flask API contract tests (in-memory mongomock, no server needed)
python backend/test_api_mongomock.py

# Live Atlas connectivity check (needs MONGODB_URI in .env) - the ONE
# environment-dependent test
python backend/test_mongodb.py

# Full frontend UI verification (needs a running backend + Atlas)
python verify_frontend_ui.py
```

## Project Structure

```
mapcompete/
├── .gitignore
├── README.md
├── DEPLOYMENT.md            # Vercel + Render + MongoDB Atlas guide
├── render.yaml              # Render blueprint
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── requirements.txt     # includes pymongo
│   ├── api.py
│   ├── database.py          # MongoDB persistence layer
│   ├── scraper.py
│   ├── ai_service.py
│   ├── place_identity.py
│   ├── Dockerfile.backend
│   ├── docker-entrypoint.sh
│   ├── test_database_mongo.py   # offline unit tests (mongomock)
│   ├── test_api_mongomock.py    # API contract tests (mongomock)
│   └── test_mongodb.py          # live Atlas connectivity check
└── frontend/
    ├── index.html
    ├── vercel.json          # /api/* -> Render rewrite
    ├── nginx.conf
    └── js/
        ├── app.js
        └── components/
            ├── dashboard.js
            ├── competitors.js
            ├── posts.js
            ├── analytics.js
            ├── ideas.js
            └── api.js
```

## License

Proprietary - Internal Use Only