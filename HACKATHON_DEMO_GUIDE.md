# 🛡️ Guardian Go — Hackathon Demo Guide & System Architecture
> **"Verified care. Connected safety. Peace of mind."**

Welcome to **Guardian Go**, an AI-powered, hardware-integrated safe caregiver and family care platform built for modern child and elderly protection.

---

## 🚀 Quick Start Guide

### 1. Requirements & Dependencies
- **Python**: 3.10+ (Verified on Python 3.14)
- **FastAPI & Uvicorn**: Web framework and ASGI server
- **Database**: SQLite (`guardian_go.db` — auto-initialized and seeded on startup)
- **AI Engine**: Local Ollama running `qwen3:4b` at `http://127.0.0.1:11434` (with offline fallback engine)

### 2. Run the Platform Server
Execute the server from the project root directory:
```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
or
```bash
python -m backend.main
```

### 3. Run the Full Test Suite
```bash
python -m pytest
```
*Result: **92/92 PASSED (100%)***

---

## 🔑 Demo Login Credentials & Portal Links

| Portal | URL | Demo Email | Password | Role Features |
| :--- | :--- | :--- | :--- | :--- |
| **Landing Page** | `http://127.0.0.1:8000/` | - | - | Interactive role selection & platform hero |
| **Parent Portal** | `http://127.0.0.1:8000/portals/user` | `parent@demo.com` | `password123` | Caregiver search, AI recommendations, Safety Centre, Daily reports, Family Circle, 1-Tap SOS |
| **Guardian Portal** | `http://127.0.0.1:8000/portals/guardian` | `guardian@demo.com` | `password123` | Booking requests, Check-in/out, Biometrics, Care routine logging, Digital Passport |
| **Admin Command Centre** | `http://127.0.0.1:8000/portals/admin` | `admin@demo.com` | `password123` | System metrics, Local Qwen AI summary, Risk alerts, Unresolved complaints, Emergency dispatch |

---

## 🏆 Key Features Implemented Across 18 Phases

### 1. 🛡️ 4-Gate Verification & Digital Guardian Passport
- **Gate 1**: Government Identity Verification (Aadhaar / Passport).
- **Gate 2**: Police Clearance & Criminal Record Audit.
- **Gate 3**: First Aid & CPR Certification Validation.
- **Gate 4**: Facial Recognition & Anti-Spoof Liveness Check.
- **Digital Passport**: Shareable, tamper-evident caregiver verification passport (`GET /api/v1/verification/passport/{id}`).

### 2. 🏛️ DigiLocker OAuth Integration
- Seamless OAuth consent workflow (`/api/v1/digilocker/*`).
- Automatic document verification for Aadhaar (masked `XXXX-XXXX-8842`), Class XII marksheet, and certifications.
- Admin verification overrides.

### 3. 💳 3-Tier Membership Engine
- Tiers: `BASIC_CARE`, `SAFECARE`, `PREMIUM_CARE_PLUS`.
- Automated backend security entitlement engine (`check_entitlement`).
- Simulated payment processing (`SIMULATED_SUCCESS`).

### 4. 📅 Smart Booking & Schedule Conflict Engine
- Prevents double-booking overlaps (`409 Conflict`).
- Lifecycle state machine: `REQUESTED` ➔ `ACCEPTED` ➔ `CONFIRMED` ➔ `CHECKED_IN` ➔ `COMPLETED` / `CANCELLED`.

### 5. 🤖 Local Qwen AI Integration (`qwen3:4b`)
- 100% local, privacy-first AI model integration running on Ollama (`http://127.0.0.1:11434`).
- Capabilities:
  - **Matchmaking**: AI Guardian recommendation with explainable reasons.
  - **Role Assistants**: Interactive parent, guardian, and admin AI assistants.
  - **Executive Summaries**: Admin operational status summaries.
  - **Pediatric Care Summaries**: Daily care report insight generator.
  - **NLP Complaint Analysis**: Sentiment, risk level, and XAI factor breakdown.

### 6. 🔒 Hardware Safety & Indoor BLE Presence
- **Biometric Hardware Abstraction**: Fingerprint scanner enrollment & verification (`VERIFIED`, `DEMO_VERIFIED`).
- **Indoor BLE Presence Monitoring & Anomaly Detection**: Proximity distance, safe zone tracking, RSSI signal, and battery level.
- **Parent Safety Centre Dashboard**: Real-time unified safety status aggregator (`GET /api/v1/safety/centre/{parent_id}`).

