# Expedia Clone

Expedia Clone is a small full-stack travel application built from the Hello Agent project structure. A FastAPI backend owns hotel search, booking rules, and stored data, while a Vue frontend owns user input and presentation.

The application uses fictional classroom data and local booking records. It does not connect to Expedia, process payments, or create real reservations.

## Project structure

```text
expedia-clone/
├── backend/               # FastAPI application and backend tests
├── frontend/              # Vue application powered by Vite
├── expedia-clone-data/    # Supplied hotel, trip, user, and booking CSV files
├── docs/                  # Design and verification notes
├── handoffs/              # Current project status
├── prompts/               # Selected project instructions
├── AGENTS.md              # Project rules for coding agents
├── report.md              # Current Part 2 submission report draft
└── README.md
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Check it with `GET /health`.

Run the backend tests with:

```bash
cd backend
.venv/bin/python -m pytest
```

On first startup, the backend creates `backend/data/expedia.sqlite3` and imports
the supplied hotel, trip, traveler, and booking CSV records. Later starts
reuse that database, so created, cancelled, and deleted bookings persist. Set
`EXPEDIA_DB_PATH` to use a different database location, such as an isolated
database for manual verification.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite will print the local development URL when it starts. During development, Vite proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`.

Run the frontend checks with:

```bash
cd frontend
npm test
npm run lint
npm run build
```

## Application behavior

The completed Part 1 checkpoint reads `hotels.csv` and `trips.csv`, connects
their records by `hotel_id`, and displays matching hotel stays. Part 2 keeps the
same case-insensitive, partial-name search while moving application reads to
SQLite after the one-time seed.

Select a traveler to create a booking from a search result. The booking history
comes from FastAPI and supports reading saved records, changing a confirmed
booking to cancelled while retaining it, and permanently deleting a test
booking after an in-page confirmation. The customer-facing interface uses
normal traveler and booking terminology while the project continues to use the
supplied fictional classroom records.
