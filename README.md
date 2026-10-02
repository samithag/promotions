# Promotions

A web application for browsing and managing a list of promotions: offers, discounts, and deals, all in one place.

> **Status:** Early development. Sections marked _TBD_ will be completed once the related decisions are made.

## Features

Planned features for the promotion list web app:

- **Promotion list:** browse all current promotions with title, description, discount, and validity dates
- **Search and filter:** find promotions by keyword, bank, category, or status (active, upcoming, expired)
- **Sorting:** sort by newest, ending soon, or discount value
- **Promotion details:** view full terms and conditions for a single promotion
- **Manage promotions:** create, edit, and remove promotions (admin; not built yet)
- **Responsive design:** works on desktop and mobile browsers

## Tech Stack

- **Frontend:** Next.js 16 (App Router, React Server Components), TypeScript, and Tailwind CSS 4, in [`frontend/`](frontend/README.md).
- **Backend:** FastAPI scraper and API, planned in [`doc/webscraper_plan.md`](doc/webscraper_plan.md).

_TBD: database and hosting._

## Prerequisites

- Git
- Node.js 22 or later, with npm (frontend)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/samithag/promotions.git
cd promotions
```

### 2. Install dependencies

```bash
cd frontend
npm install
```

### 3. Configure the environment

The frontend runs on built-in sample data by default. To use the live API, copy `frontend/.env.example` to `frontend/.env.local` and set `PROMOTIONS_API_URL`.

### 4. Run the app locally

```bash
cd frontend
npm run dev
```

Then open http://localhost:3000.

## Running Tests

```bash
cd frontend
npm test
```

## Project Structure

```
doc/        # Plans and design notes
frontend/   # Next.js website (see frontend/README.md)
```

## Contributing

1. Create a branch from `main` using a descriptive name, such as `feature/promotion-filters` or `fix/expired-date-display`.
2. Make your changes, using small, focused commits.
3. **Update this README** in the same PR if your change affects setup, configuration, commands, or features.
4. Open a pull request against `main` and request a review.

## License

_TBD: no license has been chosen yet._
