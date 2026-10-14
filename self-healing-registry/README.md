# Self-Healing Tool Registry — Automatic Recovery from Runtime API Schema Drift

**Phase 1 (Mock API Foundation), Phase 2 (Self-Healing Recovery Engine), & Phase 3 (Evaluation, Audit Logging, and Reliability)**

This project provides an automated self-healing middleware and in-memory tool registry that detects API schema drift at runtime, retrieves the trusted active schema, safely validates transformation patches, updates tool contracts, executes bounded retries, records structured audit trails, and computes real-time reliability metrics.

---

## 1. System Architecture

```text
┌─────────────────┐       POST /student {"user_id": "123"}       ┌────────────────────────────────┐
│     Caller      │ ───────────────────────────────────────────> │ Self-Healing ASGI Middleware   │
└─────────────────┘                                              └────────────────────────────────┘
        ▲                                                                      │
        │                                                     Pass 1: Forward original payload
        │                                                                      ▼
        │                                                        ┌───────────────────────────┐
        │                                                        │   Target API Endpoint     │
        │                                                        │   (Active schema: v2)     │
        │                                                        └───────────────────────────┘
        │                                                                      │
        │                                                       Returns HTTP 422 Mismatch
        │                                                                      ▼
        │                                                        ┌───────────────────────────┐
        │                                                        │   Recovery Coordinator    │
        │                                                        └───────────────────────────┘
        │                                                                      │
        │                        ┌─────────────────────────────────────────────┴──────────────────┐
        │                        ▼                                             ▼                  ▼
        │             ┌───────────────────────┐                    ┌──────────────────────┐  ┌──────────────────┐
        │             │  GET /schema (State)  │                    │ Patch Validator      │  │ Tool Registry    │
        │             │  Fetch trusted schema │                    │ Verify compatibility │  │ Update to v2     │
        │             └───────────────────────┘                    │ & Pydantic model     │  └──────────────────┘
        │                                                          └──────────────────────┘           │
        │                                                                      │                      │
        │                                                       Pass 2: Bounded Retry (Max 1)         │
        │                                                       POST /student {"target":{"id":123}}   │
        │                                                                      ▼                      ▼
        │                                                        ┌───────────────────────────┐  ┌───────────────┐
        │                                                        │   Target API Endpoint     │  │ Audit Logger │
        │                                                        │   Returns HTTP 200 OK     │  │ Log attempt & │
        │                                                        └───────────────────────────┘  │ MTTR timing   │
        │                                                                      │                └───────────────┘
        │                                                                      │                      │
        │                                                                      │                      ▼
        │                                                                      │                ┌───────────────┐
        │                                                                      │                │ GET /metrics  │
        │                                                                      │                │ GET /audit    │
        │                                                                      │                └───────────────┘
        └───────────────── Response HTTP 200 (Recovered) ──────────────────────┘
```

---

## 2. Project Structure

```text
self-healing-registry/
├── app/
│   ├── __init__.py           # Package indicator
│   ├── main.py               # FastAPI app, route handlers, middleware & admin endpoints
│   ├── models.py             # Pydantic models for v1, v2 request & response schemas
│   ├── registry.py           # In-memory Tool Registry storing contracts & schema versions
│   ├── validator.py          # Patch proposal validator & Pydantic schema verifier
│   ├── recovery.py           # Recovery Coordinator & SelfHealingASGIMiddleware
│   ├── audit.py              # Structured audit event logger with secret sanitization
│   └── metrics.py            # Evaluation Metrics Calculator (Adaptation Rate, MTTR, Retries)
├── tests/
│   ├── __init__.py           # Test package indicator
│   ├── test_api.py           # Baseline Mock API tests (9 tests)
│   ├── test_recovery.py      # Acceptance tests for Self-Healing Engine (8 tests)
│   └── test_evaluation.py    # Phase 3 Automated Evaluation Suite (12 tests)
├── run_verification.py       # Standalone end-to-end verification script
├── requirements.txt          # Minimal project dependencies
├── EVALUATION.md             # Detailed evaluation report & metrics specification
└── README.md                 # Project documentation
```

---

## 3. Core Modules Explained

