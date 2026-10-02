# Web Scraper Plan

Plan for the bank promotions scraper (Jira: SCRUM-1). It runs as the backend of a Python (FastAPI) API.

## Goal

Scrape credit card promotions from two leading Sri Lankan banks every hour, sort them into categories, and build up a dataset over time that the API serves to the web app.

| Bank | Source URL |
|---|---|
| Commercial Bank (ComBank) | https://www.combank.lk/rewards-promotions |
| Sampath Bank | https://www.sampath.lk/sampath-cards/credit-card-offer?firstTab=Other |

## How the sites are built

Both pages were checked before planning, because how a page is built decides how hard it is to scrape.

- **ComBank:** the promotions are plain HTML that comes straight from the server, grouped under headings such as "Food & Restaurants". httpx + BeautifulSoup is enough; no browser is needed.
- **Sampath:** a Nuxt app. The offers are not in the page; the browser loads them from a JSON API, `GET https://www.sampath.lk/api/card-promotions?category=<tab>&page_number=<n>&size=<n>`, one category tab at a time. The scraper reads that API directly.

**Found during implementation:** both sites use bot protection.

- **Sampath:** for scripted requests, the API returns the real `total` but an empty `data` list.
- **ComBank:** couldn't be reached from the development environment at all.

The scraper records these runs as `blocked` and leaves stored offers untouched. It does not try to get around the protection. The parser fixtures were captured through a normal browser session.

## Architecture

```
            ┌──────────────┐   every hour   ┌──────────────────┐
            │  Scheduler   │ ─────────────▶ │  Scraper runner  │
            │ (APScheduler)│                │  per-bank parser │
            └──────────────┘                └────────┬─────────┘
                                                     │ raw offers
                                            ┌────────▼─────────┐
                                            │ Normalise +      │
                                            │ classify + dedupe│
                                            └────────┬─────────┘
                                                     │ upsert
┌───────────┐   REST    ┌──────────────┐    ┌────────▼─────────┐
│ Next.js UI│ ◀───────▶ │  FastAPI     │ ◀─▶│  PostgreSQL      │
└───────────┘           └──────────────┘    └──────────────────┘
```

## Project layout

```
backend/
  app/
    main.py                 # FastAPI app
    core/config.py          # pydantic-settings (DB URL, schedule, user agent)
    db/                     # SQLAlchemy engine/session, Alembic migrations
    models/                 # Bank, Promotion, ScrapeRun
    schemas/                # Pydantic response models
    api/v1/                 # promotions, banks, scrape-runs routes
    scrapers/
      base.py               # BaseScraper: fetch() -> parse() -> list[RawOffer]
      combank.py
      sampath.py
      registry.py           # {"combank": ComBankScraper, ...}
    services/
      classifier.py         # maps offers into one shared set of categories
      ingest.py             # normalise, dedupe, upsert, close expired offers
    worker.py               # scheduler entrypoint (separate process)
  tests/fixtures/           # saved HTML/JSON snapshots per bank
```

Adding a bank later means one new file under `scrapers/` plus one line in the registry.

## Data model

| Table | Key fields |
|---|---|
| `banks` | id, code (`combank`), name, source_url |
| `promotions` | id, bank_id, external_id, title, merchant, description, discount_value, discount_type (% / fixed / installment), card_types, category, bank_category (as the bank labels it), valid_from, valid_to, image_url, source_url, first_seen_at, last_seen_at, is_active |
| `scrape_runs` | id, bank_id, started_at, finished_at, status (running / success / blocked / failed), offers_found, offers_new, offers_closed, error, raw_path |

- **Deduplication:** match on the bank's own ID for the offer: Sampath's record ID, or the slug of ComBank's offer URL. Both banks provide one, so no content hash is needed. Each hourly run inserts new offers and updates `last_seen_at` on existing ones.
- **History:** when an offer disappears from the site, set `is_active = false` instead of deleting it. This builds up the dataset over time and makes "expired" filtering easy.

## Classification

1. Use the bank's own category label as the main signal (ComBank's section headings, Sampath's `category` field).
2. Map both banks onto one shared list of categories: Dining, Supermarket, Travel, Hotels, Fashion, Electronics, Health, Fuel, Online, Other.
3. When a label is missing or unclear, fall back to keyword rules on the title and merchant (for example "restaurant" or "dining" → Dining).
4. Extract the discount with regexes ("20% off", "Rs. 5,000", "0% installment") and the validity dates with `dateparser`.

The first version is rule-based. An LLM classifier can come later if the rules turn out not to be accurate enough.

## Scheduling

