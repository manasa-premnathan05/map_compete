# MapCompete - Google Maps Competitor Intelligence Tool

A web-based competitor intelligence tool focused on Google Maps Updates. The system collects Google Maps update/post data from competitor business profiles, stores the data locally, analyzes what competitors are publishing, identifies recurring topics and trends, and uses the collected repository to generate new Google Maps update ideas and complete draft posts.

## Features

- **Project Management**: Create and manage multiple projects
- **Competitor Tracking**: Manually add and manage competitor businesses
- **Keyword Management**: Add search keywords for discovery
- **Web Scraping**: Selenium-based scraper for Google Maps posts
- **Duplicate Detection**: Prevents collecting the same posts multiple times
- **AI Analysis**: Uses Gemini and Grok AI to analyze competitor posts
- **Content Generation**: Generate content ideas and complete Google Maps updates
- **Analytics**: View topic frequency, keyword usage, and competitor activity
- **Responsive Design**: Works on desktop and mobile devices
- **CAPTCHA Handling**: Gracefully handles verification challenges
- **Demo Data**: Pre-loaded dataset for immediate evaluation

## Technology Stack

### Backend
- Python 3.11
- Flask REST API
- SQLite Database
- Selenium WebDriver for scraping
- Gemini AI & Grok AI for analysis and generation

### Frontend
- HTML5
- Tailwind CSS (via CDN)
- Vanilla JavaScript (no frameworks)
- Playfair Display & Space Mono fonts

### DevOps
- Docker & Docker Compose
- Nginx for frontend serving
- Gunicorn for backend serving

## Installation

### Prerequisites
- Docker and Docker Compose
- Git

### Quick Start (Docker)
1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your API keys
3. Run `docker-compose up --build`
4. Access the application at `http://localhost:3000`

### Manual Installation
1. Install Python 3.11+ and Node.js (for TailwindCSS build, if desired)
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Set up environment variables in `.env` file
4. Start the backend: `python backend/api.py`
5. Serve the frontend (using any static file server) or open `frontend/index.html` directly

## Usage

1. **Create a Project**: Enter your business name and profile information
2. **Add Competitors**: Manually add competitor businesses with their Google Maps URLs
3. **Add Keywords** (Optional): Add search terms related to your business
4. **Start Scraping**: Begin collecting competitor Google Maps posts
5. **View Results**: Browse collected posts, analyze trends, and generate content ideas
6. **Generate Content**: Create new Google Maps update ideas based on competitor analysis

## API Endpoints

### Projects
- `GET /api/projects` - Get all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/<id>` - Get specific project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Competitors
- `GET /api/projects/<id>/competitors` - Get competitors for project
- `POST /api/projects/<id>/competitors` - Add competitor
- `PUT /api/competitors/<id>` - Update competitor
- `DELETE /api/competitors/<id>` - Delete competitor

### Keywords
- `GET /api/projects/<id>/keywords` - Get keywords for project
- `POST /api/projects/<id>/keywords` - Add keyword
- `DELETE /api/keywords/<id>` - Delete keyword

### Posts
- `GET /api/posts` - Get posts (with filtering options)
- `GET /api/posts/<id>` - Get specific post

### Scraping
- `POST /api/projects/<id>/scrape` - Start scraping for project
- `GET /api/projects/<id>/scraping-logs` - Get scraping logs

### AI Analysis
- `POST /api/projects/<id>/analyze` - Analyze project posts
- `POST /api/projects/<id>/ideas` - Generate content ideas
- `POST /api/projects/<id>/complete-update` - Generate complete update

### Generated Ideas
- `GET /api/projects/<id>/generated-ideas` - Get generated ideas
- `POST /api/generated-ideas/<id>/use` - Mark idea as used

### Analytics
- `GET /api/projects/<id>/analytics/topics` - Get topic frequency
- `GET /api/projects/<id>/analytics/keywords` - Get keyword frequency

## Design System

### Color Palette
- Background: `#FFFFFF` (Pure White)
- Primary Text: `#1A202C` (Dark Slate)
- Secondary Text: `#4A5568` (Medium Slate)
- Muted Text: `#718096` (Gray-Blue)
- Accent: `#CBD5E0` (Soft Gray-Blue)
- Focus Accent: `#63B3ED` (Muted Pastel Blue)
- Success: `#68D391` (Muted Green)
- Warning: `#F6E05E` (Muted Yellow)
- Border/Light: `#EDF2F7` (Very Light Gray)

### Typography
- Headers: Playfair Display (Serif)
- Body/Data: Space Mono (Monospace)

### 3D Elements
- Single 3D location pin icon in header
- Subtle elevation effects on cards and buttons
- Hover lifts and shadow increases for interactive elements

### Layout
- Asymmetrical split-pane design (sidebar + main content)
- 8px grid system for spacing
- Maximum width: 1200px with 24px padding
- No decorative gradients, animations, or gratuitous motions

## Data Model

### Projects
- id, name, our_profile, created_at

### Competitors
- id, project_id, name, gmap_url, added_at

### Keywords
- id, project_id, keyword, added_at

### Posts
- id, competitor_id, post_url, text_content, published_date, scrape_date
- image_urls (JSON), cta, detected_topic, detected_keywords (JSON)
- raw_data (JSON), content_hash (for duplicate detection)

### Generated Ideas
- id, project_id, idea_text, generated_at, used_flag

### Scraping Logs
- id, project_id, start_time, end_time, competitors_processed
- posts_found, new_posts, duplicates_skipped, failures, captcha_encountered
- error_info

## Evaluation & Verification

To verify the implementation:

1. Register for free Gemini API key (Google AI Studio) and Grok API (x.com)
2. Set environment variables in `.env` file
3. Run `docker-compose up --build`
4. Access http://localhost:3000
5. Create test project, add 2 competitors with known Google Maps profiles
6. Start scrape, observe logs for CAPTCHA handling
7. Verify posts appear in database with correct fields
8. Run analysis, check topic frequencies
9. Generate 5 ideas, verify uniqueness
10. Generate complete update, validate all required fields present
11. Test responsive layout via browser dev tools
12. Confirm demo dataset loads when DB is empty

## License

This project is created for the Google Maps Competitor Update Intelligence Tool technical examination assignment.

## Acknowledgments

- Tailwind CSS for utility-first CSS framework
- Playfair Display and Space Mono fonts from Google Fonts
- Selenium for web automation
- Gemini and Grok AI for artificial intelligence capabilities
- Flask for Python web framework