| Module | Responsibility |
|---|---|
| [`app/registry.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/registry.py) | Maintains registered tool contracts, active schema versions, and version update history in memory. Updated strictly after patch validation succeeds. |
| [`app/validator.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/validator.py) | Strictly validates proposed migration patches. Ensures data types are convertible (e.g. integer id), forbids credential/token injection, and verifies target Pydantic conformity. |
| [`app/recovery.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/recovery.py) | Pure ASGI middleware and coordinator. Intercepts HTTP 422, fetches trusted schema from `/schema`, validates patch, updates registry, executes bounded retry (max 1 retry), and measures MTTR. |
| [`app/audit.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/audit.py) | Records structured audit entries including attempt UUIDs, timestamps, tool name, schema versions, failure reasons, patch decisions, retry counts, final HTTP statuses, MTTR elapsed time, and outcomes. Sanitizes sensitive keys. |
| [`app/metrics.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/metrics.py) | Computes real-time evaluation metrics: Adaptation Rate, Mean Time to Recovery (MTTR), Average Retry Count, and Patch Rejection Count. Handles empty datasets safely. |
| [`app/main.py`](file:///C:/Users/Armaan%20Mulla/Desktop/Genesis%202.0/self-healing-registry/app/main.py) | Main FastAPI application integrating the mock API, admin controls, schema registry, audit logs, and metrics endpoints. |

---

## 4. Setup and Installation

### 1. Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- `pip`

### 2. Activate Virtual Environment & Install Dependencies

**Windows (PowerShell):**
```powershell
cd "C:\Users\Armaan Mulla\Desktop\Genesis 2.0"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r self-healing-registry/requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r self-healing-registry/requirements.txt
```

---

## 5. Running the Application

### Option A: From Repository Root
```powershell
python run.py
```

### Option B: Direct Uvicorn Command
```powershell
cd self-healing-registry
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Access URLs:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Evaluation Metrics:** [http://127.0.0.1:8000/admin/metrics](http://127.0.0.1:8000/admin/metrics)
- **Recent Audit Logs:** [http://127.0.0.1:8000/admin/audit-logs](http://127.0.0.1:8000/admin/audit-logs)
- **Tool Registry:** [http://127.0.0.1:8000/registry](http://127.0.0.1:8000/registry)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Schema Discovery:** [http://127.0.0.1:8000/schema](http://127.0.0.1:8000/schema)

---

## 6. Testing in Swagger UI (`/docs`)

You can demonstrate the full self-healing lifecycle, audit logs, and metrics directly from the interactive docs:

1. **Step 1: Baseline Request (v1)**
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
   - Expand `POST /student` $\rightarrow$ Click **Try it out**.
   - Ensure payload is `{"user_id": "123"}` $\rightarrow$ Click **Execute**.
   - Returns **HTTP 200 OK** (`"schema_version": "v1"`).
   - Check `GET /registry` $\rightarrow$ `student_service` is on `"v1"`.

2. **Step 2: Simulate Schema Drift**
   - Expand `POST /admin/break-api` $\rightarrow$ Click **Try it out** $\rightarrow$ Click **Execute**.
   - Returns **HTTP 200 OK** confirming active schema switched to `"v2"`.

3. **Step 3: Demonstrate Raw 422 Failure (Bypassed Recovery)**
   - Expand `POST /student`.
   - Set query parameter `bypass_recovery` to `true`.
   - Send payload: `{"user_id": "123"}` $\rightarrow$ Click **Execute**.
   - Returns **HTTP 422 Unprocessable Entity**. Proves that unhealed requests fail validation!

4. **Step 4: Demonstrate Automatic Self-Healing Recovery**
   - In `POST /student`, leave `bypass_recovery` as `false` (default).
   - Send the same old format: `{"user_id": "123"}` $\rightarrow$ Click **Execute**.
   - Notice the response returns **HTTP 200 OK**!
   - Response headers include:
     - `x-self-healing-recovered: true`
     - `x-self-healing-version: v2`
   - Response body shows the record was converted and accepted under v2:
     ```json
     {
       "status": "success",
       "message": "Student record validated successfully against active schema 'v2'.",
       "student_id": 123,
       "schema_version": "v2",
       "data": {
         "target": {
           "id": 123
         }
       }
     }
     ```

5. **Step 5: Inspect Audit Logs (`GET /admin/audit-logs`)**
   - Expand `GET /admin/audit-logs` $\rightarrow$ Click **Try it out** $\rightarrow$ Click **Execute**.
   - View the structured audit event containing UUID, timestamps, patch decision (`APPLIED_AND_VERIFIED_V1_TO_V2`), retry count (`1/1`), MTTR elapsed time (`elapsed_time_ms`), and final status (`200`).

6. **Step 6: Inspect Evaluation Metrics (`GET /admin/metrics`)**
   - Expand `GET /admin/metrics` $\rightarrow$ Click **Try it out** $\rightarrow$ Click **Execute**.
   - View statistical metrics:
     ```json
     {
       "total_recovery_attempts": 1,
       "successful_recoveries": 1,
       "failed_recoveries": 0,
       "eligible_recovery_attempts": 1,
       "adaptation_rate": 100.0,
       "mean_time_to_recovery_ms": 0.65,
       "average_retry_count": 1.0,
       "patch_rejection_count": 0,
       "dataset_status": "populated"
     }
     ```

7. **Step 7: Reset Everything**
   - Expand `POST /admin/reset-api` $\rightarrow$ Click **Try it out** $\rightarrow$ Click **Execute**.
   - Mock API, Tool Registry, and metrics return cleanly to baseline `"v1"`.

---

## 7. Automated Test Suites

### Run All 29 Pytest Tests
```powershell
pytest self-healing-registry/tests/ -v
```

Tests include:
- `test_api.py`: 9 baseline tests covering health, schema discovery, admin breaking, and resetting.
- `test_recovery.py`: 8 acceptance tests covering transparent self-healing, registry updates, invalid patch rejection, retry limit guards, and reset verification.
- `test_evaluation.py`: 12 evaluation tests covering normal requests, automatic recovery, trusted schema queries, security checks, incompatible data, retry boundaries, registry immutability on failure, audit log formats, repeat run consistency, empty metrics handling, and secret sanitization.

### Run End-to-End Verification Runner
```powershell
python self-healing-registry/run_verification.py
```
Outputs formatted step-by-step progress for all 9 verification steps in the terminal.
