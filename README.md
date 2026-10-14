# Self-Healing Tool Registry — Automatic Recovery from Runtime API Schema Drift

This repository contains:
- **Phase 1: Foundation Mock API Server** (Runtime schema drift simulation)
- **Phase 2: Self-Healing Recovery Engine** (Automated schema mismatch interception, patch validation, tool registry update, bounded retry, and structured auditing)

The core application code and documentation are located inside [`self-healing-registry/`](./self-healing-registry):

- **Main Application**: [`self-healing-registry/app/main.py`](./self-healing-registry/app/main.py)
- **Tool Registry**: [`self-healing-registry/app/registry.py`](./self-healing-registry/app/registry.py)
- **Patch Validator**: [`self-healing-registry/app/validator.py`](./self-healing-registry/app/validator.py)
- **Recovery Coordinator & Middleware**: [`self-healing-registry/app/recovery.py`](./self-healing-registry/app/recovery.py)
- **Audit Logger**: [`self-healing-registry/app/audit.py`](./self-healing-registry/app/audit.py)
- **Pydantic Models**: [`self-healing-registry/app/models.py`](./self-healing-registry/app/models.py)
- **Test Suites**:
  - Phase 1 Tests: [`self-healing-registry/tests/test_api.py`](./self-healing-registry/tests/test_api.py)
  - Phase 2 Acceptance Tests: [`self-healing-registry/tests/test_recovery.py`](./self-healing-registry/tests/test_recovery.py)
- **Verification Runner**: [`self-healing-registry/run_verification.py`](./self-healing-registry/run_verification.py)
- **Full Documentation**: [`self-healing-registry/README.md`](./self-healing-registry/README.md)

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

### 2. Run All Automated Tests (17 tests)
```bash
pytest self-healing-registry/tests/ -v
# or standalone runner:
python self-healing-registry/run_verification.py
```

### 3. Start the Server
```bash
python run.py
# or:
# cd self-healing-registry && uvicorn app.main:app --reload
```

Visit the interactive Swagger UI at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
