# MapCompete — Technical Documentation

#### Google Maps Competitor Update Intelligence
#### Document type: technical documentation and operating manual
#### Date of issue: 30 September 2026
#### Version: 1.0
#### Source repository: https://github.com/manasa-prennathan05/map_compete
#### Live frontend: https://map-compete.vercel.app
#### Live backend: https://map-compete.onrender.com
#### Backend health endpoint: https://map-compete.onrender.com/api/health

## 1. Introduction

### 1.1 Purpose of this document

This document describes the MapCompete application from a technical standpoint. It explains what the application does, how it is constructed, how its components communicate, how each stage of its working process operates, how it is configured, how it is deployed, and how it is tested. It is a description of the system as it is delivered, and it is intended to be sufficient for a reader to install the application, operate it, extend it or review it without further explanation.

### 1.2 Intended audience

The document is addressed to technical reviewers, to developers who will maintain or extend the code, and to operators who will deploy or diagnose it. Familiarity with web applications, Python, relational or document databases and browser automation is assumed.

### 1.3 Scope

The document covers the backend service, the browser-facing single-page application, the database layer, the scraping subsystem, the language model integration, the configuration surface, the deployment procedure and the test programs included in the repository. Business background, commercial considerations and future product plans are outside its scope.

## 2. System Overview

### 2.1 Functional summary

MapCompete is a competitor-intelligence application for businesses that are listed on Google Maps. An operator registers a business together with its location and field of activity, records the competing businesses that should be monitored, and then collects and analyses the public content that those competitors publish on Google Maps. The result is a body of evidence about competitor activity, together with suggested content that the operator can publish on their own Google Maps profile.

The application is organised around the concept of a project. A project is a single monitored business, and all competitors, scraped content, keywords, analytics and generated content belong to exactly one project. This allows one installation to serve several monitored businesses without interference between them, and it allows the interface to present one business at a time through a project selector in the header.

### 2.2 Principal capabilities

- Registration of a monitored business, including its name, address or locality, business profile text and field of activity.
- Distinction between two kinds of competitor research: local businesses that are physically close to the monitored business, and national or online brands where proximity is not meaningful.
- Assisted discovery of competitors from a business name and location, using both search on Google Maps and language model reasoning.
- Verification of a competitor against Google Maps so that duplicate spellings of the same business resolve to a single canonical record.
- Collection of public Google Maps content for each tracked competitor, including updates, ratings, review volumes and review text.
- Classification of the collected content by topic, keyword and sentiment, with industry-specific topic profiles for cafes, salons, fashion and online commerce.
- Analytical views covering topic frequency, keyword frequency, review analytics, trend direction over time, and market gaps derived from competitor coverage.
- Generation of content suggestions and complete Google Maps update drafts, with a record of which suggestions have already been used.
- Logging of every scraping run with outcome, counts, failures and diagnostics, so that collection activity is auditable.
- Recording of scraping failures with reasons such as CAPTCHA, blocked access, missing results, timeouts and browser errors.

### 2.3 Operating environment

The application is delivered as two independently deployed parts that communicate over HTTP: a static browser application and an HTTP service backed by a managed document database. The browser application requires no build step and no server-side rendering. The HTTP service is packaged as a container image that includes a browser engine, because the collection process drives a real browser against Google Maps rather than calling a private interface.

## 3. System Architecture

### 3.1 Logical components

| Component | Responsibility |
| --- | --- |
| Browser application | Presents the interface, holds view state, and communicates with the service exclusively through the JSON interface |
| API client module | Resolves the service address for the current environment and wraps every request in a typed function |
| HTTP service | Validates requests, applies business rules, coordinates the scraper and the language model providers, and persists results |
| Persistence layer | Encapsulates all database access behind an application-facing interface, so no route contains database queries |
| Scraping subsystem | Drives a headless browser, extracts public content, classifies it, and reports per-run diagnostics |
| Analysis subsystem | Classifies content by topic, keyword and sentiment, and derives aggregate figures and trends |
| Language model provider layer | Abstracts over one or more external providers, selects the available provider, and falls back when a provider fails |
| Migration and helper programs | Administrative programs for database population, repair and inspection |

### 3.2 Deployment topology

| Element | Platform | Address | Notes |
| --- | --- | --- | --- |
| Browser application | Vercel | https://map-compete.vercel.app | Static files served from the repository frontend directory; API requests are forwarded to the service |
| HTTP service | Render | https://map-compete.onrender.com | Container image built from backend/Dockerfile.backend, served by Gunicorn |
| Database | MongoDB Atlas | Cluster mapcompete, database competitor_intelligence | Reached only from the service, never from the browser |
| Scraper | Inside the service container | Not externally addressable | Invoked on demand; no background workers or scheduled tasks |
| Request forwarding | Vercel rewrite | /api/:path* to the service | Makes browser requests same-origin and removes the need for cross-origin approvals |

### 3.3 Technology stack

| Area | Technology | Version | Role |
| --- | --- | --- | --- |
| Service framework | Flask | 2.3.3 | Routing, request handling, JSON responses |
| Cross-origin handling | Flask-CORS | 4.0.0 | Origin permitting for browser calls |
| Production server | Gunicorn | 23.0.0 | Multiple worker processes inside the container |
| Database driver | PyMongo | 4.10.1 | Synchronous access to MongoDB |
| Browser automation | Selenium | 4.15.2 | Control of the headless browser |
| Language models | groq, openai, google-generativeai | 0.9.0 or later, 1.3.0, 0.3.2 | Analysis and content generation |
| Configuration loading | python-dotenv | 1.0.0 | Reading environment files |
| Container base | Debian-based Python image | Per Dockerfile | Hosts the service and the browser engine |
| Interface | Vanilla JavaScript modules | Language standard | No framework and no build step |
| Styling | Tailwind CSS | Current published build | Utility-based styling delivered from a content network |
| Charts | Chart.js | 4.4.4 | Analytical visualisation |
| Map display | Leaflet | 1.9.4 | Geographic presentation of places |

