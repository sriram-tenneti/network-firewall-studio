# Network Firewall Studio - Local Setup Guide

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11 or higher | https://www.python.org/downloads/ |
| **Node.js** | 18 or higher | https://nodejs.org/ |
| **Git** | Any recent version | https://git-scm.com/download/win |

> No database required. All data is stored in JSON files that are auto-created on first startup.

---

## Quick Start (Windows PowerShell)

### 1. Clone the Repository

```powershell
git clone https://github.com/sriram-tenneti/network-firewall-studio.git
cd network-firewall-studio
```

### 2. Start the Backend

Open a **PowerShell terminal**:

```powershell
cd firewall-studio-backend

# Create a virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

A `data/` folder will be auto-created with seed data (17 neighbourhoods, 17 security zones, etc.).

### 3. Start the Frontend

Open a **second PowerShell terminal**:

```powershell
cd firewall-studio-frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

You should see:
```
VITE v6.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### 4. Open the App

Navigate to **http://localhost:5173** in your browser (Chrome recommended).

---

## Pages

| Page | URL | Description |
|------|-----|-------------|
| **Design Studio** | http://localhost:5173 | Create firewall rules with naming standards, drag-and-drop destinations, compliance validation |
| **Migration Studio** | Click "Migration Studio" in header | Migrate legacy DC rules to NGDC with neighbourhood/security zone mapping |
| **Org Admin** | Click "Org Admin" in header | Manage all organizational config: Neighbourhoods, Security Zones, Applications, Datacenters, Policy Matrix, etc. |

---

## API Documentation

Once the backend is running, Swagger/OpenAPI docs are available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Troubleshooting

### PowerShell Execution Policy Error
If you get an error running `.\venv\Scripts\Activate.ps1`:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found
Make sure Python is in your PATH. During installation, check "Add Python to PATH".

### Port Already in Use
If port 8000 or 5173 is in use:
```powershell
# Backend on different port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Frontend on different port
npx vite --port 5174
```

If you change the backend port, update `firewall-studio-frontend/.env`:
```
VITE_API_URL=http://localhost:8001
```

### Reset Data
Delete the `firewall-studio-backend/data/` folder and restart the backend. Fresh seed data will be regenerated.

---

## Quick Start (macOS / Linux)

```bash
# Clone
git clone https://github.com/sriram-tenneti/network-firewall-studio.git
cd network-firewall-studio

# Backend (Terminal 1)
cd firewall-studio-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd firewall-studio-frontend
npm install
npm run dev
```

---

## Project Structure

```
network-firewall-studio/
├── SETUP.md                          # This file
├── firewall-studio-backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── database.py               # JSON file storage + seed data
│   │   ├── routes/
│   │   │   ├── rules.py              # Firewall rule CRUD endpoints
│   │   │   ├── migrations.py         # Migration workflow endpoints
│   │   │   ├── reference.py          # Reference data CRUD (NHs, SZs, DCs, Apps)
│   │   │   └── policy.py             # Policy validation endpoint
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic models
│   │   └── services/
│   │       └── naming_standards.py   # Naming standards validation engine
│   ├── data/                         # Auto-created JSON data files
│   ├── requirements.txt              # pip dependencies
│   └── pyproject.toml                # Poetry config (alternative)
├── firewall-studio-frontend/
│   ├── src/
│   │   ├── App.tsx                   # React router
│   │   ├── pages/                    # Design Studio, Migration Studio, Org Admin
│   │   ├── components/               # UI components
│   │   ├── lib/api.ts                # Backend API client
│   │   └── types/index.ts            # TypeScript interfaces
│   └── package.json
└── docs/
    ├── architecture/C4-ARCHITECTURE.md
    ├── workflows/WORKFLOW-DIAGRAMS.md
    └── confluence/Network-Firewall-Studio-Architecture.html
```
