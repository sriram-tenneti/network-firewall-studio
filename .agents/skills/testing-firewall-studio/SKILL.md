# Testing Network Firewall Studio

## Environment Setup

### Backend
```bash
cd firewall-studio-backend
pip install -r requirements.txt
pip install openpyxl  # Required for Excel import
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd firewall-studio-frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

Backend must be started before frontend. Frontend calls backend at `http://localhost:8000`.

## Key Test Flows

### 1. Home Screen + Module Navigation
- Navigate to `http://localhost:5173/`
- Verify 3 module cards render: Firewall Studio, NGDC Standardization, Network Firewall Request
- Click each card to verify navigation to `/firewall-studio`, `/ngdc-standardization`, `/firewall-management`
- Each module has its own header with tabs (Rule Designer, Import, Review & Approval, etc.)
- Home button (house icon) in module header returns to home screen

### 2. Compile + Group Submission (Firewall Studio)
- Navigate to Firewall Studio, click "Compile" on a rule (e.g., R-3001 for CRM app)
- Modal title should say "Compile & Submit"
- Below compiled output, verify "Group Submission to Firewall Device" section appears
- For apps WITH groups: shows "All Groups Submitted" with provisioned groups and device commands
- For apps WITHOUT groups: shows "Failed" with "No groups found for app" message
- Test different vendor formats: Generic YAML, Palo Alto, Check Point, Cisco ASA

### 3. Compile + Group Submission (NGDC Migration)
- Navigate to NGDC Standardization, click "Migrate" on a legacy rule
- Proceed through 4-step workflow: Review → IP Mapping → Compile → Submit
- In Step 3 (Compile), click "Compile Rule"
- Verify compiled output renders and group provisioning section shows status
- Legacy rules typically have no matching groups, so expect "Failed" status

### 4. API Verification
- `GET /api/reference/app-dc-mappings` should return 15 seed mappings
- `GET /api/reference/ngdc-mappings` should return 8 seed mappings
- `POST /api/reference/legacy-rules/LR-001/compile` with `{"vendor": "generic"}` should return compiled output with `group_provisioning` field

## Known Gotchas

- **GroupProvisioningSection crash**: If `group_provisioning` returns `{status: "error", message: "..."}` without `provisioned`/`violations` arrays, the component must use optional chaining (`?.`) and nullish coalescing (`?? []`) to avoid crashes. This was fixed in PR #5.
- **React crash recovery**: If the React app crashes (blank page), a hard refresh (`Ctrl+Shift+R`) might not recover it. Restart the Vite dev server (`pkill -f vite` then re-run `npx vite`).
- **Seed data**: Backend auto-seeds data on startup from JSON files in `firewall-studio-backend/data/`. If data looks wrong, restart the backend.
- **Legacy rules have app_id as numeric strings** (e.g., "1316") which don't match group app_ids. This is expected — legacy rules show "No groups found" in group provisioning.

## Devin Secrets Needed
- `GITHUB_TOKEN` — GitHub PAT for pushing to `sriram-tenneti/network-firewall-studio`