- Run APScheduler in its own `worker.py` process, not inside the API. Inside the API, each web worker would start its own scheduler and scrape the same pages several times.
- Run each bank as its own job, so one site failing doesn't block the other.
- Retry with backoff (`tenacity`) and record every run in `scrape_runs`.
- If a queue with retries is needed later, Celery beat + Redis can replace APScheduler without changing the scraper code.
- Scrape politely: respect `robots.txt` (checked once per site per run; a disallowed page makes the run `blocked`), send a clear User-Agent, pause between requests, request each page at most once an hour, and set timeouts.
- Lock each bank while saving a scrape, so a manual scrape and the hourly one can't save the same new offer twice.

## API endpoints (v1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/promotions` | Filter by `bank`, `category`, `status`, `q`; sort by `newest`, `ending_soon`, `discount`; paginated |
| GET | `/api/v1/promotions/{id}` | Details for one promotion |
| GET | `/api/v1/banks` | Banks being tracked |
| GET | `/api/v1/categories` | Categories with offer counts |
| GET | `/api/v1/scrape-runs` | Run history and health |
| POST | `/api/v1/scrape-runs` | Trigger a scrape manually (admin) |
| GET | `/health` | Liveness check |

These cover the search, filter and sorting features listed in the README.

### Frontend contract

The Next.js frontend (`frontend/`, SCRUM-11) already calls these endpoints, so the API must return the following. The TypeScript version is in `frontend/src/lib/promotions/types.ts`.

- **`GET /api/v1/promotions`**
  - **Params:** `q`, `bank`, `category`, `status`, `sort`, `page` (1-based), `page_size`. Each one is optional.
  - **Response:** `{ items: Promotion[], total, page, page_size }`.
  - **`page_size` up to 50 must be accepted.** The home page asks for 50 offers to count those ending this week.
- **`GET /api/v1/promotions/{id}`:** one `Promotion`, or 404 if it doesn't exist.
- **`GET /api/v1/categories?status`:** `[{ slug, label, count }]` for every category, including those with a count of 0.
- **`bank`:** the bank code (`combank`, `sampath`), not `bank_id`.
- **`category`:** a lowercase slug of the shared categories (`dining`, `supermarket`, `travel`, `hotels`, `fashion`, `electronics`, `health`, `fuel`, `online`, `other`).
- **`status`:** derived from the validity dates in Sri Lankan time.
  - `expired` when `is_active` is false or `valid_to` is past.
  - `upcoming` when `valid_from` is in the future.
  - `active` otherwise.
  - Leaving it out means every status.
- **`sort=discount`:** percentage offers first, largest first. Then fixed amounts, then installment plans, then offers with no discount.
- **`discount_type`:** `percentage`, `fixed` or `installment`. `discount_value` is the percent, the rupee amount, or the number of 0% installment months.
- **Dates:** `valid_from` and `valid_to` are ISO dates (`YYYY-MM-DD`) or null. `first_seen_at` and `last_seen_at` are ISO timestamps.

## Testing

- **Parser tests:** run each parser against saved HTML/JSON snapshots in `tests/fixtures/`. They run offline and don't break when the live site changes.
- **Unit tests** for the classifier and the discount/date extraction.
- **API tests** with `TestClient` against a test database.
- **Live check:** a separate test that hits the real sites, run by hand or nightly, to catch layout changes early.

## Phases

1. **Skeleton:** FastAPI app, config, Postgres via docker-compose, Alembic, models.
2. **ComBank scraper:** parser, fixture tests, and the save/dedupe step.
3. **Sampath scraper:** find the content API or parse the embedded data.
4. **Classifier:** shared categories plus discount/date extraction.
5. **Hourly worker:** scheduler, retries, and run logging.
6. **Read API:** endpoints, plus README updates (tech stack, setup, commands).

## Libraries

`fastapi`, `uvicorn`, `sqlalchemy` 2.x, `alembic`, `pydantic-settings`, `psycopg`, `httpx`, `beautifulsoup4` + `lxml`, `apscheduler`, `tenacity`, `pytest`.

`dateparser` turned out not to be needed. The banks use a small set of date formats that a regex handles, and Sampath supplies timestamps. Playwright was not added (see the note on bot protection above).

## Decisions

- **Database:** Postgres in Docker Compose; SQLite for local development and tests.
- **Debit cards:** included. `card_types` records the card networks and kinds an offer mentions (for example `["Visa", "Mastercard", "Credit", "Debit"]`), so the UI can filter on them later.
- **Raw pages:** kept. Each run saves the HTML/JSON it fetched under `data/raw/<bank>/<timestamp>/`, keeping the newest 24 runs per bank. The path is stored in `scrape_runs.raw_path`.
