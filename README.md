# GUARDIAN GO
### AI-Powered Safe Caregiver & Family Care Platform
> *"Verified care. Connected safety. Peace of mind."*

---

## 1. Project Overview
**Guardian Go** is a hackathon-ready, full-stack childcare and family care platform designed to guarantee child safety, caregiver trust, and real-time peace of mind for parents. It integrates **4-gate caregiver trust verification**, **simulated Bluetooth Low Energy (BLE) child beacon proximity tracking**, **1-tap Emergency SOS escalation**, and a **local Qwen 3 4B AI Safety Assistant (via Ollama)** with a zero-crash offline safety engine fallback.

---

## 2. Key Features
- **3 Role-Based Portals**: Dedicated UI dashboards for **Parents**, **Guardians (Caregivers)**, and **Admin Control Center**.
- **4-Gate Caregiver Verification**: Identity, Criminal Background Check, First Aid & CPR, and Document Verification standards.
- **BLE Child Beacon Tracking**: Simulated hardware proximity monitor tracking RSSI signal, distance (meters), battery level, and safe zone perimeter (10m).
- **1-Tap Emergency SOS**: Instant emergency alert broadcasting live GPS coordinates, beacon state, and caregiver details with audit logging.
- **AI Safety Assistant**: Role-specific assistance powered by local Ollama (`qwen3:4b`) with automatic, graceful offline fallback mode.
- **Real-Time Routine & Session Logging**: Digital check-in/out timers and structured care logs (Meals, Medication, Activities, Naps, Hygiene).
- **Comprehensive Admin Monitoring**: Verification approvals/rejections, live safety incident resolution, fleet telemetry, and audit trail.

---

## 3. Technology Stack & Architecture

```
                               ┌─────────────────────────┐
                               │     Client Browsers     │
                               └────────────┬────────────┘
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Web Application (Python 3.14)                         │
├──────────────────────────┬────────────────────────────┬───────────────────────────────┤
│    Parent Portal UI      │    Guardian Portal UI      │    Admin Control Center UI    │
│   (/portals/user/)       │   (/portals/guardian/)     │     (/portals/admin/)         │
└────────────┬─────────────┴─────────────┬──────────────┴──────────────┬────────────────┘
             │                           │                             │
             ▼                           ▼                             ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                   REST API Layer                                      │
├───────────────┬───────────────┬────────────────┬─────────────────┬────────────────────┤
│  /bookings    │    /safety    │    /beacon     │       /ai       │       /admin       │
└───────┬───────┴───────┬───────┴───────┬────────┴────────┬────────┴─────────┬──────────┘
        │               │               │                 │                  │
        ▼               ▼               ▼                 ▼                  ▼
┌───────────────────────────────────────────────┐ ┌─────────────────────────────────────┐
│             SQLite 3 Database                 │ │          Local Ollama AI            │
│   (users, guardians, bookings, routines,      │ │       (Model: qwen3:4b)             │
│    beacons, safety_events, audit_logs)        │ │  (Endpoint: http://127.0.0.1:11434) │
└───────────────────────────────────────────────┘ └─────────────────────────────────────┘
```

- **Backend**: FastAPI, Uvicorn, Pydantic, SQLite (Standard library `sqlite3`), `httpx`
- **Frontend**: Vanilla HTML5, CSS3 (Modern custom design system), JavaScript ES6+
- **AI Service**: Ollama (`qwen3:4b`) at `http://127.0.0.1:11434/api/generate` + Guardian Go Offline Safety Engine fallback

---

## 4. Installation

```bash
# Clone or navigate to the project directory
cd "c:\Users\premk\OneDrive\Desktop\Guardian goo"

# Install required Python packages
pip install -r requirements.txt
```

---

## 5. How to Start Backend

Start the FastAPI application server using `run.py`:

```bash
python run.py
```

The application will start locally on **`http://127.0.0.1:8000`**. Database tables and realistic seed data are automatically initialized on startup.

---

## 6. How to Start Ollama (AI Model)

To enable live local LLM inference using Qwen 3 4B:

```bash
# Pull and start qwen3:4b model on Ollama
ollama run qwen3:4b
```

> **Note**: If Ollama is not installed or turned off, **Guardian Go will NOT crash**. The built-in **Offline Safety Engine** seamlessly responds with domain-tailored child safety advice!

---

## 7. Demo Accounts & Portals

