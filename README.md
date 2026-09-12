# Expedia Clone

Expedia Clone is a small full-stack travel application built from the Hello Agent project structure. A FastAPI backend owns hotel search, booking rules, and stored data, while a Vue frontend owns user input and presentation.

The application uses fictional classroom data and simulated bookings. It does not connect to Expedia, process payments, or create real reservations.

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
├── report.md              # Part 1 submission report
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

Part 1 is implemented. It reads `hotels.csv` and `trips.csv`, connects their records by `hotel_id`, and displays matching hotel stays in the frontend. Search is case-insensitive and accepts a full or partial hotel name.

Part 2 is not implemented. It will import the supplied hotel, trip, user, and booking records into SQLite and add booking CRUD after Part 1 is reviewed.