### 3.4 Repository structure

```
map_compete/
  backend/
    api.py                  HTTP service: routes, request guards, orchestration
    database.py             Persistence layer and database interface
    scraper.py              Browser automation and content extraction
    ai_service.py           Language model providers and analysis logic
    topic_classifier.py     Deterministic topic, keyword and sentiment analysis
    place_identity.py       Canonical identity for places on Google Maps
    Dockerfile.backend      Container image definition
    docker-entrypoint.sh    Production start script for Gunicorn
    requirements.txt        Python dependencies
    test_*.py               Database, API and connectivity test programs
  frontend/
    index.html              Single-page application shell and all views
    vercel.json             Rewrite rule that forwards API requests
    nginx.conf              Equivalent proxy rule for the container stack
    css/style.css           Styling beyond the utility framework
    js/app.js               Entry point, tab and dialog behaviour
    js/components/          Dashboard, competitors, posts, analytics, ideas, API client
  docker-compose.yml        Local container composition
  render.yaml               Blueprint for the hosted service
  serve_local.py            Local development server with request forwarding
  verify_deployment.py      Live verification of the deployed and local wiring
  verify_api_base.mjs       Regression program for address resolution
  .env.example              Documented configuration template
```

## 4. Data Model

### 4.1 Storage approach

All application data is held in MongoDB. The database is addressed by a connection string and a database name, both supplied through configuration; the database and its collections are created on first use. No relational database and no local database file are involved, and no structural migration step is required before the application runs.

The persistence layer exposes an application-oriented interface, for example operations to create a project, add a competitor, save a scraped post, record a review, or read the statistics of the most recent collection run. Routes in the service call these operations and never construct queries themselves, which keeps the storage decisions in one module.

### 4.2 Collections

| Collection | Contents | Principal keys |
| --- | --- | --- |
| places | Canonical records of real-world businesses identified on Google Maps, shared between projects | place_key (unique), google_place_id, hex_id, cid, kgmid, name |
| competitors | Businesses monitored inside one project, linked to a place record | project_id, place_id, business_key |
| posts | Public updates collected from competitors, with topic, sentiment and media references | content_hash (unique), post_url, competitor_id, scrape_date, published_date, canonical_post_id |
| post_competitors | Association between a post and every competitor that published identical content | post_id, competitor_id |
| reviews | Public reviews collected from competitor pages, including rating and date | content_hash (unique), project_id, competitor_id |
| keywords | Keywords tracked for a project, whether entered by the operator or suggested | project_id |
| generated_ideas | Content suggestions produced for a project, with a marker for those already used | project_id |
| scraping_logs | One record per collection run with outcome, counts, failures and diagnostics | project_id |
| counters | Monotonic sequences used to allocate small integer identifiers | name |

### 4.3 Identity and duplicate control

Duplicate control is applied at three levels, because the same real-world business and the same published content can be encountered repeatedly.

- Place identity. Each business receives a place key derived from the strongest available identifier, in order of preference: the Google place identifier, then the hexadecimal identifier, then the customer identifier, then the knowledge panel identifier, then a combination of normalised name and address. The place key is unique, so two projects that monitor the same competitor share a single place record while holding separate competitor records.
- Competitor identity. A business key derived from the place identity is stored on the competitor record, which allows the same competitor to be recognised even when its name is written differently.
- Content identity. Every collected post and review is stored with a content hash computed from its normalised text and provenance. The hash is unique, so a repeated collection run cannot insert the same content twice; repeated appearances are counted as duplicates skipped rather than as new content.

Where two competitors publish identical content, one post record is retained and the association collection records both publishers, which allows the interface to show the content once while analytics still count it against each competitor.

### 4.4 Identifier allocation

Small integer identifiers are used in the interface and in the API. They are allocated from a dedicated counters collection using an atomic increment, which guarantees strictly increasing values, prevents reuse after a deletion, and avoids the long hexadecimal identifiers of the storage engine appearing in the user interface.

## 5. Process Description

### 5.1 Process map

The working process of the application consists of seven stages. Stages one to three prepare the monitored set, stage four collects the raw material, stages five and six derive intelligence from it, and stage seven presents it. Each stage stores its outcome before the next stage begins, so a failure in a later stage never invalidates an earlier result.

1. Project registration, in which the monitored business is described and its own Google Maps presence is resolved.
2. Competitor discovery, in which candidate competitors are proposed either from geographic proximity or from national market context.
3. Competitor verification and tracking, in which candidates are resolved to canonical place records and attached to the project.
4. Collection, in which the public Google Maps content of each tracked competitor is retrieved, classified and stored.
5. Analysis, in which topics, keywords, sentiment, ratings and trends are derived and market gaps are identified.
6. Content generation, in which update suggestions and complete update drafts are produced and recorded.
7. Review, in which the operator examines the collected evidence and the suggestions in the interface.

### 5.2 Stage one: project registration

The process begins when the operator creates a project. The interface collects the business name, the profile description, the locality, the field of activity and a flag that states whether the business competes locally or nationally. The service validates that a name is present, allocates a project identifier, and stores the project.

The own-business resolution step then attempts to find the business on Google Maps using the supplied name and locality. When a match is found, the resulting place record is linked to the project and reused, so the monitored business is represented by the same canonical place structure as its competitors. The stored project therefore carries both the operator-supplied description and a resolved place reference where one could be established.

If an operator supplies a Google Maps address directly, the service extracts the identifiers contained in that address and applies them during resolution, which allows an exact match to be established without a search.

### 5.3 Stage two: competitor discovery

Discovery is requested from the competitors view, or from the dashboard, by supplying a company name and, unless the business competes nationally, a geographic location. The service then operates in one of two modes.

