# KaliWorkbench

Local Kali/Debian dashboard for orchestrating and visualizing security/hardware CLI workflows. It currently implements the PRD's **Fase 1 foundation** plus module slices from Fase 2–5:

- Fase 1: monorepo, FastAPI backend, React/Vite frontend, supervised process runner with WebSocket log streaming, SQLite (WAL) persistence, workspaces, mandatory target allowlist
- Fase 2: `gitleaks` / `ffuf` / `nuclei` output parsing → `findings` table (`GET /api/jobs/{id}/findings`); HTTP response diff (`POST /api/response-diff`); `tshark` packet capture output parsing for cleartext credential indicators
- Fase 3: ASM pipeline (`POST /api/asm/pipeline`) and snapshot diff (`POST /api/asm/snapshot`, `POST /api/asm/snapshot/diff`)
- Fase 4: LAN coordinator (`POST /api/lan/inspect`), BLE coordinator (`POST /api/ble/inspect`), GATT coordinator (`POST /api/gatt/inspect`)
- Fase 5: findings summary (`POST /api/report/generate`), SARIF 2.1.0 export per job (`GET /api/jobs/{id}/sarif`), Markdown (`GET /api/jobs/{id}/report.md`), HTML (`GET /api/jobs/{id}/report.html`) and PDF (`GET /api/jobs/{id}/report.pdf`) report export, preflight tool checks (`GET /api/preflight`)
- Fase 3/4 additions: asset inventory from nmap XML (`POST /api/asm/parse/nmap`, `POST /api/workspaces/{id}/assets/sync`, `GET /api/workspaces/{id}/assets`), subfinder output parsing (`POST /api/asm/parse/subfinder`), airodump-ng CSV analysis with rogue-AP detection (`POST /api/rf/analyze`)

**Non-loopback startup guard:** the server refuses to bind to a non-loopback `KWB_HOST` unless `KWB_ALLOW_NON_LOOPBACK=true` is also set, and prints an explicit warning. The HTTP surface has a session-token model only — do not expose it to untrusted networks.

**Install (Kali/Debian):** `install/install-kali.sh` provisions dependencies, a `kaliworkbench` system user, `setcap` for `tshark`/`python`, and a `systemd` unit (`install/kaliworkbench.service`). Use `install/verify-kali.sh` to check service and `/health`.

Not yet implemented: `bleak`/`bluetoothctl`/`gatttool` adapters wired into the LAN/BLE/GATT coordinators (they currently run allowlisted argv commands), PDF rendering polish, privileged helper daemon with per-module capability delegation, asset change-alerts pushed as findings. The LAN/BLE/GATT endpoints and the `/api/rf/analyze` endpoint accept real data once the tools are present.

## Prerequisites

- Linux (Kali/Debian target)
- Python 3.11+ (`python3`)
- Node.js 20+ and npm (or pnpm)

## Repository layout

- `backend/` — FastAPI app, SQLite (WAL) database, process supervisor, scope validation, REST/WS APIs
- `frontend/` — React + TypeScript + Vite + Tailwind UI
- `backend/data/` — local runtime data (SQLite DB); gitignored

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the API (binds to `127.0.0.1:8000` by default):

```bash
cd backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On startup the server generates a **session token** and prints it to the console. The API and WebSocket endpoints require this token (`Authorization: Bearer <token>` for REST; `?token=<token>` for WebSocket). Keep the server bound to localhost.

## Frontend setup

```bash
npm install --include=dev
npm run dev:frontend
```

Note: if your shell has `NODE_ENV=production` set (e.g. some CI or Docker defaults), plain `npm install` skips devDependencies — use `--include=dev` explicitly (or `NODE_ENV=development npm install`).

The Vite dev server proxies `/api`, `/health`, and `/ws` to the backend at `http://127.0.0.1:8000` (see `frontend/vite.config.ts`). Open the dev server at `http://localhost:5173` and paste the session token into the header field.

## Security notes

- The server binds to `127.0.0.1` by default and **refuses to start** on a non-loopback host unless `KWB_ALLOW_NON_LOOPBACK=true` is set and the operator accepts the risk. Do not expose the server to untrusted networks; the auth model is a single startup-generated bearer token with no user separation.
- Run the web server as an unprivileged user. Privileged hardware/tool access is intended to be delegated via `setcap`/helper daemon in Fase 4 proper (see `install/install-kali.sh`).
- All command-executing endpoints validate `target` against the workspace allowlist before execution and log denials to `audit_logs`.
- `/api/preflight` and the UI's tool-health grid report which optional tools are installed.

## Development

- Backend tests: `cd backend && source .venv/bin/activate && pytest`
- Backend app imports: `cd backend && source .venv/bin/activate && python -c "from app.main import app; print('OK')"`
- Frontend typecheck: `npm run typecheck:frontend`
- Frontend build: `npm run build:frontend`
- Frontend tests: `npm run test:frontend` (vitest + jsdom)
- All tests: `npm test` (frontend + backend)

## Status

Foundation + module-slices implemented and validated: 55 backend tests passing (nmap/subfinder/airodump parsing, asset inventory roundtrip, runner integration tests, PDF/HTML/Markdown reports), 8 frontend tests passing, frontend typecheck/build clean, allowlist-guarded endpoints. Remaining PRD scope: hardware adapters (`tshark` live capture, `bluetoothctl`/`btmon`/`bleak`), rogue-AP live detection during watch, PDF theming, privileged helper daemon, change-alert notifications.
