# Promotions

A web application for browsing credit card promotions from Sri Lankan banks. Offers are scraped every hour from Commercial Bank (ComBank) and Sampath Bank, sorted into categories, and shown on one site.

## Features

- **Promotion list:** browse current promotions with merchant, discount, and validity dates
- **Search and filter:** find promotions by keyword, bank, category, or status (active, upcoming, expired)
- **Sorting:** sort by newest, ending soon, or discount value
- **Promotion details:** view the full terms and conditions for a single promotion
- **Hourly scraping:** offers are collected from both banks every hour and kept as history when they end
- **Manage promotions:** create, edit, and remove promotions (admin; not built yet)
- **Responsive design:** works on desktop and mobile browsers

## Tech Stack

- **Frontend:** Next.js 16 (App Router, React Server Components), TypeScript, and Tailwind CSS 4, in [`frontend/`](frontend/README.md).
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, and an APScheduler scrape worker, in [`backend/`](backend/README.md). The design is in [`doc/webscraper_plan.md`](doc/webscraper_plan.md).
- **Database:** PostgreSQL (SQLite for local development and tests).
- **Deployment:** Docker Compose.

_TBD: hosting._

## Prerequisites

- Git
- Docker, to run the whole stack
- For local development without Docker:
  - Node.js 22 or later, with npm (frontend)
  - [uv](https://docs.astral.sh/uv/) (backend; it installs Python 3.12 for you)

## Getting Started

### Run everything with Docker

```bash
git clone https://github.com/samithag/promotions.git
cd promotions
docker compose up -d --build
```

This starts four services:

| Service | What it does | URL |
|---|---|---|
| `frontend` | The website | http://localhost:3000 |
| `backend` | The REST API; runs database migrations on start | http://localhost:8000 (docs at `/docs`) |
| `worker` | Scrapes both banks at startup, then every hour | none |
| `db` | PostgreSQL | none |

Optional settings go in a `.env` file at the repo root:

- `ADMIN_TOKEN=...` enables `POST /api/v1/scrape-runs` for triggering a scrape by hand.
- `PROMOTIONS_API_URL=` (set to empty) makes the frontend show its built-in sample data instead of calling the API.

Stop the stack with `docker compose down`. Add `-v` to also delete the database.

### Run without Docker

Backend (uses a SQLite file by default):

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py     # API on http://localhost:8000
uv run python -m app.worker        # scrape worker, in a second terminal
```

Frontend:

```bash
cd frontend
npm install
PROMOTIONS_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

Leave out `PROMOTIONS_API_URL` to run the frontend on sample data.

## Running Tests

```bash
cd backend && uv run pytest     # parsers, extraction, ingest, worker, API
cd frontend && npm test         # data layer and formatting
```

## Project Structure

```
backend/      # FastAPI API, scrapers and worker (see backend/README.md)
doc/          # Plans and design notes
frontend/     # Next.js website (see frontend/README.md)
compose.yaml  # Local Docker deployment
```

## Contributing

1. Create a branch from `main` using a descriptive name, such as `feature/promotion-filters` or `fix/expired-date-display`.
2. Make your changes, using small, focused commits.
3. **Update this README** in the same PR if your change affects setup, configuration, commands, or features.
4. Open a pull request against `main` and request a review.

## License

_TBD: no license has been chosen yet._
