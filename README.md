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

```
├── backend/
│   ├── api.py              # Flask REST API
│   ├── database.py         # SQLite schema & operations
│   ├── scraper.py          # Selenium Google Maps scraper
│   ├── ai_service.py       # AI providers (Groq, Gemini) with fallbacks
│   └── place_identity.py   # Canonical Google Maps identity resolution
│
├── frontend/
│   ├── index.html          # Single-page application
│   └── js/
│       ├── app.js          # Main app router
│       └── components/     # Dashboard, Competitors, Posts, Analytics, Ideas
│
└── database.db             # SQLite database (auto-created)
```

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

## Quick Start

### Prerequisites
- Python 3.9+
- Chrome/Chromium (for Selenium)
- Node.js (optional, for frontend dev server)

### Installation

```bash
# Clone and enter project
cd mapcompete

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your API keys:
# GROQ_API_KEY=your_groq_key
# GEMINI_API_KEY=your_gemini_key

# Start backend API (port 5000)
cd backend
python api.py

# Start frontend (port 3000)
cd ../frontend
python -m http.server 3000
```

### Access
- Frontend: http://localhost:3000
- API: http://localhost:5000
- Health check: http://localhost:5000/api/health

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

## Database Schema (Key Tables)

| Table | Purpose |
|-------|---------|
| `projects` | Project metadata, primary business |
| `places` | Canonical Google Maps places |
| `project_places` | Project ↔ Place relationships (role: primary/competitor) |
| `competitors` | Project-specific competitor tracking |
| `posts` | Scraped Google Maps posts/updates |
| `scraping_logs` | Persistent scraping run records |
| `generated_ideas` | AI-generated content ideas |
| `post_competitors` | Many-to-many post ↔ competitor |

## AI Providers

- **Groq** (primary) - llama-3.1-8b-instant, llama-3.3-70b-versatile
- **Gemini** (fallback) - gemini-1.5-flash, gemini-1.5-pro
- **Fallback** - Rule-based analysis when no API keys available

## Environment Variables

```env
# Required for AI features
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional
FLASK_ENV=development
FLASK_DEBUG=1
```

## Testing

```bash
# Run frontend UI verification
python verify_frontend_ui.py

# Test API endpoints
cd backend
python -c "
import sys; sys.path.insert(0, '.')
from api import app
with app.test_client() as c:
    print(c.get('/api/health').get_json())
"
```

## Project Structure

```
mapcompete/
├── .gitignore
├── README.md
├── requirements.txt
├── .env.example
├── backend/
│   ├── api.py
│   ├── database.py
│   ├── scraper.py
│   ├── ai_service.py
│   ├── place_identity.py
│   └── __init__.py
├── frontend/
│   ├── index.html
│   ├── js/
│   │   ├── app.js
│   │   └── components/
│   │       ├── dashboard.js
│   │       ├── competitors.js
│   │       ├── posts.js
│   │       ├── analytics.js
│   │       ├── ideas.js
│   │       └── api.js
│   └── css/
│       └── (embedded in index.html)
└── database.db
```

## License

Proprietary - Internal Use Only