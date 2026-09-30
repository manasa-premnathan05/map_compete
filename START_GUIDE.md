# Quick Start Guide for MapCompete

## Option 1: Start Immediately (No API Keys Required)

All core functionality works without API keys using intelligent fallback methods.

### Step 1: Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend dependencies are handled via CDN in the HTML
```

### Step 2: Start the Backend
```bash
cd backend
python api.py
```
The API will be available at http://localhost:10000 (the `PORT` in `.env`;
set `PORT=5000` to keep the old port)

### Step 3: Open the Frontend
Recommended (serves `frontend/` and proxies `/api/*` to a working backend):
```bash
# From the root directory
python serve_local.py
```
Or use any static server; the page then auto-detects the local API:
```bash
python -m http.server 3000 --directory frontend
```
Then visit http://localhost:3000

### Step 4: Test Core Workflow
1. Create a project (e.g., "Test Salon")
2. Add competitors manually (you can use dummy URLs like "https://maps.google.com/placeholder" for testing)
3. Click "Start Scraping" - it will show "No competitors with valid URLs" which is expected for testing
4. Add some sample posts directly via database or wait for real scraping
5. Use the AI analysis and content generation features - they'll use fallback methods

## Option 2: Enhanced Features (With API Keys)

### Step 1: Get API Keys
Follow the instructions in the README.md or .env.example file to get:
- Gemini API Key from Google AI Studio
- Grok API Key from xAI Console

### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env and add your actual keys
```

### Step 3: Start System with Docker (Recommended for Full Stack)
```bash
docker-compose up --build
```
Then visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api/health

## What's Working Right Now (Without API Keys)

✅ **Complete User Workflow:**
- Project creation and management
- Competitor and keyword management  
- Web scraping interface (will work with real URLs)
- Data storage and retrieval
- Duplicate detection
- Basic analytics (counts, simple filtering)
- Template-based content generation
- Basic complete update generation
- All UI components and interactions
- Responsive design on mobile/desktop
- CAPTCHA handling simulation

🔧 **Fallback AI Features:**
- Rule-based topic extraction from post text
- Simple keyword frequency counting
- Template-based idea generation (business-appropriate templates)
- Template-based complete updates
- All generated content is stored and tracked for duplicate prevention

📊 **What You'll See Without API Keys:**
- Console logs showing "Using GeminiAIService with fallbacks"
- Analysis results showing "Fallback analysis based on keyword frequency"
- Generated ideas using business templates
- Complete updates using placeholder business copy

## Next Steps

1. **Test Core Functionality:** Try the workflow outlined above
2. **Add API Keys:** When ready for enhanced AI insights
3. **Deploy:** Use Docker for production deployment
4. **Customize:** Modify templates in ai_service.py for your specific use case

The system is designed to be immediately useful while providing a clear upgrade path when you add AI capabilities.