- Local mode. The name and location are combined into a search phrase, and the search results of Google Maps for that phrase are examined. The candidate results are filtered to remove the monitored business itself and any competitor already tracked by the project. When the language model is available, the operator-supplied field of activity and the local context are supplied to the model so that the returned candidates are businesses of the same kind, and the model output is reconciled with the search results.
- Online mode. Proximity is not meaningful, so the process identifies nationally operating competitors in the same market segment instead, again combining search results with language model reasoning where the model is available.

Each discovered candidate is returned with the name, the Google Maps address, a category where one is available, and any identifier that could be extracted. Candidates are presented as selectable cards, and no candidate is stored until the operator confirms it. The service reports the number of candidates found, and reports an explicit reason, such as no results or blocked access, when the search could not be completed.

### 5.4 Stage three: verification and tracking

Before a competitor is stored, it is verified. Verification accepts a Google Maps address, an extracted identifier or a typed business name, and resolves it to a canonical place record. The resolution result carries a confidence value and a statement of the identity source that was used, for example an exact identifier match, a name and address match, or a name-only match.

The consequence of verification is that the same competitor cannot enter a project twice under two spellings, and that two projects monitoring the same competitor share one place record while keeping separate competitor records for their own statistics. Verified competitors are added to the project either individually or in a single action, and a competitor that cannot be resolved is reported with the reason rather than being stored with an unknown identity.

Each competitor record also carries the state of its most recent collection, which allows the interface to show whether content has ever been collected for it and when that collection last occurred.

### 5.5 Stage four: collection

Collection is requested per competitor or for the whole project. The per-competitor request performs one complete cycle for one business; the project-wide action performs the same cycle once for each competitor that has a usable address, one competitor at a time, so that partial progress is stored and a single failure does not discard the work already completed.

The cycle performed for each competitor consists of the following steps.

1. The browser is started in headless mode with the configured engine, and the competitor page is opened using its stored Google Maps address.
2. The page is confirmed to have loaded and the business is confirmed to be present, which distinguishes a genuine empty result from a page that never rendered.
3. The updates region of the business profile is located and expanded, and the page is scrolled repeatedly so that the lazily loaded updates are added to the document.
4. Update entries are extracted together with their text, their publication date, their relative age, their media references and their public address.
5. Each extracted entry is classified. Text that carries the summary characteristics of a place suggestion card, such as a rating with a review count in parentheses or an operational label, is rejected and never stored as content.
6. The remaining entries are recorded as collected content, with topic, sentiment and keyword information attached, and duplicate content is identified by its content hash and counted rather than stored again.
7. Media attached to the collected content is downloaded and referenced on the stored record so that images remain available after the original page changes.
8. Review information is collected from the reviews region, including the reviewer name, the rating, the relative date and the text, and stored in the review collection so that rating distribution and review analysis use real values.
9. The statistics of the run are written to the project log, including the number of entries collected, the number of duplicates skipped, the number of images downloaded, the number of failures, the duration and the outcome status of each competitor.
10. Failure conditions are recorded with a specific reason, and the competitor is annotated with its resulting state.

The outcome of each run is therefore expressed as a status with a stated reason, which allows an operator to distinguish between a business that genuinely publishes nothing, a run that was interrupted by an automated verification challenge, a run that was refused by the remote site, and a run that failed inside the automation layer.

### 5.6 Stage five: analysis

Analysis is deterministic wherever possible, so that results do not depend on an external service. The following figures are derived directly from stored content.

- Topic classification. Each piece of content is assigned to a topic using an industry profile that is inferred from the project field and profile text. Separate keyword sets exist for cafes, salons, fashion retail and online commerce, so the same text is classified appropriately for the business domain concerned.
- Keyword frequency, computed across the stored content of the project, with common and non-informative tokens removed.
- Sentiment, derived from the text and, where a rating is present, from that rating, and expressed as a label with a score.
- Rating distribution and review volume, derived from the stored reviews, used to present the rating profile of each competitor.
- Topic trends, computed by comparing the presence of each topic across competitors and across time windows, which yields a direction of travel for each topic rather than a single snapshot.
- Market gaps, identified by comparing the topics that competitors cover with the topics that the monitored business covers, which produces a statement of the subjects that are not yet taken.

Where the language model is available, a narrative analysis is additionally produced through the analysis endpoint and presented with the deterministic figures rather than replacing them. Analysis results that are derived from stored content are available even when no external service can be contacted.

### 5.7 Stage six: content generation

Content generation is requested from the ideas view or from the dashboard. Two kinds of output are produced.

- Individual suggestions, requested with a count. Each suggestion carries the text of a proposed update, the topic it addresses, the keywords it uses and the components it is built from, for example an opening line, a body and a call to action.
- A complete update, which produces a single ready-to-publish Google Maps update assembled from the current competitor activity, with a heading, a body, a call to action and a suggested visual direction.

Generation is grounded in the stored evidence rather than in general knowledge. The prompt is assembled from the topics and keywords observed in the project, the trend figures, the market gaps, the profile and location of the monitored business, and a list of competitor names that must not appear in the output. The exclusion of competitor names is applied when the response is assembled as well as when it is requested, so a suggestion that names a competitor is removed rather than presented.

Every generated suggestion is stored against the project with the topic it addresses, and the operator can mark a suggestion as used. The interface uses that marker to state how many suggestions have already been used, which prevents the same idea being presented repeatedly as new.

### 5.8 Stage seven: review and presentation

The interface presents the results of the preceding stages in five views that share a single project selection.

1. Dashboard. Key figures for the selected project, a competitor landscape table, trending topics, a keyword cloud, the most recent collected content, a suggestion of the day, a market gap summary, collection statistics and an activity log.
2. Competitors. The monitored competitors with their collected counts and states, the discovery panel, and the dialogue for adding a competitor with verification.
3. Posts. The collected content with filters by competitor and by topic, and the full record of an individual item including its media.
4. Analytics. Topic frequency, keyword frequency, rating distribution, market overview and trend analysis, with a dedicated analysis action that produces the narrative summary.
5. Ideas. Generated suggestions with their topics and usage state, together with the complete update draft.

