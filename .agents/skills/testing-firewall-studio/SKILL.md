# Testing Network Firewall Studio

## Overview
Network Firewall Studio is a full-stack app (FastAPI backend + React/Vite frontend) for managing firewall rules with NGDC naming standards enforcement.

## Local Setup

### Backend
```bash
cd firewall-studio-backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd firewall-studio-frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend `.env` should have `VITE_API_URL=http://localhost:8000` for local testing.

For deployed testing, update `.env` to the deployed backend URL and rebuild with `npm run build`.

## Devin Secrets Needed
- `GITHUB_TOKEN` - GitHub Personal Access Token with repo scope for pushing to sriram-tenneti/network-firewall-studio

## Testing Flows

### Design Studio (http://localhost:5173)
1. **Naming Standards Builder**: Click "Group" radio button in Source panel → Select App ID from dropdown → Select Subtype → Click a Neighbourhood (NH01-NH17) → Verify auto-generated name follows `grp-{AppID}-{NH}-{SZ}-{Subtype}` format
2. **Name Validation**: Type invalid name like "bad-name" in Group/Source Name field → Verify red warning icon and error message appears. Type valid name like `grp-ORD-NH01-GEN-APP` → Verify green checkmark appears
3. **Rule Creation**: Click "+ All" button in ActionBar → Verify green success notification → Verify new rule appears in Rule Lifecycle table with "Compliant" badge and "Draft" status
4. **Lifecycle Actions**: Click "Certify" on a Draft rule → Verify status changes to "Certified" with notification

### Migration Studio
1. Click "Migration Studio" in header nav bar
2. **Migration Planner**: Verify 5 legacy rules shown with NGDC Target mappings using naming standards (grp-/svr-/rng- prefixes)
3. **Filters**: Click "Auto", "New-Group", "Needs Review" filter buttons → Verify correct filtering
4. **NGDC DC Switching**: Click different DCs in NGDC Data Centers sidebar (East/West/Central NGDC) → Verify Neighbourhoods and IPs/Groups update accordingly
5. **Execute Migration**: Click "Update Migration" button → Verify green success notification with migration ID

### Backend API Verification
```bash
# Valid name
curl -s -X POST http://localhost:8000/api/reference/naming-standards/validate \
  -H 'Content-Type: application/json' \
  -d '{"name": "grp-APP001-NH01-CDE-WEB"}'
# Expected: {"valid": true, "type": "group", "parsed": {...}}

# Invalid name
curl -s -X POST http://localhost:8000/api/reference/naming-standards/validate \
  -H 'Content-Type: application/json' \
  -d '{"name": "bad-name"}'
# Expected: {"valid": false, "error": "Name 'bad-name' does not start with a valid prefix..."}
```

## Known Considerations
- Backend uses in-memory storage (Python dicts) - data resets on restart
- ServiceNow CHG and GitOps integrations are stubbed/mock endpoints
- No authentication is implemented - all endpoints are open
- Port 5173 may conflict if another Vite dev server is running; Vite auto-selects next available port
- When exposing via tunnels (deploy expose), Fly.io machine limits may be hit; tunnels are the fallback
- The frontend dev server can sometimes hang on health checks; if `curl localhost:5173` hangs, kill the process and restart
