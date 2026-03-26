# Intelligent Finance Mentor

A full-stack project for finance learning and trading guidance with:
- A FastAPI backend for auth and API services
- A React frontend for dashboards and mentoring UI
- ML scripts for historical data processing and strategy experimentation

## Repository Structure

- `backend/` - FastAPI app, database models, auth/security, and ML scripts
- `frontend/` - React app (Create React App)

## Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Git

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend:

```bash
uvicorn main:app --reload
```

Default URL:

- `http://127.0.0.1:8000`

## Frontend Setup

```bash
cd frontend
npm install
npm start
```

Default URL:

- `http://localhost:3000`

## Typical Development Flow

1. Start backend server in one terminal.
2. Start frontend app in another terminal.
3. Open frontend in browser and use API-backed features.

## Git Notes

This repository uses a root `.gitignore` configured for Python and React workflows to prevent committing virtual environments, `node_modules`, and build artifacts.