The project selection is held in the page header and applies to every view. Statistics are read from the stored run logs, so the figures presented after a page reload are the figures recorded during collection and not figures recomputed on the fly.

### 5.9 Process control and failure reporting

The process is designed so that every stage fails in a visible and diagnosable way.

- Requests that cannot be served because the database is not reachable are answered with an explicit unavailability response rather than an internal error, and the reason is included without exposing credentials.
- The health endpoint reports the state of the service and of the database separately, so that an operator can distinguish a service that is not running from a service that is running without database access.
- Collection failures are recorded with a reason code, and the reasons are also written to persistent log files, so a failure can be diagnosed after the fact.
- The interface reports the reason for a failed operation in a visible message, and states which address it resolved for the current environment, so that a configuration problem can be identified from the browser alone.
- Long-running operations are performed against a single competitor at a time where possible, which keeps each request inside the timeouts of the hosting platform and preserves partial results.

## 6. Backend Service Description

### 6.1 Bootstrap

The service is a single Flask application that is created when the module is loaded. Configuration is read from the process environment at import time, and environment files are read from the repository root and from the backend directory if they exist, so the same code runs unchanged in local development and in the container. The persistence layer and the language model manager are constructed once and shared by all routes.

The service exposes forty-two routes beneath the /api prefix. Routes are grouped by the resource they address: projects, competitors, keywords, content collected from competitors, reviews, places, analysis, trends, market information, generated ideas and diagnostics.

### 6.2 Request lifecycle

Every request passes through the same sequence.

1. Cross-origin headers are applied according to the configured list of permitted origins, or to all origins when the configuration permits it.
2. A guard examines API requests other than the health endpoint. If the database is not configured or not reachable, the request is terminated immediately with an unavailability response that states the reason, which prevents individual routes from reporting a misleading internal error.
3. The route handler validates the request payload, applies the business rules and calls the persistence layer, the scraper or a language model provider as required.
4. The result is returned as JSON. Errors are returned as JSON with an informative message rather than as a stack trace, and credentials and connection strings are never included in a response.

### 6.3 Response conventions

| Situation | Response |
| --- | --- |
| Success | HTTP 200 with a JSON object containing the requested resource and, where applicable, an operation summary |
| Invalid request payload | HTTP 400 with a message identifying the missing or invalid input |
| Resource not found | HTTP 404 with a message |
| Database not configured or unreachable | HTTP 503 with a message stating the reason and never containing credentials |
| Automation or external service failure | HTTP 502 or HTTP 500 with a reason code such as a verification challenge, refused access, missing result, timeout or browser error |
| Health endpoint, healthy | HTTP 200 with the service status, the database status and a timestamp |
| Health endpoint, database unavailable | HTTP 503 with the service status, the database status and a description of the database problem |

### 6.4 Health and diagnostics

The health endpoint answers even when the database is unavailable, because its purpose is to report the state of the whole system rather than to serve data. It reports the service as healthy or degraded, and it reports the database separately as connected or disconnected. This distinction is what allows a hosting platform and an operator to determine whether a failure belongs to the service or to the database.

A separate diagnostics endpoint reports the state of the scraping environment: whether a browser engine can be located, whether the browser can be started, and whether the remote site can be reached. It does not scrape, so it can be used freely to establish whether collection is possible from the current host.

Collection activity is additionally recorded in persistent log files beneath the backend directory, one for runs and one for errors, so that the history of collection activity survives the request that produced it.

### 6.5 Concurrency and long-running operations

In production the service runs under a multi-process server with a worker count suited to the memory available, and with a request timeout sized for the longest legitimate operation, which is a collection run. Because the server is synchronous, a collection request occupies one worker for its duration; this is the reason the interface performs project-wide collection one competitor at a time, and the reason the health endpoint is deliberately independent of the database so that it remains responsive.

The browser process is started per collection run and closed at the end of that run, whether the run succeeded or failed, so that no browser process accumulates between runs.

## 7. Scraping Subsystem

### 7.1 Purpose and constraint

Competitor activity on Google Maps is not available through an interface intended for programmatic access. The application therefore retrieves it in the same manner as a human visitor, by driving a real browser to the public page and reading the rendered document. This approach keeps the application within publicly available behaviour, but it has two consequences that shape the design: collection is comparatively slow, and it is subject to the same interruptions a human visitor would encounter.

### 7.2 Browser provisioning

The browser is started in headless mode. The engine binary is located in a defined order of preference: an explicitly configured location first, then the conventional locations used by Linux container images, then the system default. This order allows the same code to run on a developer workstation and inside the container image without modification. Where the driver is supplied by the container, no download is performed at run time; where the driver must be obtained, it is obtained before the run rather than during it, so that a slow download cannot be confused with a slow page.

The container image includes the engine and its dependencies so that hosted collection behaves in the same way as local collection, and so that a hosted environment is not missing a component that local development happens to provide.

### 7.3 Extraction

Extraction proceeds from the rendered document rather than from the raw response, because the content of interest is inserted into the page after it loads.

- The page is allowed to settle before the document is read, and the presence of the business itself is confirmed, so that a page that never rendered is reported as a browser or timeout condition rather than as an empty result.
- The region that holds published updates is expanded, because its content is not present while it is collapsed.
- The document is scrolled in successive steps so that entries loaded on demand are added; the number of steps is bounded so that a page that never stops loading cannot occupy the run indefinitely.
- Entries are read with their text, their publication date where present, their relative age, their media references and their public address.

### 7.4 Classification during collection

Not everything that appears in the document is content published by the business. A business profile also contains summary cards for other places and operational labels such as service options. These are recognised by their characteristic shape, for example a rating followed by a review count in parentheses, or one of the known operational labels, and are rejected during collection. This prevents summary information from being stored and analysed as though it were published content, which would distort topic and keyword figures.

