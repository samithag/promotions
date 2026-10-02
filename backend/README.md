# Promotions backend

Scrapes credit card promotions from Commercial Bank and Sampath Bank every hour and serves them over a REST API (Jira: SCRUM-1). The design is in [`doc/webscraper_plan.md`](../doc/webscraper_plan.md).

## Commands

Run these from `backend/`. [uv](https://docs.astral.sh/uv/) installs Python 3.12 and the dependencies.

| Command | What it does |
|---|---|
| `uv sync` | Install dependencies |
| `uv run alembic upgrade head` | Create or update the database tables |
| `uv run fastapi dev app/main.py` | Start the API at http://localhost:8000 (interactive docs at `/docs`) |
| `uv run python -m app.worker` | Start the scrape worker: scrapes every bank now, then every hour |
| `uv run pytest` | Run the tests (offline; no network or database needed) |
| `uv run ruff check . && uv run ruff format --check .` | Lint and check formatting |
| `uv run alembic revision --autogenerate -m "..."` | Create a migration after changing `app/models` |

## Configuration

Settings come from environment variables or a `.env` file (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./promotions.db` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host/db` |
| `SCRAPE_INTERVAL_MINUTES` | `60` | Time between scrapes of each bank |
| `REQUEST_DELAY_SECONDS` | `1` | Pause between requests to the same site |
| `RAW_DIR` / `RAW_KEEP_PER_BANK` | `data/raw` / `24` | Where raw pages are saved, and how many runs to keep per bank |
| `ADMIN_TOKEN` | not set | Enables `POST /api/v1/scrape-runs`; send it as `X-Admin-Token` |

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/promotions` | Filter by `q`, `bank`, `category`, `status`; sort by `newest`, `ending_soon`, `discount`; `page`, `page_size` (max 100) |
| GET | `/api/v1/promotions/{id}` | One promotion, or 404 |
| GET | `/api/v1/categories?status=` | Every category with its offer count |
| GET | `/api/v1/banks` | Banks being tracked |
| GET | `/api/v1/scrape-runs` | Recent scrape runs, newest first |
| POST | `/api/v1/scrape-runs` | Start a scrape now, for all banks or `{"bank": "combank"}` (admin) |
| GET | `/health` | Liveness check |

Response shapes follow the "Frontend contract" in the plan, which the website relies on.

## How scraping works

1. **Fetch and parse.** Each bank has a scraper in `app/scrapers/`, listed in `registry.py`.
   - **ComBank** (`combank.py`): parses the server-rendered listing page, then fetches each offer's detail page for the terms.
   - **Sampath** (`sampath.py`): reads the site's JSON API, `/api/card-promotions`, one category tab at a time.
2. **Ingest** (`app/services/ingest.py`):
   - Discounts, dates and card types are extracted from the text (`extract.py`), and each offer is put in one of 10 shared categories (`classifier.py`).
   - Offers are matched to stored ones by the bank's own ID. Offers that disappear are marked inactive, not deleted.
3. **Log the run** (`app/services/scrape.py`):
   - Every run is recorded in `scrape_runs`, and its raw responses are saved for debugging.
   - Network errors and 5xx responses are retried 3 times with backoff.

### Blocked runs

Both banks use bot protection. When a site answers but withholds its offers, the scraper raises `BlockedError` and the run is recorded with status `blocked`:

- **ComBank:** the listing page comes back with no offer cards.
- **Sampath:** the API reports a `total` but returns an empty `data` list.

A blocked run doesn't change stored offers. Without this rule, one blocked run would mark every offer as ended. Check `GET /api/v1/scrape-runs` to see whether scraping is healthy.

The scrapers send a clear User-Agent and pause between requests. They do not try to get around bot protection.

## Tests

`tests/fixtures/` holds pages captured from the banks' sites through a normal browser session. Parser tests run against them offline, so they keep passing when the live sites change. When a site's layout changes, save a fresh copy of the page, update the fixture, and fix the parser until the tests pass.

API tests use an in-memory SQLite database. Scraper and worker tests use `httpx.MockTransport` instead of the network.
