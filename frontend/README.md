# Self-Healing Tool Registry Dashboard (Phase 4)

A responsive, developer-oriented operational dashboard for monitoring and testing the **Self-Healing Tool Registry**.

Built with **React**, **Vite**, **TypeScript**, and **CSS**.

---

## 1. Features

- **KPI Overview**: Displays real-time metrics directly from `/admin/metrics`:
  - Total Recovery Attempts
  - Successful Recoveries
  - Failed Recoveries
  - Adaptation Rate (%)
  - Mean Time to Recovery (MTTR) in milliseconds
  - Average Retry Count and Patch Rejections
- **Interactive Simulation Sandbox**:
  - Simulate runtime schema drift via `POST /admin/break-api`.
  - Send requests to `POST /student` using presets (Schema v1, Schema v2, Incompatible string, Credential injection) or custom JSON.
  - Toggle `bypass_recovery` to demonstrate raw HTTP 422 failure vs. automatic self-healing HTTP 200 recovery.
  - View response status, latency, headers (`x-self-healing-recovered`), and formatted response body.
  - Reset API & Registry via `POST /admin/reset-api`.
- **Schema Inspector**:
  - Inspect active authoritative schema definition from `/schema`.
  - Side-by-side Before & After drift comparison (Schema v1 vs. Schema v2).
  - Inspect the in-memory Tool Registry (`/registry`) contracts and version history.
- **Structured Audit Trail**:
  - Filterable, searchable table showing all recovery attempts from `/admin/audit-logs`.
  - Displays attempt IDs, timestamps, endpoints, schema transitions, patch decisions, retries, MTTR timings, and status badges.
  - Expandable row inspector showing sanitized original vs. transformed payloads.
- **Recovery Latency Timeline**:
  - Recharts bar chart tracking recovery latencies and success/failure distribution over recent attempts.

---

## 2. Environment Variables

Create or update `.env` in the `frontend/` folder:

```env
# URL of the running FastAPI backend server
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 3. How to Run the Backend and Frontend

### Terminal 1: Start the Backend FastAPI Server
```powershell
# Open terminal in the workspace root
cd "C:\Users\Armaan Mulla\Desktop\Genesis 2.0"

# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Start the mock API and recovery engine
python run.py
```
Backend will be available at:
- API Server: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

### Terminal 2: Start the Frontend Dashboard
```powershell
# Open terminal in the frontend directory
cd "C:\Users\Armaan Mulla\Desktop\Genesis 2.0\frontend"

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
Frontend will be available at:
- Dashboard URL: `http://localhost:5173`

---

## 4. Build for Production

```powershell
cd frontend
npm run build
```
Generates production-ready optimized static bundle in `frontend/dist/`.
Preview production build:
```powershell
npm run preview
```
