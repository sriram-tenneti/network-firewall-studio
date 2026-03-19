# Testing Network Firewall Studio

## Environment Setup

### Backend (Python/FastAPI)
```bash
cd firewall-studio-backend
pip install -r requirements.txt
pip install openpyxl python-multipart
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (React/Vite)
```bash
cd firewall-studio-frontend
npm install
npm run dev -- --host 0.0.0.0
```

Frontend runs on port 5173, backend on port 8000.

## Important: Data Seeding

- The backend uses JSON file storage in `firewall-studio-backend/data/`
- On first startup, `seed_database()` creates all JSON files with seed data
- **The seed check is based on `neighbourhoods.json` existence** — if ANY data file exists, it skips ALL seeding
- To force a full re-seed (e.g., after changing SEED_LEGACY_RULES), delete the entire `data/` directory and restart the backend
- If only `legacy_rules.json` is deleted, the seed won't re-run because `neighbourhoods.json` still exists

## Navigation

| Page | URL Path | Header Link |
|------|----------|-------------|
| Firewall Studio | `/` | "Firewall Studio" |
| Migration to NGDC | `/migration` | "Migration to NGDC" |
| Review & Approval | `/review` | "Review & Approval" |
| Firewall Management | `/management` | "Firewall Management" |
| Data Import | `/import` | "Data Import" |
| Settings | `/settings` | "Settings" |

## Key Testing Workflows

### 1. Legacy Rule Display & Expanded IPs
- Navigate to Migration to NGDC (`/migration`)
- Verify legacy rules load with all 17 columns
- Click "View" on any rule to open detail modal
- Verify expanded IP tree sections (Source, Destination, Service) render hierarchically

### 2. Submit for Review → Review & Approval
- On Migration to NGDC page, check boxes next to rules
- "Submit for Review" and "Migrate to NGDC" buttons appear when rules are selected
- Click "Submit for Review" — rules change to "In Progress" status
- Navigate to Review & Approval (`/review`) — submitted rules appear as "Pending"

### 3. Excel Import with Deduplication
- Navigate to Data Import (`/import`)
- Click "Choose Excel File" and upload an .xlsx file
- Expected columns: App ID, App Current Distributed ID, App Name, Inventory Item, Policy Name, Rule Global, Rule Action, Rule Source, Rule Source Expanded, Rule Source Zone, Rule Destination, Rule Destination Expanded, Rule Destination Zone, Rule Service, Rule Service Expanded, RN, RC
- Result shows added count and duplicate count
- Uploading the same file twice should show all as duplicates on second import

### 4. Migration to NGDC (Rule Separation)
- Select rules on Migration to NGDC page
- Click "Migrate to NGDC"
- Rules disappear from Migration to NGDC AND Firewall Management pages
- Migration is logged in history

### 5. Firewall Management
- Navigate to Firewall Management (`/management`)
- Only non-migrated legacy rules appear
- "Export Spreadsheet" exports CSV with all 17 columns
- IP/Subnet Exceptions section at bottom

## Common Issues

- **`python-multipart` not installed**: Backend crashes on startup with `RuntimeError: Form data requires "python-multipart"` — install with `pip install python-multipart`
- **Stale data files**: If legacy rules show old format (with `rule_name`, `source_entries` etc.), delete `firewall-studio-backend/data/` and restart
- **Build errors in MappingPanel**: If LegacyRule type changes, MappingPanel.tsx may need updating since it references LegacyRule fields directly
- **Route mismatch**: Routes are defined in App.tsx — Firewall Management is at `/management` not `/firewall-management`

## Build Verification
```bash
cd firewall-studio-frontend
npm run build  # Should complete with 0 errors
```

## Devin Secrets Needed
- `GITHUB_TOKEN` — GitHub Personal Access Token with repo scope for pushing to sriram-tenneti/network-firewall-studio
