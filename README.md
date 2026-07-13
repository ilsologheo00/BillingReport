# BillingReport

Internal webapp that syncs license/subscription purchases from StreamOne ION and
reports them per customer, alongside our cost, the price charged to the client,
and our margin.

- **Cost** per license line comes from StreamOne ION.
- **Price** charged to each client is entered and maintained manually in this app
  (ION has no concept of what we charge our customers).
- **Margin** = price − cost, computed per license line and aggregated per customer.

No StreamOne ION API credentials were available when this was built, so the app
ships with a **mock ION provider** (deterministic sample customers/licenses) that
lets you run the whole flow — sync, browse customers, set prices, see margin —
today. Flip one env var to switch to the real API once credentials and API docs
are in hand.

## Stack

- Backend: Python, FastAPI, SQLAlchemy + SQLite, JWT auth (single admin user)
- Frontend: React + TypeScript (Vite)

## Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # edit ADMIN_USERNAME / ADMIN_PASSWORD / JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev                       # http://localhost:5173
```

Log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `backend/.env` (seeded
into the database on first startup).

## Switching to the real StreamOne ION API

1. Obtain ION API credentials (client id/secret) and confirm the token and
   resource endpoint paths from ION's API documentation.
2. In `backend/.env`, set:
   ```
   ION_MODE=live
   ION_TOKEN_URL=...
   ION_BASE_URL=...
   ION_CLIENT_ID=...
   ION_CLIENT_SECRET=...
   ION_CUSTOMERS_PATH=...
   ION_SUBSCRIPTIONS_PATH=...
   ```
3. If ION's JSON response fields differ from the guessed shape, adjust the
   `_map_customer` / `_map_line` methods in
   `backend/app/services/ion/live_provider.py` — that's the only place response
   parsing happens.
4. Restart the backend and click "Sync Now". A failed sync surfaces its error
   in the UI and in `GET /api/sync/status` rather than crashing the app.

## How pricing/margin persists across syncs

License lines (`LicenseLine`) are fully overwritten on every sync — ION is the
source of truth for cost. Prices (`SellPrice`) are stored separately, keyed by
`(customer, sku)`, and are **never touched by sync**, so manually-entered
pricing survives renewals and repeated syncs.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```
