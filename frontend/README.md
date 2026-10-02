# Promotions frontend

The Next.js site that shows the credit card promotions scraped from Commercial Bank and Sampath Bank (Jira: SCRUM-11).

## Commands

Run these from `frontend/`. Node.js 22 or later is required.

| Command | What it does |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Start the dev server at http://localhost:3000 |
| `npm test` | Run the unit tests (Vitest) |
| `npm run lint` | Lint with ESLint |
| `npm run typecheck` | Type-check with TypeScript |
| `npm run build` / `npm start` | Build and serve the production site |

## Docker

The `Dockerfile` builds Next.js in standalone mode (`output: "standalone"`) and runs the minimal server as a non-root user on port 3000. From the repo root:

```bash
docker compose up -d --build   # build and start
docker compose down            # stop
```

To build and run it on its own:

```bash
docker build -t promotions-frontend .
docker run -p 3000:3000 -e PROMOTIONS_API_URL=http://host.docker.internal:8000 promotions-frontend
```

`PROMOTIONS_API_URL` is read when the server handles each request, not at build time, so one image works for every environment.

## Data source

The site reads promotions through a `PromotionsRepository` (`src/lib/promotions/`):

- **Sample data (default):** with no configuration, the site serves built-in sample offers (`mock-data.ts`) and shows a notice saying so. Their dates are relative to today, so there is always a mix of running, upcoming and ended offers.
- **Live API:** copy `.env.example` to `.env.local` and set `PROMOTIONS_API_URL` to the FastAPI backend (`backend/`). `docker compose up` sets this automatically. The site then calls the `/api/v1` endpoints from `doc/webscraper_plan.md`. Responses are cached for 5 minutes, since offers are scraped hourly.

The response shapes the site expects are set out under "Frontend contract" in [`doc/webscraper_plan.md`](../doc/webscraper_plan.md#frontend-contract). If `PROMOTIONS_API_URL` has a path prefix (for example `https://host/promotions`), it is kept. If the API returns an error, or a 404 from a list endpoint, the site shows its error page rather than an empty list.

## How it works

- **Server-rendered pages:** `/` (offer list) and `/promotions/[id]` (offer details) fetch data in React Server Components.
- **State in the URL:** search, filters, sort and page are query params (for example `/?bank=sampath&category=dining&sort=ending_soon`), so every view can be shared and the back button works. `FilterBar` is the only client component that changes them.
- **Dates:** offer status (running, upcoming, ended) is worked out from the validity dates using Sri Lankan time.

## Project structure

```
src/
  app/
    page.tsx                  # Offer list: hero, filters, results, pagination
    promotions/[id]/page.tsx  # Offer details
    loading.tsx, error.tsx, not-found.tsx
  components/                 # CardFace, PromotionCard, FilterBar, Hero, ...
  lib/
    format.ts                 # Discount, date and validity formatting
    promotions/
      types.ts                # Domain types, banks, categories, sorts
      query.ts                # URL search params <-> PromotionQuery
      status.ts               # Running / upcoming / ended logic
      sort.ts                 # Sort orders
      mock-data.ts            # Sample offers
      mock-repository.ts      # In-memory filtering, sorting, paging
      http-repository.ts      # FastAPI client
      index.ts                # getRepository(): picks mock or HTTP (server only)
      test-utils.ts           # Test fixtures
    *.test.ts                 # Unit tests sit next to the code they test
.env.example                  # PROMOTIONS_API_URL
vitest.config.mts
```
