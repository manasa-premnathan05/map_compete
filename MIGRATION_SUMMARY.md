# MapCompete — SQLite → MongoDB Atlas Migration: What Changed & What To Do Next

**Date:** 2026-09-29 · **Status:** complete, tested against live Atlas, awaiting deploy configuration
**Target architecture:** Vercel (frontend) → Render (Flask + Selenium backend) → MongoDB Atlas

---

## 1. Summary in one paragraph

The persistence layer was replaced from SQLite to MongoDB Atlas (PyMongo) **without
changing any API endpoint, response shape, or frontend code path** — all 43 routes,
numeric `id` values, duplicate-prevention rules, analytics payloads, scraping statuses
and AI features behave exactly as before. Deployment files were converted from an
Oracle-VM plan to Render (Docker web service with Chromium) + Vercel (static frontend
with an `/api/*` rewrite). No data migration was performed (none was needed — the old
data was explicitly not required); today the cluster holds only the validation data
listed at the end of §7.
All data now lives in MongoDB, so Render's ephemeral filesystem is fine and the SQLite
file is no longer used at runtime.

---

## 2. Architecture (before → after)

```
BEFORE (SQLite)                          AFTER (MongoDB Atlas)
────────────────                         ────────────────────
Browser → Vercel                        Browser → Vercel
           → Oracle VM (Flask)                       → Render (Flask + Chromium)
             → SQLite file (.db)                       → MongoDB Atlas
             → persistent Docker volume               → managed, no local files
PC must be ON to scrape               Scrape runs on demand; PC can be OFF
```

The backend is still **request-driven**: Selenium starts only when a user presses
**Scrape**, one browser at a time, sequential — no background workers, no queues.

---

## 3. Files created

| File | Purpose |
|---|---|
| [`render.yaml`](render.yaml) | Render blueprint: Docker web service, health check `/api/health`, secrets as `sync: false` (never in git) |
| [`backend/test_mongodb.py`](backend/test_mongodb.py) | **Live Atlas diagnostic** (the one environment-dependent test): config → connect → ping → insert/read/delete a marked smoke-test doc; leaves nothing behind; clear failure when `MONGODB_URI` is missing |
| [`backend/test_database_mongo.py`](backend/test_database_mongo.py) | **Offline unit tests** (mongomock): empty-DB, CRUD for all collections, dedup + share-links, delete cascades, ordering, analytics, canonical places, id-collision safety |
| [`backend/test_api_mongomock.py`](backend/test_api_mongomock.py) | **API contract tests** (`Flask.test_client()` + mongomock): health 200/503, 503 guard, project/competitor/post/analytics routes, JSON shapes, 201-on-create |

`mongomock` is a **test-only** dependency (not in `requirements.txt`):

```bash
pip install mongomock
```

---

## 4. Files modified (tracked in git)

### Persistence & API
| File | What changed |
|---|---|
| [`backend/database.py`](backend/database.py) | **Full rewrite** (2,535 lines): SQLite → MongoDB. Same public method surface (`get_projects`, `add_competitor`, `add_post`, `get_posts`, `get_market_overview`, `get_trend_analysis`, …) so `api.py` is untouched. One reusable `MongoClient` (SRV, 5 s timeouts), `DatabaseUnavailableError` (credential-safe), idempotent `ensure_indexes()`, atomic `counters` collection for numeric ids, `available()`/`health()`. No `sqlite3`, no SQL, no seed data. |
| [`backend/api.py`](backend/api.py) | `DB_PATH`/`DatabaseManager(DB_PATH)` → `DatabaseManager()` (reads `MONGODB_URI`); `/api/health` reports MongoDB connectivity (200 connected / 503 degraded, never leaks creds); `DatabaseUnavailableError` handler + `before_request` guard → clear **503** when the DB is down; the one raw-SQL block (competitor status update) → `db.update_competitor_scrape_status()`; `PORT` default `5000` → `10000` |
| [`backend/requirements.txt`](backend/requirements.txt) | Added `pymongo==4.10.1` (existing packages untouched) |

### Configuration
| File | What changed |
|---|---|
| [`.env.example`](.env.example) | Added `MONGODB_URI` + `MONGODB_DATABASE`; `PORT=10000`; CORS notes for Vercel; no real credentials |
| [`.gitignore`](.gitignore) | `.env`, `.env.*`, `!.env.example`, `*.db`, `*.sqlite`, `*.sqlite3` |