Sentiment, topic and keywords are attached to each entry as it is stored, which means that analysis after collection does not need to re-read the original page.

### 7.5 Media handling

Media referenced by collected content is retrieved and stored with the record so that the content remains reviewable after the original page changes. Media that cannot be retrieved is recorded as a failure of that item without discarding the text of the item.

### 7.6 Interruptions and failure classification

Because collection is performed against a publicly visible page, interruptions are expected rather than exceptional. The subsystem classifies the following conditions separately, because they require different responses from an operator.

- A verification challenge, where the remote site requests human confirmation. The run is stopped, the condition is recorded, and the interface offers an explicit resumption step rather than retrying indefinitely.
- Refused or rate-limited access, where the remote site declines to serve the page.
- A selector or layout condition, where the page loads but the expected regions cannot be found, which indicates a change in the target page rather than a fault in the application.
- A timeout or browser error, where the engine fails to start, fails to navigate or is closed unexpectedly.
- An empty result, where the page loads correctly and the business genuinely has published nothing. This is a valid outcome and is recorded as such rather than as a failure.

### 7.7 Performance characteristics

Collection of a single competitor typically takes from tens of seconds to a few minutes, depending on the amount of content and on the number of scroll steps required. Memory use is dominated by the browser process, which is the reason the hosting configuration keeps the worker count low and the reason the browser is closed after each run. The project-wide action therefore divides the work into one request per competitor, so that an interruption affects one competitor only and all previously collected content is already stored.

## 8. Intelligence and Language Model Services

### 8.1 Provider abstraction

Language model access is placed behind a common interface with four operations: analysis of stored content, generation of suggestions, generation of a complete update, and discovery of competitors. Concrete provider classes implement that interface, and a manager class selects the provider that is available and falls back to a second provider when the first fails. The routes address the manager and are therefore independent of which provider is configured.

### 8.2 Providers and configuration

| Provider | Configuration key | Model | Role |
| --- | --- | --- | --- |
| Groq | GROQ_API_KEY | qwen/qwen3.8-27b as the configured default, with openai/gpt-oss-20b and openai/gpt-oss-120b attempted automatically as alternatives | Primary provider for analysis, generation and assisted discovery |
| Google Gemini | GEMINI_API_KEY | gemini-pro | Optional secondary provider, used when configured |
| Legacy alias | GROK_API_KEY | The Groq implementation | Retained so that an earlier configuration key continues to function |

The Groq provider attempts its configured model first and then the alternative models in order, which means that a model being withdrawn or becoming unavailable in an account does not disable the feature. The provider layer logs which model answered, so the behaviour is observable in the service log.

Keys are read from the process environment or from an environment file. No key is present in the source code, and no key is written to the database or returned in a response.

### 8.3 Deterministic fallback

The application remains useful when no provider is configured or when every provider fails. Analysis of topics, keywords, sentiment, rating distribution, trends and market gaps is computed from stored content by the classification module and does not require an external service. Where a provider is unavailable, the corresponding narrative or suggested output is produced from templates assembled from the computed figures, and the interface continues to present the computed analysis. The generation feature therefore degrades from model-authored text to template-authored text rather than failing.

### 8.4 Grounding and constraints

Prompts are constructed from the evidence stored for the project rather than from general instructions alone. The material supplied to the provider includes the observed topics and their frequencies, the observed keywords, the trend directions, the identified market gaps, the profile and location of the monitored business, and the list of competitor names that must not appear in the output. The response is then post-processed: competitor names are removed, empty suggestions are discarded, and each retained suggestion is stored with the topic it addresses so that the interface can report how many have been used.

### 8.5 Failure behaviour

A provider failure is recorded in the log with the reason returned by the provider and the model that was attempted. Because analysis values are computed locally, a provider outage does not prevent an operator from reading the stored figures; only the narrative or suggested text is affected, and the interface reports the failure of the specific action rather than blanking the view.

## 9. Browser Application

### 9.1 Structure

The interface is a single page that is delivered as static files. It is organised as JavaScript modules with no framework and no build step, which means that the files served by the hosting platform are exactly the files in the repository.

| Module | Approximate size | Responsibility |
| --- | --- | --- |
| js/app.js | 7 kilobytes | Entry point, tab switching, dialogs, notifications |
| js/components/api.js | 22 kilobytes | Address resolution and every request to the service |
| js/components/dashboard.js | 61 kilobytes | Dashboard view and its figures |
| js/components/competitors.js | 68 kilobytes | Competitor view, discovery and verification |
| js/components/posts.js | 20 kilobytes | Collected content view and filters |
| js/components/analytics.js | 89 kilobytes | Analytical views, charts and the analysis action |
| js/components/ideas.js | 23 kilobytes | Generated suggestions and the complete update |
| css/style.css | Supporting styles | Presentation beyond the utility framework |

### 9.2 Address resolution

Because the same files are used in development, in the container stack and in the hosted deployment, the address of the service is resolved when the page loads rather than being fixed in the files. The rules are applied in the following order.

1. If an explicit address has been provided by the page, for example by the local development server, that address is used.
2. If the page is not served from a local address, the relative path /api is used, and the hosting platform forwards that path to the service. The browser therefore performs a same-origin request and no cross-origin approval is involved.
3. If the page is served from a local address, the known local addresses are tested, and the first one that identifies itself as this application and reports a connected database is used. The hosted service is tested as a final candidate so that local development remains possible when the local backend cannot reach the database.

The address that was selected is written to the browser console, prefixed with the application name, which makes the resolution observable without a debugging tool.

### 9.3 Interface behaviour

The page header holds the project selector, which applies to every view. Operations that take time, such as discovery, collection and generation, display their progress and report their outcome as a notification. Where a request fails, the reason reported by the service is shown; a failed list request replaces the loading placeholder with an explicit statement, so that a non-responsive system cannot be mistaken for a system that is still loading.

### 9.4 External dependencies

