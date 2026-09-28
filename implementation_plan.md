# Implementation Plan: Google Maps Geo-Location & Field-Based Competitor Discovery

## Overview
Implement the automated competitor discovery workflow specified in the assignment (Section 6 & Section 25) and requested by the user:
When a user searches a company's name (e.g., *"ABC Salon, Kharghar"* or *"Aura Salon, Downtown"*), the system analyzes the business's **geographic location** and **industry field/category**, identifies real nearby competitor businesses on Google Maps in that exact locality, and presents them in an interactive discovery list with an option to enter/add them directly into the project's tracked competitors.

---

## User Review Required

> [!IMPORTANT]
> - **Input Flexibility**: The user can search either a combined query (e.g., `"ABC Salon, Kharghar"`) or enter the company name and location separately. The system automatically detects the business field (e.g., Salon, Dental Clinic, Cafe) and geographic area.
> - **De-duplication (Section 6 Compliance)**: Discovered competitors are checked against existing competitors in the project. Any competitor already being tracked is marked with an *"Already Tracked"* badge to prevent duplicate records.
> - **One-Click Entry**: Users can either click `+ Add` on individual discovered competitors or select multiple competitors and click `+ Add Selected to Project`.

---

## Proposed Changes

### 1. Backend: Location & Field Competitor Discovery Engine
#### [MODIFY] [backend/ai_service.py](file:///e:/Downloads/google%20map%20competitor/backend/ai_service.py)
- Add `discover_local_competitors(query, location=None, field=None, existing_competitors=[])`:
  - Uses Groq AI (with fallback to Gemini / rule-based Google Maps search format).
  - Extracts the exact business field (e.g., *Hair & Beauty Salon*, *Cosmetic Dermatology*, *Specialty Barber*) and geographical area (e.g., *Kharghar, Navi Mumbai*).
  - Identifies 5–8 top local competitor businesses operating in that exact geographic zone and field.
  - Generates verifiable Google Maps place URLs (`https://www.google.com/maps/search/?api=1&query=...`), addresses, approximate ratings, and specialties.
  - Cross-references existing project competitors to flag `already_added`.

#### [MODIFY] [backend/api.py](file:///e:/Downloads/google%20map%20competitor/backend/api.py)
- Add endpoint `POST /api/projects/<int:project_id>/discover-competitors`:
  - Accepts `{"query": "...", "location": "...", "field": "..."}`.
  - Retrieves existing competitors for the project from `db.get_competitors(project_id)`.
  - Invokes `ai_service.discover_local_competitors(...)`.
  - Returns structured competitor candidates with verified Google Maps URLs and tracking status.

---

### 2. Frontend: Discovery UI & Interactive Entry
#### [MODIFY] [frontend/index.html](file:///e:/Downloads/google%20map%20competitor/frontend/index.html)
- In `#competitors-view`:
  - Add a dedicated **"Smart Competitor Discovery"** panel:
    - Input bar: Search company name or location (e.g., *"ABC Salon, Kharghar"* or *"Organic Cafe in Brooklyn"*).
    - `🔍 Discover Competitors` button with loading spinner.
    - Results container: Displays detected field badge (e.g. 🏷️ *Hair Salon & Aesthetics*) and location badge (📍 *Kharghar Sector 12*), followed by cards for each discovered business with direct Google Maps link and an `[+ Add to Tracked]` action button.
- In `#add-competitor-modal`:
  - Add a tab or toggle between *"Quick Discover via Google Maps"* and *"Manual URL Entry"*.

#### [MODIFY] [frontend/js/components/competitors.js](file:///e:/Downloads/google%20map%20competitor/frontend/js/components/competitors.js)
- Wire up the discovery form submission:
  - Calls `api.discoverCompetitors(projectId, query)`.
  - Renders discovered competitor cards with ratings, Google Maps links, and badges.
  - Wire up the `[+ Add to Project]` button on each discovered competitor card to call `api.addCompetitor()` and automatically refresh the main tracked competitors table.

#### [MODIFY] [frontend/js/components/api.js](file:///e:/Downloads/google%20map%20competitor/frontend/js/components/api.js)
- Add `discoverCompetitors(projectId, queryData)` method.

---

## Verification Plan

### Automated Verification
1. Run `python -m py_compile backend/ai_service.py backend/api.py` to ensure no syntax errors.
2. Test endpoint with PowerShell:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/api/projects/1/discover-competitors" -Method Post -ContentType "application/json" -Body '{"query": "ABC Salon, Kharghar"}'
   ```
   Verify it returns detected field (*Salon*), location (*Kharghar*), and a list of local competitors with Google Maps URLs.
3. Test adding one discovered competitor to the project and verify `already_tracked` turns true on subsequent searches.

### Manual / Browser Verification
1. Open `http://localhost:3000` &rarr; Go to **Competitors** tab.
2. Enter a company name with location (e.g., *"ABC Salon, Kharghar"* or *"Aura Salon, Downtown"*).
3. Click **"Discover Competitors"**.
4. Confirm discovered competitors are displayed with their address and Google Maps links.
5. Click **"+ Add to Project"** and verify the competitor immediately appears in the Tracked Competitors table and on the Dashboard.
