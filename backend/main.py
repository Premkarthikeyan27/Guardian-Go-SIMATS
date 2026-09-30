import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.database import init_db, seed_db
from backend.routers import auth, parent, guardian, admin, bookings, safety, ai, beacon, verification, digilocker, membership, risk, reports, notifications, family, complaints, security
from backend.services.security_service import rate_limiter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize and seed database on startup
    init_db()
    seed_db()
    yield

app = FastAPI(
    title="Guardian Go API",
    description="AI-Powered Safe Caregiver & Family Care Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Security Headers & Rate Limiting Middleware
@app.middleware("http")
async def add_security_headers_and_rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    if request.url.path.startswith("/api/v1/auth/login") or request.url.path.startswith("/api/v1/safety/sos"):
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please wait before retrying."})

    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; img-src 'self' data: https:;"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include API Routers
app.include_router(auth.router)
app.include_router(parent.router)
app.include_router(guardian.router)
app.include_router(admin.router)
app.include_router(bookings.router)
app.include_router(safety.router)
app.include_router(ai.router)
app.include_router(beacon.router)
app.include_router(verification.router)
app.include_router(digilocker.router)
app.include_router(membership.router)
app.include_router(risk.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(family.router)
app.include_router(complaints.router)
app.include_router(security.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "Guardian Go",
        "tagline": "Verified care. Connected safety. Peace of mind.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Serving Portals & Frontend Pages
@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Guardian Go Landing Page"}

# Dedicated Authentication Entry Points
@app.get("/login")
def serve_parent_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "parent", "login.html"))

@app.get("/guardian/login")
def serve_guardian_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "guardian", "login.html"))

@app.get("/admin/login")
def serve_admin_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "login.html"))

@app.get("/portals/user")
@app.get("/portals/user/")
def serve_user_portal():
    file_path = os.path.join(FRONTEND_DIR, "parent", "index.html")
    return FileResponse(file_path)

@app.get("/portals/guardian")
@app.get("/portals/guardian/")
def serve_guardian_portal():
    file_path = os.path.join(FRONTEND_DIR, "guardian", "index.html")
    return FileResponse(file_path)

@app.get("/portals/admin")
@app.get("/portals/admin/")
def serve_admin_portal():
    file_path = os.path.join(FRONTEND_DIR, "admin", "index.html")
    return FileResponse(file_path)

# Mount Static Files for assets (parent, guardian, admin, root)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    app.mount("/parent", StaticFiles(directory=os.path.join(FRONTEND_DIR, "parent")), name="parent_static")
    app.mount("/guardian", StaticFiles(directory=os.path.join(FRONTEND_DIR, "guardian")), name="guardian_static")
    app.mount("/admin", StaticFiles(directory=os.path.join(FRONTEND_DIR, "admin")), name="admin_static")
