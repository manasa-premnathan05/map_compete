# MapCompete Deployment Guide — Vercel + Render + MongoDB Atlas

Target architecture (PC can be OFF after deployment):

```
Browser ──> Vercel (frontend, static)
                │  /api/* rewrite
                ▼
            Render Web Service (Flask + Gunicorn + Selenium/Chromium, Docker)
                │
                ▼
            MongoDB Atlas (all application data, fresh/empty at first deploy)
```

* Scraping runs **only when a user presses Scrape** (request-driven, no
  background workers, no Redis/Celery).
* There is **no local database file** anymore. Everything lives in MongoDB
  Atlas, so Render's ephemeral filesystem is fine.
* **Free tiers**: Atlas M0 (free), Render Free web service, Vercel Hobby.
  Still, always verify `Billing` shows $0.00 on every platform after setup.

**Contents**

0. What you will need
1. MongoDB Atlas setup
2. Environment variables
3. Render backend deployment
4. Selenium / Chromium on Render
5. Vercel frontend deployment
6. CORS finalization
7. Post-deploy verification checklist
8. Local development
9. Testing
10. Troubleshooting
11. Security notes
12. Free-tier recap

---

## 0. What you will need

* A GitHub account with this repository.
* A free [MongoDB Atlas](https://www.mongodb.com/atlas) account.
* A free [Render](https://render.com) account.
* A free [Vercel](https://vercel.com) account.
* Your AI keys: `GROQ_API_KEY` (required for AI features), optional
  `GEMINI_API_KEY`.

**Never paste secrets into chat, docs, or git.** They go into Render's
environment settings and your local `.env` (git-ignored) only.

---

## 1. MongoDB Atlas setup

1. MongoDB Atlas → **Build a Database** → choose the free **M0 Shared** tier.
2. Choose any region/provider close to you.
3. **Database Access → Add New Database User**
   * Authentication: username + password (generate a strong password; store
     it in a password manager — you will only paste it into Render once).
   * Permissions: **Read and write to any database**.
4. **Network Access → Add IP Address**
   * Easiest: `0.0.0.0/0` (Allow Access From Anywhere). The password is the
     protection; restrict later if you prefer.
5. **Connect → Drivers** → choose Python → copy the SRV string, e.g.:

   ```
   mongodb+srv://mapcompete:<PASSWORD>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

   Replace `<PASSWORD>` with your user's password. This full string is your
   `MONGODB_URI`.

The database starts **empty** — collections (`projects`, `competitors`,
`places`, `posts`, `post_competitors`, `reviews`, `keywords`,
`generated_ideas`, `scraping_logs`, `counters`) and their indexes are created
automatically and idempotently on first application boot. Do **not** import
any old SQLite file; no migration is needed or supported.

---

## 2. Environment variables

Local (`.env` in the repo root — git-ignored, copy from `.env.example`):

```env
MONGODB_URI=mongodb+srv://mapcompete:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=competitor_intelligence
GROQ_API_KEY=gsk_your_key
GEMINI_API_KEY=
GROK_API_KEY=
PORT=10000
CORS_ORIGINS=*
```

The same keys (except `PORT`, which Render sets itself) are configured in
Render → **Environment** tab. See §3.

---

## 3. Render backend deployment

The repository contains a **`render.yaml` blueprint** (Docker web service),
so the shortest path is:

1. Render Dashboard → **New → Blueprint** → connect your GitHub repository.
2. Render reads `render.yaml` and creates the `mapcompete-backend` web
   service from `backend/Dockerfile.backend`.
3. Open the service → **Environment** and fill the secret values
   (`sync: false` entries are never stored in git):

   | Key | Value |
   |-----|-------|
   | `MONGODB_URI` | your Atlas SRV string (with password) |
   | `MONGODB_DATABASE` | `competitor_intelligence` |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` (after step 5; `*` works meanwhile) |
   | `GROQ_API_KEY` | your Groq key |
   | `GEMINI_API_KEY` | optional |
   | `GROK_API_KEY` | optional (legacy alias) |
   | `GUNICORN_WORKERS` | `2` (Render Free has 512 MB) |
   | `GUNICORN_TIMEOUT` | `1800` (long scrapes) |

4. Deploy. Render builds the Docker image (Chromium + Chromium driver are
   installed in the Dockerfile) and starts Gunicorn bound to
   `0.0.0.0:$PORT` — Render injects `$PORT` automatically.

**Manual alternative (no blueprint):** New → Web Service → connect repo →
Runtime: **Docker** → Dockerfile Path: `backend/Dockerfile.backend` →
Docker Context: `backend` → add the environment keys above.

Expected first boot (Logs tab):

```
[entrypoint] Starting gunicorn (workers=2, timeout=1800s) on 0.0.0.0:10000
INFO:... Connected to MongoDB database 'competitor_intelligence'
```

Health check: `https://<your-service>.onrender.com/api/health` must return

```json
{"status": "healthy", "database": "connected", ...}
```

If `MONGODB_URI` is missing/wrong you get HTTP **503** with a clear
`database_error` (no credentials, no traceback) — fix the env var and
redeploy/restart.

### Render Free expectations

* The service **spins down after ~15 min without traffic**; the first request
  after idle takes ~30–60 s (cold start). Pressing Scrape wakes it up.
* 512 MB RAM — keep `GUNICORN_WORKERS=2`; Selenium runs one browser at a
  time (scraping is sequential by design).
* Never enable a paid instance type unless you intend to pay.

---

## 4. Selenium / Chromium on Render

Handled entirely by `backend/Dockerfile.backend`:

* `chromium` + `chromium-driver` come from Debian's repositories (version
  matched, amd64 on Render).
* `CHROME_BINARY=/usr/bin/chromium` and `CHROMEDRIVER_PATH=/usr/bin/chromium-driver`
  are baked as env vars, so Selenium never downloads an x86-only driver.
* Chromium launches headless with `--no-sandbox --disable-dev-shm-usage`
  (container-safe); no GUI/display is needed.
* Drivers are created **per scrape request only** — the API server never
  starts Selenium at boot — and every scrape path closes the driver in a
  `finally` block, so failures never leak Chromium processes.

To verify after deploy: create a project, add a competitor with a real
Google Maps URL and press **Scrape** (see §7).

---

## 5. Vercel frontend deployment

The frontend is the existing static app (`frontend/`) — no framework, no
build step. All API calls go to the relative `/api/*` path, which Vercel
forwards to Render through `frontend/vercel.json`.

1. Edit **`frontend/vercel.json`** and replace the placeholder with your real
   Render URL:

   ```json
   {
     "rewrites": [
       { "source": "/api/:path*",
         "destination": "https://YOUR-SERVICE-NAME.onrender.com/api/:path*" }
     ]
   }
   ```

   Commit and push **before** importing to Vercel (or edit the file in the
   Vercel dashboard later).

2. Vercel → **Add New → Project** → import the GitHub repository:
   * **Root Directory**: `frontend`  (so `vercel.json` is picked up)
   * **Framework Preset**: Other (no build command, output = static files)
   * No environment variables are needed — the frontend resolves the API URL
     at runtime (`window.__API_BASE__` override → localhost in dev →
     relative `/api` in production).

3. Deploy → you get `https://your-app.vercel.app`.

Local override (only if you ever need it): set `window.__API_BASE__` before
`app.js` loads, e.g. `http://localhost:10000/api`.

---

## 6. CORS finalization

Once the Vercel domain exists, set it on Render:

```
CORS_ORIGINS=https://your-app.vercel.app
```

(comma separated if you also keep a local origin:
`https://your-app.vercel.app,http://localhost:3000`), then restart the
service. Until then `CORS_ORIGINS=*` keeps development working.

---

## 7. Post-deploy verification checklist

Run these from the Vercel URL (and directly against the Render URL once):

1. `GET https://<render>/api/health` → `200` with `"database": "connected"`.
2. Open the Vercel site → the dashboard loads with **zero projects**
   (the empty database is correct — no demo data).
3. Create a project (e.g. a real business name + location) → appears in the
   switcher. *This also exercises AI discovery.*
4. Add a competitor with a real Google Maps URL → Resolve → Save.
5. Press **Scrape** on that competitor → status `SUCCESS`/`NO_POSTS`,
   post count appears; check Render logs for the scraper run and confirm no
   Chromium process lingers after it finishes (`ps aux | grep chrom` inside
   the container if needed).
6. Posts tab shows the scraped updates; Dashboard statistics update.
7. Analytics tab → **Run AI Analysis** completes (needs `GROQ_API_KEY`).
8. Ideas tab → **Generate Content Ideas** returns cards.
9. Delete the test project → `DELETE` returns 200, project disappears.
10. Re-run step 3-5 once more to confirm subsequent scrapes **deduplicate**
    (`duplicates_skipped` grows, `new_posts` stays 0 for re-scrapes).

---

## 8. Local development

```bash
cp .env.example .env           # fill MONGODB_URI + GROQ_API_KEY
pip install -r backend/requirements.txt
python backend/api.py          # API on http://localhost:10000 (PORT env)

# frontend, any static server:
cd frontend && python -m http.server 3000
# open http://localhost:3000
```

* Local development talks to the **same Atlas cluster** (or your own local
  `mongod`) — no SQLite file is used or needed.
* Optional Docker stack: `docker compose up --build` (API proxied on
  `localhost:5000`, frontend on `:3000`).
* Windows note: `gunicorn` is Linux-only; local dev uses `python
  backend/api.py`. Render/Docker use Gunicorn via `docker-entrypoint.sh`.

---

## 9. Testing

```bash
# Offline unit tests - persistence layer against an in-memory MongoDB
pip install mongomock
python backend/test_database_mongo.py

# API contract tests (Flask test_client + mongomock, no server needed)
python backend/test_api_mongomock.py

# Live Atlas connectivity (the ONE environment-dependent test)
python backend/test_mongodb.py

# Full UI verification (needs running backend + Atlas)
python verify_frontend_ui.py
```

Expected: the first three print `ALL ... TESTS PASSED`. `test_mongodb.py`
exits non-zero with a clear message when `MONGODB_URI` is missing — that is
its designed behaviour, not a code failure.

---

## 10. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `/api/health` → 503 `"MONGODB_URI is not configured"` | Set `MONGODB_URI` in Render → Environment → Restart |
| `/api/health` → 503 `"MongoDB is unreachable: ..."` | Wrong password, or Atlas **Network Access** doesn't allow the IP (`0.0.0.0/0` is simplest) |
| Vercel site loads but API calls fail (502/504) | `frontend/vercel.json` still has `YOUR-BACKEND.onrender.com` placeholder, or the Render service is asleep (first hit is slow — retry after ~30 s) |
| CORS error in browser console | Set `CORS_ORIGINS=https://your-app.vercel.app` on Render and restart |
| Render build fails on `pip install` | Check `backend/requirements.txt` wasn't modified; Render needs internet on first build |
| Scrape returns `SCRAPER_ERROR` / driver not found | Render logs should show `CHROME_BINARY`/`CHROMEDRIVER_PATH`; the Dockerfile installs both — rebuild the image (Manual Deploy → Clear build cache) |
| Scrape works locally but not on Render | Local Chrome ≠ container Chromium: always test through the Docker image (`docker compose up --build`) before suspecting Render |
| `CAPTCHA_REQUIRED` | Google asked for verification; re-run later or scrape fewer competitors per run |
| Groq `429 Too Many Requests` | Rate limited — the backend retries with backoff; wait and retry |
| Service sleeps between visits | Render Free cold start (~30–60 s). Keep the tab open or upgrade if you need always-on |
| Old SQLite questions | The `.db` file is no longer read by anything at runtime; it is git-ignored and can be kept locally for reference only |

---

## 11. Security notes

* Secrets live only in: your local `.env` (git-ignored) and Render's
  Environment settings. `.env.example` contains placeholders only.
* `.gitignore` blocks `.env`, `.env.*` (except `.env.example`), `*.db`,
  `*.sqlite`, `*.sqlite3` — run `git status` before every commit.
* The API never returns connection strings or stack traces: MongoDB errors
  are sanitized (`credentials stripped`) and mapped to HTTP 503.
* Logs never contain `MONGODB_URI` or API keys (only sanitized error text).
* Use `CORS_ORIGINS` with your real Vercel domain in production.
* MongoDB queries use driver filters (no string-built queries) — no query
  injection surface from user input.

---

## 12. Free-tier recap

| Service | Plan | Notes |
|---------|------|-------|
| MongoDB Atlas | M0 (free) | 512 MB, no billing info required |
| Render | Free | 512 MB RAM, sleeps after ~15 min idle, build minutes limit |
| Vercel | Hobby | Static frontend, generous bandwidth |

Checklist after setup: Atlas `Billing` = $0.00, Render `Billing` = $0.00,
Vercel `Billing` = $0.00. Never upgrade a service to a paid plan by
accident (watch for "Upgrade" prompts when scaling).