### Deployment
| File | What changed |
|---|---|
| [`backend/Dockerfile.backend`](backend/Dockerfile.backend) | No more `.db` seed COPY / `DB_PATH`; `EXPOSE 10000`; PORT-aware HEALTHCHECK; writable `/tmp/chrome`; Chromium + `chromium-driver` kept (amd64 on Render) |
| [`backend/docker-entrypoint.sh`](backend/docker-entrypoint.sh) | SQLite seeding removed; Gunicorn binds `0.0.0.0:$PORT` (default 10000) |
| [`backend/.dockerignore`](backend/.dockerignore) | Now excludes `.env`, `.env.*`, `*.db` (no DB baked into the image) |
| [`docker-compose.yml`](docker-compose.yml) | No volume; passes `MONGODB_URI`/`MONGODB_DATABASE`; container port 10000 |
| [`frontend/vercel.json`](frontend/vercel.json) | Rewrite destination → `https://YOUR-BACKEND.onrender.com/api/:path*` ← **you must replace `YOUR-BACKEND`** |
| [`frontend/nginx.conf`](frontend/nginx.conf) | `/api/` proxy target `backend:5000` → `backend:10000` |

### Frontend
| File | What changed |
|---|---|
| [`frontend/js/components/api.js`](frontend/js/components/api.js) | Only the local-dev base URL: `http://localhost:5000/api` → `http://localhost:10000/api` (matches `PORT=10000`). Production stays relative `/api`. No UI change. |

### Documentation
| File | What changed |
|---|---|
| [`README.md`](README.md) | Architecture (Vercel/Render/Atlas), local dev on :10000, env vars, collections table, new test commands, project structure |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | **Fully rewritten** for Render + Vercel + Atlas (old Oracle-VM guide removed): Atlas setup, env vars, Render blueprint/manual, Selenium on Render, Vercel, CORS, verification checklist, local dev, tests, troubleshooting, security, free-tier recap |

*(Also still modified in your working tree from the previous task — not part of this
migration: `backend/ai_service.py` Groq fix, `backend/scraper.py` env-var Chromium,
`frontend/index.html` AI panel, `analytics.js`, `dashboard.js`, `Dockerfile.frontend`.)*

---

## 5. Local-only changes (git-ignored by the repo's `verify_*.py` rule)

| File | Change |
|---|---|
| `.env` (untracked) | `PORT=5000` → `PORT=10000`; added empty `MONGODB_URI=` / `MONGODB_DATABASE=competitor_intelligence keys for you to fill |
| [`verify_basic_functionality.py`](verify_basic_functionality.py) | temp `.db` files replaced by an in-memory mongomock client (still ALL PASSED) |
| [`verify_frontend_ui.py`](verify_frontend_ui.py) | default API URL → `http://localhost:10000/api` |

**Left alone (obsolete, not deleted):** `backend/repair_scraped_data.py`,
`backend/scrape_profiles.py`, `backend/clean_projects.py`, `seed_*`/`populate_*` one-off
scripts, and legacy docs `START_GUIDE.md` / `walkthrough.md` / `implementation_plan.md`.
Nothing in the running application imports them.

---

## 6. Database design (SQLite → MongoDB)

| Collection | Purpose | Key indexes |
|---|---|---|
| `projects` | projects + own canonical place | — |
| `competitors` | project↔competitor rows | `project_id`, `place_id`, `business_key`, `(project_id, place_id)` |
| `places` | canonical businesses | **unique** `place_key`; `google_place_id`, `hex_id`, `cid`, `kgmid`, `name` |
| `posts` | scraped updates | **unique** `content_hash` (dedup); `post_url`, `competitor_id`, `published_date`, `scrape_date` |
| `post_competitors` | post↔competitor share links | **unique** `(post_id, competitor_id)` |
| `reviews` | scraped reviews | **unique** `content_hash`; `project_id`, `competitor_id` |
| `keywords` / `generated_ideas` / `scraping_logs` | as before | `project_id` |
| `counters` | atomic numeric-id allocation | `_id` |

* **IDs preserved:** documents carry a numeric `id` (MongoDB `_id` is internal), allocated
  from `counters` via `find_one_and_update + $inc` (never `count+1`); counters seed to
  `max(id)` with `$max`, so restarts/concurrency cannot rewind or duplicate them.
* **Timestamps** are stored exactly as SQLite returned them (`YYYY-MM-DD HH:MM:SS`) —
  no frontend display changes.
* `project_places` (old SQL view) is derived on the fly from competitors with a `place_id`.
* **Duplicate prevention unchanged:** posts dedupe on `content_hash` then `post_url`
  (duplicates create a `post_competitors` share-link so other projects still see the
  post); reviews on content hash; competitors on canonical place / business key; places
  on unique `place_key` + weak-name folding.
* **No seed/demo data** anywhere — a fresh database starts empty, as required.
* Owner posts, public/user content and reviews stay in separate collections/fields
  (`post_source` = `owner` / `public`); scraping statuses and logs unchanged.