| Role | Demo Email | Portal URL |
| :--- | :--- | :--- |
| **Landing & Role Selector** | N/A | `http://127.0.0.1:8000/` |
| **Parent / User Portal** | `parent@demo.com` | `http://127.0.0.1:8000/portals/user/` |
| **Guardian Portal** | `guardian@demo.com` | `http://127.0.0.1:8000/portals/guardian/` |
| **Admin Control Center** | `admin@demo.com` | `http://127.0.0.1:8000/portals/admin/` |

---

## 8. API Endpoints Reference

### Health & Auth
- `GET /api/health` - System health check
- `GET /api/v1/auth/me` - Get active demo user profile

### Parent & Caregiver Discovery
- `GET /api/v1/guardians` - List all verified guardians
- `GET /api/v1/bookings` - List care bookings
- `POST /api/v1/bookings` - Create a new care booking request
- `POST /api/v1/bookings/{id}/accept` - Guardian accepts booking
- `POST /api/v1/bookings/{id}/decline` - Guardian declines booking

### Care Sessions & Routines
- `POST /api/v1/care-sessions/check-in` - Caregiver check-in timestamp
- `POST /api/v1/care-sessions/check-out` - Caregiver check-out timestamp
- `POST /api/v1/care/routine` - Log routine activity (meal, medication, nap, hygiene)
- `GET /api/v1/care/routine` - List routine log history

### Safety & BLE Beacon
- `POST /api/v1/safety/sos` - Trigger Emergency SOS
- `GET /api/v1/safety/events` - Fetch live safety incidents
- `POST /api/v1/safety/events/{id}/resolve` - Admin resolve safety incident
- `GET /api/v1/beacon/status` - Fetch live child BLE beacon telemetry
- `POST /api/v1/beacon/simulate` - Simulate BLE beacon actions (`breach`, `reset`, `connect`, `warning`)

### AI Assistant
- `POST /api/v1/ai/assistant/user` - Parent AI safety queries
- `POST /api/v1/ai/assistant/guardian` - Guardian AI protocol queries

### Admin Operations
- `POST /api/v1/admin/guardians/{id}/approve` - Approve caregiver verification
- `POST /api/v1/admin/guardians/{id}/reject` - Reject caregiver verification
- `GET /api/v1/admin/analytics` - System dashboard metrics
- `GET /api/v1/admin/audit` - Platform immutable audit logs

---

## 9. Hackathon Demo Flow (Recommended Presentation Sequence)

1. **Landing Page (`http://127.0.0.1:8000/`)**:
   - Introduce Guardian Go tagline & core tech pillars.
2. **Parent Portal (`http://127.0.0.1:8000/portals/user/`)**:
   - View caregiver cards in Discovery feed.
   - Click **Book Guardian** to submit a booking request.
   - Test **BLE Beacon Simulation**: Click *"Simulate Safe Zone Breach"* -> Observe prominent warning banner & toast!
   - Test **SOS Emergency Button**: Click *"SOS Emergency"* -> Confirm -> Observe emergency broadcast.
   - Ask AI Assistant: Click query chips or type *"What should I do during an emergency?"*.
3. **Guardian Portal (`http://127.0.0.1:8000/portals/guardian/`)**:
   - View trust score (96/100) and 4 verification badges.
   - Click **Accept** on the pending booking request.
   - Click **Check In** to start active care session timer.
   - Submit a routine log under Meal/Activity -> Observe instant entry in feed.
4. **Admin Control Center (`http://127.0.0.1:8000/portals/admin/`)**:
   - Inspect live metrics cards & analytics graphs.
   - Review pending guardian applications -> Click **Approve** or **Reject**.
   - Review Safety Monitoring table -> Resolve the active SOS event.
   - Inspect immutable **Audit Trail**.

---

## 10. BLE Beacon Simulation & AI Fallback Explanation

### BLE Beacon Simulation
Physical BLE hardware is simulated via backend signal processing (`beacon_service.py`). The beacon updates RSSI, battery levels, and distance. When distance exceeds 10.0m or "Breach" is clicked, a `BEACON_BREACH` safety event and audit record are generated automatically.

### AI Graceful Fallback Engine
When calling `/api/v1/ai/assistant/*`, the backend sends a request to Ollama (`qwen3:4b`) with a 3.0s timeout. If Ollama is unavailable or slow, the server switches to the **Guardian Go Offline Safety Engine**, returning precise domain-tailored advice without raising 500 errors or throwing tracebacks.

---

## 11. Automated Testing

Run the full pytest suite:

```bash
python -m pytest
```

Expected output: **13 passed**.