### 7. 🚨 1-Tap Emergency SOS System
- Dispatches emergency case reference (`INC-SOS-XXXXXX`).
- Streams live GPS coordinates and BLE beacon proximity.
- Multi-channel broadcast push/SMS alerts to Family Circle and Admin Command Center.
- Emergency escalation protocol: `ACTIVE` ➔ `DISPATCHED` ➔ `RESPONDER_ON_SCENE` ➔ `RESOLVED`.

### 8. 👨‍👩‍👧 Family Circle & Care Routines
- Primary Parents invite extended family members (Grandparents, Co-Parents, Emergency Contacts).
- Granular permissions: `FULL_ACCESS`, `CARE_VIEWER`, `EMERGENCY_ONLY`.
- Log structured care routines across 6 categories (Meals, Medication, Play, Naps, Hygiene, Notes).

### 9. ⚖️ Complaint NLP + XAI & Safety Governance
- Real-time NLP sentiment analysis & risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Core Governance Rule**: *"AI flags risk only; Admin decides"*.
- Auto-escalation of high-risk complaints into Admin Risk Alerts.
- Admin actions: `DISMISS`, `WARN_GUARDIAN`, `INVESTIGATE`, `SUSPEND_GUARDIAN`.

### 10. 🛡️ Security Hardening
- **Security Headers Middleware**: `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1`, `Content-Security-Policy`, `Strict-Transport-Security`.
- **Sliding-Window Rate Limiter**: In-memory rate limiting on auth and emergency endpoints.
- **Sensitive PII Masking**: Masked Aadhaar (`XXXX-XXXX-8842`), phone numbers, and salted PBKDF2 SHA-256 password hashing.
- **Injection Defense**: 100% parameterized SQLite database queries.

---

## 🎨 Design System & Theme
- **Theme**: Soft Light Green Premium Palette
- **Primary Green**: `#A8D5BA` (Soft Sage) / `#2e7d56` (Deep Accent)
- **Secondary**: `#DCEFE2` (Pale Mint)
- **Background**: `#F5FAF6` (Warm Off-White)
- **Text Dark**: `#1F2933` (Charcoal)
- **Muted Text**: `#667085` (Slate)
- **Emergency / SOS**: `#D9534F` (Soft Coral Red)
- **Glassmorphism**: Backdrop blur filters (`backdrop-filter: blur(12px)`) and micro-animations.

---

## 🧪 Comprehensive Test Suite Summary

| Test File | Modules Tested | Result |
| :--- | :--- | :--- |
| `test_auth_phase1.py` | PBKDF2 Auth, Registration, Login entry points, RBAC | **9/9 PASSED** |
| `test_verification_phase2.py` | 4-Gate Verification, Digital Passport | **8/8 PASSED** |
| `test_digilocker_phase3.py` | DigiLocker OAuth, Aadhaar Masking, Admin Override | **5/5 PASSED** |
| `test_membership_phase4.py` | 3 Membership Tiers, Entitlements, Payments | **7/7 PASSED** |
| `test_bookings_phase5.py` | Booking Lifecycle, Availability, Overlap Conflict Engine | **8/8 PASSED** |
| `test_ai_phase6.py` | Ollama Local Qwen AI Health, Recommendations, Role Assistants | **5/5 PASSED** |
| `test_trust_risk_phase7.py` | Trust Score Engine, Risk Alert Resolution | **4/4 PASSED** |
| `test_safety_phase8.py` | Safety Centre, Fingerprint, Face Liveness, BLE Signal | **6/6 PASSED** |
| `test_reports_phase9.py` | Daily Care Reports, Parent Timeline, AI Insights | **5/5 PASSED** |
| `test_notifications_phase10.py` | Multi-Channel Notifications, Unread Counter, Read-All | **4/4 PASSED** |
| `test_family_phase11.py` | Family Circle Invite, Permissions, Care Routines | **4/4 PASSED** |
| `test_emergency_phase12.py` | 1-Tap SOS, Case File Reference, Dispatch State Machine | **4/4 PASSED** |
| `test_complaints_phase13.py` | Complaint NLP, XAI Risk Factors, Admin Resolution | **4/4 PASSED** |
| `test_admin_phase14.py` | Admin Command Centre Payload, AI Summary, Override | **4/4 PASSED** |
| `test_security_phase15.py` | Security Headers, Rate Limiting, PII Data Masking | **4/4 PASSED** |
| `test_ui_phase16.py` | Portal HTML Serving, Static Assets, Design System | **4/4 PASSED** |
| `test_integration_phase17.py` | Full Platform End-to-End Journey | **1/1 PASSED** |
| **TOTAL** | **All 17 Test Files** | **92/92 PASSED (100%)** |

---

*Guardian Go — Hackathon Prototype Ready for Demonstration.*