---

## 7. Tests performed & results

| Test | Result |
|---|---|
| `py_compile` on 9 backend files | ✅ OK |
| YAML parse (`render.yaml`, `docker-compose.yml`) | ✅ OK |
| `node --check` (`api.js`, `analytics.js`) | ✅ OK |
| `python backend/test_database_mongo.py` (mongomock, ~111 checks) | ✅ **ALL PASSED** |
| `python backend/test_api_mongomock.py` | ✅ **ALL PASSED** |
| `python verify_basic_functionality.py` | ✅ **ALL TESTS PASSED** |
| Live Flask (no URI) + curl `/api/health` | ✅ boots; `503 {"status":"degraded","database_error":"MONGODB_URI is not configured..."}` (no creds/traces) |
| Live Flask `/api/projects` with DB down | ✅ `503` JSON via the central guard |
| `python backend/test_mongodb.py` without URI | ✅ clean `[FAIL] MONGODB_URI is not set` + exit 1 (designed) |
| App import | ✅ 43 routes registered |
| Git safety | ✅ `.env`/`*.db` ignored, `.env.example` not ignored, nothing staged |

### Live Atlas validation (2026-09-29 — the environment-dependent tests, now executed)

| Test | Result |
|---|---|
| `python backend/test_mongodb.py` (live Atlas) | ✅ **SUCCESS: MongoDB Atlas is configured correctly for MapCompete.** — connect → DB access → insert/read → cleanup, nothing left behind |
| Live API vs Atlas: `GET /api/health` | ✅ `200 {"status":"healthy","database":"connected"}` |
| Live reads + writes vs Atlas | ✅ project create/edit/delete through the real UI flows; numeric ids from the atomic `counters` strictly increasing (1 → 6, no reuse after deletes) |
| Live scrape (`POST /api/competitors/13/scrape`) | ✅ real Google Maps crawl: page loaded, **business verified**, updates section opened, 5 scrolls → `NO_POSTS` (that salon publishes no Google Posts — correct behaviour, not an error) |
| `python verify_frontend_ui.py` (full 19-check run) | ✅ **17/19 PASS** — checks 12–13 failed only because the brand-new DB had no posts (those routes answer `400 No posts found` by design) |
| `python verify_frontend_ui.py --only analytics,idea` (after seeding posts) | ✅ **ALL 2 UI CHECKS PASSED** (AI analysis completed; 2 ideas + complete-update format) — effective result **19/19** |

**Honest limits (not tested on this PC):** Docker image build (no Docker/WSL2 — verified
on deploy via `DEPLOYMENT.md` §3/§7) and Gunicorn runtime (Linux-only; `api:app` import
verified). Everything else — live Atlas CRUD, live scraping with business verification,
the AI features against Atlas and the full UI suite — was executed against your real
cluster on 2026-09-29.

**Data left in Atlas by the validation runs** (delete it in the UI if you want a clean
slate): project **Aura Salon & Wellness** (id 1), 3 tracked real competitors, 3 fixture
posts created through the app's own `DatabaseManager.add_post` (marked in
`raw_data.note`), 2 generated ideas. Every throwaway project the UI suite created was
auto-deleted.

---

## 8. What YOU need to do next (in order)

### Step 1 — Fill your local `.env`
```env
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=competitor_intelligence
```
Then verify locally: `python backend/api.py` →
`http://localhost:10000/api/health` must show `"database":"connected"`, and
`python backend/test_mongodb.py` should print
`SUCCESS: MongoDB Atlas is configured correctly for MapCompete.`

### Step 2 — Create the MongoDB Atlas cluster (free M0)
1. Atlas → **Build a Database** → free **M0 Shared**.
2. **Database Access → Add New Database User** (username + strong password,
   *Read and write to any database*).
3. **Network Access → Add IP Address** → `0.0.0.0/0` (Allow from anywhere).
4. **Connect → Drivers → Python** → copy the SRV string → that is your
   `MONGODB_URI` (replace `<password>`). **Never commit it.**

### Step 3 — Push the code
```bash
git add -A            # .env is ignored, secrets are never staged
git status            # double-check nothing sensitive appears
git commit -m "Migrate persistence to MongoDB Atlas; deploy targets Render + Vercel"
git push
```

### Step 4 — Deploy the backend on Render
1. Render → **New → Blueprint** → connect the repo (uses [`render.yaml`](render.yaml)).
   *Or manually:* **New → Web Service** → Runtime **Docker** → Dockerfile
   `backend/Dockerfile.backend`, Docker context `backend`.