Three libraries are loaded from content networks: the utility styling framework, the charting library and the mapping library. These are the only runtime dependencies of the interface. No package installation is required to serve the frontend and the hosting platform performs no build step.

## 10. Configuration Reference

### 10.1 Environment variables

| Variable | Consumed by | Default | Meaning |
| --- | --- | --- | --- |
| MONGODB_URI | Persistence layer | None | Connection string of the database cluster |
| MONGODB_DATABASE | Persistence layer | competitor_intelligence | Database name inside the cluster |
| GROQ_API_KEY | Language model layer | None | Primary provider key |
| GEMINI_API_KEY | Language model layer | None | Optional secondary provider key |
| GROK_API_KEY | Language model layer | None | Legacy alias for the primary provider key |
| PORT | Service | 10000 | Port the service listens on; the hosting platform supplies its own value |
| CORS_ORIGINS | Service | All origins | Comma separated list of permitted browser origins |
| API_BASE_URL | Local development server | None | Address of the service used when forwarding local requests |
| GUNICORN_WORKERS | Container start script | 3 | Number of worker processes |
| GUNICORN_TIMEOUT | Container start script | 1800 | Request timeout in seconds |

The documented template is .env.example. The environment file itself is excluded from version control, so credentials never enter the repository.

### 10.2 Addresses and ports

| Context | Component | Address | Port |
| --- | --- | --- | --- |
| Hosted | Browser application | https://map-compete.vercel.app | 443 |
| Hosted | Service | https://map-compete.onrender.com | 443 |
| Local | Browser application through the development server | http://localhost:3000 | 3000 |
| Local | Service used directly | http://localhost:10000 | 10000 |
| Local | Service through the container composition | http://localhost:5000 | 5000 |

### 10.3 Where the address of the service is recorded

| Context | Location | Consumed by |
| --- | --- | --- |
| Hosted browser application | frontend/vercel.json, forwarding rule | The hosting platform |
| Container stack | frontend/nginx.conf, proxy rule | The web server in the frontend image |
| Local development, recommended | API_BASE_URL in the environment file, or the command line argument | The local development server |
| Local development, plain file server | The resolution described in section 9.2 | The browser |
| Any context | An explicit address defined by the page before the application loads | The browser, highest priority |

The environment file is not read by the browser. The browser application is delivered as static files without a build step, so there is no stage at which an environment value could be inserted into the delivered files. The value in the environment file therefore configures the local development server, and it is documented in the template so that the project has one visible place in which the service address for local work is stated.

## 11. Deployment Process

### 11.1 Prerequisites

| Item | Purpose |
| --- | --- |
| MongoDB Atlas account with a cluster | Storage of all application data |
| Network access entry for the hosting service | Permission for the service to reach the cluster |
| Render account | Hosting of the containerised service |
| Vercel account | Hosting of the static browser application |
| Primary language model key | Analysis and content generation |

### 11.2 Deployment of the service on Render

The service is deployed as a container so that the browser engine and its system dependencies are present in the runtime image.

1. Create a web service in Render and connect the repository.
2. Select the Docker runtime and set the Dockerfile path to backend/Dockerfile.backend with backend/ as the build context.
3. Set the health check path to /api/health.
4. Provide the environment variables: the database connection string and database name, the language model keys, the permitted origins, and the worker and timeout values. The port is supplied by the platform and must not be set manually.
5. Deploy. The first build takes several minutes because the browser engine and its dependencies are installed into the image.
6. Confirm that the health endpoint reports the service as healthy and the database as connected.
7. Enable automatic deployment from the default branch so that subsequent commits are built and released without manual action.

The blueprint file render.yaml in the repository describes the same service, including the environment variables and the health check path, and can be used to create it through the blueprint mechanism. The file also records the deployment address and the permitted origins so that the configuration is visible in version control.

### 11.3 Deployment of the browser application on Vercel

1. Create a project in Vercel and connect the repository.
2. Set the root directory to frontend so that the rewrite rule is applied.
3. Select the framework preset for a static site with no build command and no output directory, because the files are served as they are stored.
4. No environment variables are required, because the application resolves the service address at run time and forwards API requests through the rule recorded in frontend/vercel.json.
5. Deploy and confirm that the site loads and that a request to an API path is forwarded and answered.
6. Enable automatic deployment from the default branch.

### 11.4 Deployment sequence

The two parts can be deployed in either order, but the following sequence avoids a period in which the interface is reachable while its service is not.

1. Prepare the database cluster and its network access entry.
2. Deploy the service and confirm its health endpoint.
3. Confirm that the forwarding rule in frontend/vercel.json names the deployed service.
4. Deploy the browser application.
5. Confirm the interface end to end.

### 11.5 Post-deployment verification

| Step | Expected result |
| --- | --- |
| Request the health endpoint of the service | Healthy status with the database reported as connected |
| Request an API path on the frontend address | The request is forwarded and answered with a successful response |
| Open the frontend address | The interface loads and the project selector is populated from stored data |
| Open the browser console | The resolved service address is reported and no error is recorded |
| Create a project | The project appears in the selector and is stored |
| Add a competitor with a Google Maps address and verify it | The competitor is resolved to a canonical place and can be stored |
| Request collection for one competitor | A status is recorded with the counts and, where applicable, the reason for failure |
| Request analysis and generation | Both return a result, whether produced by a provider or by the templates |

## 12. Local Development

### 12.1 Prerequisites

Python 3.11 or later, a database cluster reachable from the development machine, and a browser engine for local collection. Network access to a content network is required for the styling and charting libraries.

### 12.2 Installation

```
git clone https://github.com/manasa-prennathan05/map_compete.git
cd map_compete
pip install -r backend/requirements.txt
copy .env.example .env
```

The environment file then requires the database connection string and, optionally, the language model keys and the service address used for local forwarding.

### 12.3 Running the service

```
python backend/api.py
```

