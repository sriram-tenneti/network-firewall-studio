# Testing Network Firewall Studio

## Overview
The Network Firewall Studio is a FastAPI + React (Vite/TypeScript/Tailwind/shadcn) app for managing firewall rules, migrations, and organizational config.

## Local Dev Setup

### Backend (FastAPI + JSON file storage)
```bash
cd firewall-studio-backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- JSON data files are auto-created in `firewall-studio-backend/data/` on first startup
- No external database needed - all data stored in JSON files
- Backend runs on http://localhost:8000
- API docs at http://localhost:8000/docs

### Frontend (React + Vite)
```bash
cd firewall-studio-frontend
npm install
npm run dev
```
- Frontend runs on http://localhost:5173
- No authentication required for local testing

## Key Pages to Test
1. **Design Studio** (`/`) - Rule creation, naming standards builder, drag-and-drop destinations, rule lifecycle table
2. **Migration Studio** (`/migration`) - Legacy DC to NGDC migration planner, NGDC sidebar with neighbourhoods/subnets
3. **Org Admin** (`/org-admin`) - 9 tabs: Neighbourhoods, Security Zones, Applications, NGDC Datacenters, Legacy Datacenters, Predefined Destinations, Environments, Policy Matrix, Org Configuration

## Common Pitfalls

### Data Shape Mismatches
The backend JSON storage stores raw data (e.g., neighbourhood IDs as strings like "NH01"), but frontend components may expect enriched objects (e.g., `{name, subnets: string[]}`). The `/api/reference/ngdc-datacenters` endpoint enriches data at the API layer. If new reference data endpoints are added, check whether the frontend expects enriched or raw data.

### Migration Planner Field Names
The migration mappings may use different field names than frontend components expect (e.g., `status` vs `mapping_status`, `ngdc_destination` vs `ngdc_target`). The `MigrationPlannerTable` component handles this with defensive fallbacks. When adding new fields, ensure both backend field name and any frontend aliases are handled.

### JSON File Seed Data
Seed data is populated on first startup via `app/database.py`. If you need to reset data, delete the `data/` directory and restart the backend. The seed data includes:
- 17 Neighbourhoods (NH01-NH17) with IP ranges across 3 NGDC DCs
- 17 Security Zones with IP ranges
- 3 NGDC Datacenters (EAST_NGDC, WEST_NGDC, CENTRAL_NGDC)
- 6 Legacy Datacenters
- 12 Applications
- 7 seed firewall rules
- Sample migration mappings

## Lint & Build
```bash
# Frontend
cd firewall-studio-frontend
npm run lint
npm run build

# Backend - no configured linter, just ensure uvicorn starts without errors
```

## Devin Secrets Needed
- `GITHUB_TOKEN` - GitHub Personal Access Token with repo scope for pushing to https://github.com/sriram-tenneti/network-firewall-studio