2. **Environment** → add (as secrets, they never live in git):
   `MONGODB_URI`, `MONGODB_DATABASE=competitor_intelligence `GROQ_API_KEY`,
   optional `GEMINI_API_KEY` / `GROK_API_KEY`, `GUNICORN_WORKERS=2`,
   `GUNICORN_TIMEOUT=1800`. **Do not set `PORT`** — Render injects it.
3. Deploy → verify `https://<your-service>.onrender.com/api/health` →
   `{"status":"healthy","database":"connected",...}`. The first build installs
   Chromium (a few minutes).

### Step 5 — Point the frontend at Render and deploy to Vercel
1. Edit [`frontend/vercel.json`](frontend/vercel.json): replace
   `YOUR-BACKEND.onrender.com` with your real Render URL. Commit & push.
2. Vercel → **Add New → Project** → import the repo:
   * **Root Directory:** `frontend`
   * **Framework Preset:** Other (no build step)
   * **Environment variables:** none needed
3. Deploy → you get `https://your-app.vercel.app`.

### Step 6 — Finalize CORS
On Render (Environment → restart):
```
CORS_ORIGINS=https://your-app.vercel.app
```

### Step 7 — Post-deploy verification
1. `/api/health` → 200 connected.
2. Vercel site loads with your current Atlas contents (today: project
   **Aura Salon & Wellness**, 3 competitors, 3 posts — delete them in the UI for a
   clean slate).
3. Create a project → it appears in the switcher.
4. Add a competitor with a real Google Maps URL → Resolve → Save.
5. Press **Scrape** → `SUCCESS`/`NO_POSTS`; posts and dashboard counts update.
6. Analytics → **Run AI Analysis**; Ideas → **Generate Content Ideas** works.
7. Delete a test project; re-scrape once → `duplicates_skipped` grows while
   `new_posts` stays 0 (deduplication works).

### Step 8 — Confirm $0.00 billing
Atlas, Render and Vercel `Billing` pages must all show **$0.00**. Never accept an
"Upgrade" prompt. Render Free sleeps after ~15 min idle — the first request
(~30–60 s cold start) is normal.

---

## 9. Quick reference

| Where | Keys / values |
|---|---|
| **Render Environment** | `MONGODB_URI` (secret) · `MONGODB_DATABASE=competitor_intelligence` · `CORS_ORIGINS=https://your-app.vercel.app` · `GROQ_API_KEY` (secret) · `GEMINI_API_KEY` (optional) · `GROK_API_KEY` (optional) · `GUNICORN_WORKERS=2` · `GUNICORN_TIMEOUT=1800` — **do not set `PORT`** (injected) |
| **Local `.env`** | same minus the gunicorn knobs; `PORT=10000` |
| **Vercel** | no env vars; only the rewrite destination in [`frontend/vercel.json`](frontend/vercel.json) |
| **MongoDB Atlas** | free M0 · RW database user · Network Access `0.0.0.0/0` |
| **Local dev commands** | `python backend/api.py` (API :10000) · `cd frontend && python -m http.server 3000` · optional `docker compose up --build` |
| **Test commands** | `python backend/test_database_mongo.py` · `python backend/test_api_mongomock.py` · `python backend/test_mongodb.py` (needs URI) · `python verify_frontend_ui.py` (needs live backend) |

## 10. Troubleshooting quick hits

| Symptom | Fix |
|---|---|
| `/api/health` 503 "MONGODB_URI is not configured" | Set it in Render → Environment → restart |
| 503 "MongoDB is unreachable" / `bad auth : Authentication failed` (code 8000) | Wrong credentials or Atlas IP allowlist missing. Atlas **usernames are case-sensitive** (`manasapremnathan_db_user` ≠ `Manasapremnathan_db_user`) — the one real credential bug found during validation |
| Vercel API calls 502/504 | `frontend/vercel.json` still has the placeholder, or Render is asleep (retry after ~30 s) |
| Scrape `SCRAPER_ERROR` on Render | Rebuild the image (clear build cache); Chromium is in the Dockerfile |
| CORS console error | Set `CORS_ORIGINS` to your Vercel domain on Render |
| Groq 429 | Rate limit; the backend retries — wait and retry |
| Local `/api/health` degraded | `.env` has an empty `MONGODB_URI` — fill the Atlas SRV string |

## 11. Security notes

* Secrets live only in your local `.env` (git-ignored) and Render's Environment;
  [`.env.example`](.env.example) holds placeholders only.
* The API never returns connection strings or stack traces (errors are
  credential-sanitized and mapped to HTTP 503); logs never print the URI or keys.
* All MongoDB queries use driver filters (no string-built queries → no injection).
* Run `git status` before every commit; `.env` and `*.db` are ignored.
* This file intentionally contains **no credentials** — only key names and
  placeholders.