The service starts on the configured port and reports its state at the health path. Configuration is read from the environment file at start-up, so a change to a key requires a restart.

### 12.4 Running the interface

Two methods are available and they differ only in how the service address is determined.

- Recommended: start the development server, which serves the interface files, forwards API requests to the selected service, and reports at start-up which service it selected and whether that service reports a connected database.
- Alternative: serve the frontend directory with any static file server. In this method the browser resolves the service address itself using the rules in section 9.2, and the address that was chosen appears in the console.

Where the development machine cannot reach the database, the first method remains usable because the forwarding step can address the hosted service instead.

### 12.5 Verifying a local installation

| Check | Expected result |
| --- | --- |
| Health path of the service | Healthy status with the database reported as connected |
| Project listing through the interface | The stored projects appear in the selector |
| Console of the interface | The resolved service address is reported |
| Diagnostics path | The browser engine is reported as available and the remote site as reachable |

## 13. Testing

### 13.1 Test inventory

| Program | Type | Requires | What it establishes |
| --- | --- | --- | --- |
| backend/test_database_mongo.py | Unit | In-memory database engine | That the persistence layer behaves correctly without a live database |
| backend/test_api_mongomock.py | Contract | In-memory database engine | That the API contract, including the health and unavailability behaviour, is correct |
| backend/test_mongodb.py | Connectivity | Live cluster | That the configured connection string works and that the database is writable |
| backend/api_test.py | Integration | Running service | That the principal routes answer as documented |
| verify_basic_functionality.py | Integration | Repository only | That the core flow, from project creation to content hashing and generation fallback, works |
| verify_frontend_ui.py | End to end | Running service and interface | That every interactive control works against the service |
| verify_api_base.mjs | Unit | Node runtime only | That the service address resolution selects the correct address in each environment |
| verify_deployment.py | End to end | Network access | That the deployed and local parts are correctly connected, including a real browser check |
| backend/node_validate.js | Static | Node runtime only | That the interface markup contains the expected elements and that the modules parse |

### 13.2 Coverage

The suite covers four areas. The persistence and contract tests establish the behaviour of the service without any external dependency, which makes them suitable for continuous execution. The connectivity test establishes that the deployment configuration is valid, which makes it suitable for use after a deployment. The interface and deployment tests establish that a user can complete the workflow and that the parts are connected, which makes them suitable before a release. The static tests establish that the interface files are intact.

### 13.3 Recommended sequence

1. Run the in-memory unit and contract tests while developing.
2. Run the connectivity test after any change to the database configuration.
3. Run the interface verification before releasing, with the service running.
4. Run the deployment verification after releasing, with network access to both hosted parts.

## 14. Operational Notes

### 14.1 Cold start behaviour

On a hosted plan in which the service is suspended when idle, the first request after a period of inactivity is served only after the service has been resumed. During that interval a request through the frontend forwarding rule can be answered with a gateway error. This is a property of the hosting plan rather than of the application, and the recommended handling is to allow up to a minute and to retry, or to keep the service warm with periodic requests. The health endpoint is the cheapest request with which to do so.

### 14.2 Resource limits

The collection subsystem starts a browser engine, which is the most memory-intensive part of the application. On a small hosting instance a collection request can approach the memory limit, in which case the run may be terminated before it completes. Because collection is performed one competitor at a time and each competitor's result is stored before the next begins, a termination of this kind leaves the previously collected content intact. Complete collection of a large competitor set is most reliably performed from a machine with sufficient memory, and the same content is then available to the hosted interface because it is stored centrally.

### 14.3 Database access from a development machine

The cluster accepts connections only from addresses that are listed in its network access configuration. A development machine that is not listed can open a network connection to the cluster but cannot complete the secure handshake, and the service consequently reports the database as disconnected and answers data requests with an unavailability response. The remedy is to add the public address of the development machine to the network access list of the cluster, or to run the interface against the hosted service for that session.

### 14.4 Long-running operations

Discovery, collection and generation can each take from seconds to minutes. The interface reports progress for each of these operations, and the service is configured with a request timeout that accommodates the longest of them. Because the service is synchronous, a long operation occupies one worker until it finishes; the worker count should therefore remain small on a small instance, and the interface avoids issuing several long operations at once.

### 14.5 Diagnostics reference

| Observation | Probable cause and action |
| --- | --- |
| Health path returns 503 stating that the connection string is not configured | The environment variable is absent in the current environment; add it and restart |
| Health path returns 503 with a secure handshake error | The address of the caller is not listed in the network access configuration of the cluster |
| Project list does not fill and the interface reports that the service is unreachable | The resolved service address is not answering; read the resolved address in the console, then check that service |
| Requests fail only from a local page while the hosted page works | The hosted service does not list the local origin, and the request is cross-origin; use the local development server, which forwards requests same-origin |
| Gateway error from the frontend address | The service is suspended or restarting; retry after a minute |
| Collection reports a verification challenge | The remote site requested human confirmation; perform the confirmation step offered by the interface and retry |
| Collection reports a selector condition | The layout of the target page has changed; the extraction selectors require review |
| Generation returns template text | No language model provider could be reached; check the provider key and the service log, which records the model that was attempted |

## 15. Known Limitations and Incomplete Features

The following limitations are stated so that the delivered behaviour is not overestimated.

