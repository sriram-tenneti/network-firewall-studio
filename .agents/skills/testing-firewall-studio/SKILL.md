# Testing Network Firewall Studio

## Overview
Network Firewall Studio is a full-stack app with a Python/FastAPI backend and React/Vite frontend for managing firewall rules, NGDC migration, and compliance.

## Starting the App Locally

### Backend
```bash
cd firewall-studio-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- Backend serves API at `http://localhost:8000`
- Seed data (261 legacy rules across 27 apps, 3 environments) is auto-loaded on first startup
- Data is stored as JSON files in `data/` directory — delete this folder to reset to seed data

### Frontend
```bash
cd firewall-studio-frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
- If port 5173 is in use, Vite auto-selects the next available port (e.g. 5174) — check the terminal output
- Frontend calls backend at `http://localhost:8000` (configured in `src/lib/api.ts` as `API_BASE`)

## Key Pages and Routes

| Route | Page | Module |
|-------|------|--------|
| `/` | Home | Landing page with module cards |
| `/firewall-management` | Firewall Management | View/modify legacy rules |
| `/firewall-management/import` | Import Rules (Excel) | Upload .xlsx with env selector |
| `/firewall-management/review` | Review & Approval | Review change requests |
| `/ngdc-standardization` | Migration Studio | Legacy-to-NGDC migration |
| `/ngdc-standardization/import` | Import from FM | Import FM rules for NGDC |
| `/firewall-studio` | Design Studio | NGDC-standardized rules |
| `/admin` | Admin Panel | App-env assignments, naming standards, policy matrix, org config |
| `/migration-studio` | Alias for Migration Studio | Legacy route |
| `/design-studio` | Alias for Design Studio | Legacy route |

## Testing Excel Import with Environment Stamping

This is a critical flow — imported rules must inherit the environment selected during import.

### Create a test Excel file
```python
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
headers = ['App ID', 'App Current Distributed ID', 'App Name', 'Inventory Item', 'Policy Name', 'Rule Global', 'Rule Action', 'Rule Source', 'Rule Source Expanded', 'Rule Source Zone', 'Rule Destination', 'Rule Destination Expanded', 'Rule Destination Zone', 'Rule Service', 'Rule Service Expanded', 'RN', 'RC']
ws.append(headers)
ws.append(['TEST01', 'TEST01D', 'Test Import App', 'TEST-INV-001', 'FW-TEST', 'No', 'Accept', '192.168.1.10', 'svr-192.168.1.10', 'DMZ', '10.0.0.20', 'svr-10.0.0.20', 'Internal', 'tcp/443', 'tcp/443', 'RN001', 'RC001'])
wb.save('test-import-rules.xlsx')
```

### Test Steps
1. Navigate to `/firewall-management/import`
2. Select environment from dropdown (e.g. "Non-Production")
3. Click upload area → select `.xlsx` file → click "Import"
4. Verify success message
5. Navigate to `/firewall-management` → click the Non-Production tab
6. Search for the imported app ID (e.g. "TEST01") → confirm rules appear
7. Switch to Production tab → confirm the imported rules do NOT appear

### How it works
- Frontend (`DataImportPage.tsx`) passes `selectedEnv` to `importLegacyRulesExcel(file, selectedEnv)`
- API (`api.ts`) appends `?environment=<env>` query parameter to the import endpoint
- Backend (`reference.py`) stamps `rule["environment"] = environment` on every parsed row before saving

## Environment Filtering

All three main pages (Firewall Management, Migration Studio, Design Studio) have environment tabs:
- **Production** / **Non-Production** / **Pre-Production**
- Rules are filtered by their `environment` field
- Tab badges show rule counts per environment

## Common Issues

- **Port conflicts**: If Vite says port is in use, check the actual port in terminal output
- **CORS errors**: Backend has CORS middleware allowing all origins; if you see CORS errors, check that the backend is actually running
- **"Failed to load data" on legacy routes**: Routes like `/migration-studio` and `/design-studio` are aliases — if they show errors, check `App.tsx` has proper route definitions (not just redirects)
- **NGDC compliance check TypeError**: The `check_ngdc_compliance` function in `database.py` may fail if naming standard prefix values are dicts instead of strings. The fix filters prefix values to ensure only strings are used.

## TypeScript Build Check
```bash
cd firewall-studio-frontend
npx tsc -b --noEmit
```

## Devin Secrets Needed
- `GITHUB_TOKEN` — for pushing to the repo and creating PRs
