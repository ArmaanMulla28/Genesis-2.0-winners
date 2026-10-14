# Self-Healing Tool Registry — Automatic Recovery from Runtime API Schema Drift

This repository contains:
- **Phase 1: Foundation Mock API Server** (Runtime schema drift simulation)
- **Phase 2: Self-Healing Recovery Engine** (Automated schema mismatch interception, patch validation, tool registry update, and bounded retry)
- **Phase 3: Evaluation Suite, Structured Audit Trail & Reliability Metrics** (Automated test evaluation, MTTR & adaptation rate calculations, secret sanitization, and administrative audit inspection)
- **Phase 4: Self-Healing Tool Registry Dashboard** (Developer-oriented dark UI built with React, Vite, TypeScript, and CSS)

The core backend application code and documentation are located inside [`self-healing-registry/`](./self-healing-registry):

- **Main Application**: [`self-healing-registry/app/main.py`](./self-healing-registry/app/main.py)
- **Tool Registry**: [`self-healing-registry/app/registry.py`](./self-healing-registry/app/registry.py)
- **Patch Validator**: [`self-healing-registry/app/validator.py`](./self-healing-registry/app/validator.py)
- **Recovery Coordinator & Middleware**: [`self-healing-registry/app/recovery.py`](./self-healing-registry/app/recovery.py)
- **Audit Logger**: [`self-healing-registry/app/audit.py`](./self-healing-registry/app/audit.py)
- **Metrics Calculator**: [`self-healing-registry/app/metrics.py`](./self-healing-registry/app/metrics.py)
- **Pydantic Models**: [`self-healing-registry/app/models.py`](./self-healing-registry/app/models.py)
- **Test Suites**:
  - Phase 1 Tests: [`self-healing-registry/tests/test_api.py`](./self-healing-registry/tests/test_api.py)
  - Phase 2 Acceptance Tests: [`self-healing-registry/tests/test_recovery.py`](./self-healing-registry/tests/test_recovery.py)
  - Phase 3 Evaluation Tests: [`self-healing-registry/tests/test_evaluation.py`](./self-healing-registry/tests/test_evaluation.py)
- **Evaluation Report**: [`self-healing-registry/EVALUATION.md`](./self-healing-registry/EVALUATION.md)
- **Verification Runner**: [`self-healing-registry/run_verification.py`](./self-healing-registry/run_verification.py)
- **Full Backend Documentation**: [`self-healing-registry/README.md`](./self-healing-registry/README.md)

The frontend application code and documentation are located inside [`frontend/`](./frontend):
- **Frontend App**: [`frontend/src/App.tsx`](./frontend/src/App.tsx)
- **API Service**: [`frontend/src/services/api.ts`](./frontend/src/services/api.ts)
- **Full Frontend Documentation**: [`frontend/README.md`](./frontend/README.md)

---

## Quick Start

### 1. Set Up Environment & Install Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r self-healing-registry/requirements.txt
```

### 2. Run All Automated Tests (29 tests)
```bash
pytest self-healing-registry/tests/ -v
# or standalone runner:
python self-healing-registry/run_verification.py
```

### 3. Start the Backend Server (Terminal 1)
```bash
python run.py
# or:
# cd self-healing-registry && uvicorn app.main:app --reload
```
- API Server: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
- Swagger UI: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
- Metrics endpoint: **[http://127.0.0.1:8000/admin/metrics](http://127.0.0.1:8000/admin/metrics)**
- Audit logs endpoint: **[http://127.0.0.1:8000/admin/audit-logs](http://127.0.0.1:8000/admin/audit-logs)**

### 4. Start the Frontend Dashboard (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
- Dashboard UI: **[http://localhost:5173](http://localhost:5173)**