- Collection depends on the public presentation of the target site. A change in that presentation, or an increase in the frequency of automated verification challenges, affects collection and requires maintenance of the extraction rules.
- Collection is not exhaustive by nature. It reflects what a single visitor session can load, and content that is not rendered during that session is not collected.
- Collection is synchronous. A long run occupies a service worker for its duration, and on a small hosting instance a run may be terminated by the memory limit before completion, in which case the remainder must be collected in a later request.
- Hosted plans that suspend idle services introduce a delay before the first response after inactivity.
- The features that use a language model depend on the availability and the quota of the configured provider. Quota limits and model withdrawals are handled by falling back to alternative models and then to template output, but the quality of the generated text differs between these modes.
- The application has no user accounts and no authentication. It is intended to be operated by a single trusted user, and anyone who can reach the interface can read and modify the stored data.
- Review analysis depends on the volume of reviews that can be retrieved during a collection run, so a competitor with a very large review history is represented by a sample rather than by the complete history.
- Media retrieval is best effort. A media item that cannot be downloaded is recorded as a failure of that item while the associated text is retained.
- Units of measurement and categorisation are inferred from the stored content and are not confirmed with the monitored business.
- Automated test coverage is provided as programs that are run on demand rather than by a continuous integration service, so the tests are only as current as the last manual run.
- The configuration of the hosted service is maintained in the hosting dashboard and mirrored in the blueprint file; the two must be kept in agreement manually.

## 16. Notes for the Reviewer

### 16.1 Suggested review sequence

1. Open the hosted interface and confirm that the project selector is populated. If it is not, the health endpoint of the service will state whether the service or the database is responsible.
2. Open the browser console and read the reported service address. In the hosted deployment it is the relative path /api; in a local deployment it is the address that answered and identified itself as this application.
3. Create a project, add one competitor with a real Google Maps address and verify it. This exercises the verification path, the canonical identity resolution and the stored state of the competitor.
4. Request collection for that competitor and inspect the recorded status, the counts and the reason field, together with the activity log on the dashboard.
5. Open the posts view and confirm that the collected content appears with its topic, sentiment and media, and that repeating the collection does not duplicate it.
6. Open the analytics view and confirm topic frequency, keyword frequency and rating distribution. Run the analysis action and compare the narrative result with the computed figures.
7. Open the ideas view, generate suggestions and mark one as used, then confirm that the count of used suggestions changes.

### 16.2 Access information

The application has no login. No credentials are required or provided, and none are stored in the repository. The hosted interface is reached at the frontend address given at the start of this document, and the service is reached at the backend address. The language model keys and the database connection string are supplied through environment variables and are not present in the repository.

### 16.3 Where evidence is recorded

| Evidence | Location |
| --- | --- |
| Logs of collection runs | The run log file beneath the backend directory |
| Logs of collection errors | The error log file beneath the backend directory |
| Run statistics presented to the operator | The dashboard statistics panel and the scraping logs route |
| State of the scraping environment | The diagnostics route |
| Stored content, reviews and suggestions | The corresponding views of the interface |

## Appendix A. API Surface

The service exposes forty-two routes beneath the /api prefix. Routes marked with a single method are read-only; the remaining routes accept the payloads described in the process section.

```
GET          /api/health
GET          /api/projects
POST         /api/projects
GET          /api/projects/<id>
PUT          /api/projects/<id>
DELETE       /api/projects/<id>
GET          /api/projects/<id>/places
GET          /api/projects/<id>/competitors
POST         /api/projects/<id>/competitors
POST         /api/projects/<id>/discover-competitors
POST         /api/projects/<id>/scrape
GET          /api/projects/<id>/scraping-logs
GET          /api/projects/<id>/scraping-stats
GET          /api/projects/<id>/keywords
POST         /api/projects/<id>/keywords
POST         /api/projects/<id>/analyze
GET          /api/projects/<id>/analytics/topics
GET          /api/projects/<id>/analytics/keywords
GET          /api/projects/<id>/trend-analysis
GET          /api/projects/<id>/market-overview
GET          /api/projects/<id>/market-gaps
GET          /api/projects/<id>/posts
GET          /api/projects/<id>/reviews
GET          /api/projects/<id>/reviews/analytics
GET          /api/projects/<id>/generated-ideas
POST         /api/projects/<id>/ideas
POST         /api/projects/<id>/complete-update
POST         /api/generated-ideas/<id>/use
GET          /api/competitors/<id>
PUT          /api/competitors/<id>
DELETE       /api/competitors/<id>
POST         /api/competitors/<id>/scrape
POST         /api/competitors/verify
GET          /api/posts
GET          /api/posts/<id>
DELETE       /api/keywords/<id>
GET          /api/places
GET          /api/places/<id>
GET          /api/places/autocomplete
POST         /api/places/search
POST         /api/places/resolve
GET          /api/places/diagnostics
```

## Appendix B. Configuration Template

```
# --- Database (MongoDB Atlas) -------------------------------------
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=competitor_intelligence

# --- API keys -----------------------------------------------------
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=
GROK_API_KEY=

# --- Backend link (which API the app talks to) ---------------------
# Optional. The frontend is static and cannot read this file; the value is
# used by serve_local.py, which forwards /api/* to it. The Vercel deployment
# uses the rewrite in frontend/vercel.json instead.
API_BASE_URL=
# API_BASE_URL=https://map-compete.onrender.com/api
# API_BASE_URL=http://127.0.0.1:10000/api

# --- Ports --------------------------------------------------------
PORT=10000
WEB_PORT=3000
API_PORT=5000

# --- Gunicorn (production server inside Docker/Render) ------------
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=1800

# --- CORS ---------------------------------------------------------
# Comma separated permitted origins, or * to permit all origins.
CORS_ORIGINS=*
```

## Appendix C. Glossary

| Term | Meaning in this document |
| --- | --- |
| Collection | The act of retrieving and storing the public content of a competitor |
| Competitor | A business monitored inside a project |
| Content hash | A value computed from normalised content, used to recognise content that has already been stored |
| Discovery | The assisted proposal of candidate competitors from a name and a location |
| Forwarding rule | The configuration that makes the hosting platform pass API requests from the interface to the service |
| Place | A canonical record of a real-world business, shared between projects |
| Place key | The unique identity of a place, derived from the strongest available identifier |
| Project | One monitored business and everything recorded about it |
| Run | One execution of the collection cycle for one competitor |
| Status | The recorded outcome of a run, with a stated reason where the run did not complete normally |
| Verification | The resolution of a competitor to a canonical place record before it is stored |















