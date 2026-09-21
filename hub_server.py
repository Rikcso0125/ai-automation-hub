# -*- coding: utf-8 -*-
"""
AI Automation Hub - FastAPI Server
Központi munkafolyamat-motor, többügyfeles autentikáció, integrációs vault és szuper admin felület.
"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from core.module_registry import scan_modules, get_module_by_id
from core.execution_logger import (
    save_module_config, get_recent_logs, get_stats, get_module_config,
    create_user, authenticate_user, create_session, get_user_by_session, delete_session,
    list_all_clients, get_client_by_id,
    save_user_integration, get_user_integrations, delete_user_integration,
    save_tenant_module_config, get_tenant_module_config
)
from core.webhook_dispatcher import dispatch_event

app = FastAPI(
    title="AI Automation Hub",
    description="Vállalati AI automatizációs és munkafolyamat motor",
    version="2.0.0"
)

# Statikus fájlok kiszolgálása a web mappából
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web")), name="static")

# --- Auth Helper Dependencies ---
def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in request.query_params:
        token = request.query_params["token"]
    if not token:
        return None
    return get_user_by_session(token)

def require_auth(request: Request) -> Dict[str, Any]:
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Bejelentkezés szükséges a művelethez!")
    return user

def require_superadmin(request: Request) -> Dict[str, Any]:
    user = require_auth(request)
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Ehhez a művelethez Szuper Adminisztrátori jogosultság szükséges!")
    return user

# --- Models ---
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: str
    phone: Optional[str] = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class IntegrationSaveRequest(BaseModel):
    service_type: str
    service_name: str
    credentials: Dict[str, Any]
    notes: Optional[str] = ""

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]
    is_active: bool = True

# --- Public & Dashboard Routes ---
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = BASE_DIR / "web" / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web dashboard nem található!")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/v1/modules")
async def list_modules(request: Request, client_id: Optional[int] = None):
    uid = None
    user = get_current_user_from_request(request)
    if client_id and user and user.get("role") == "superadmin":
        uid = client_id
    elif user and user.get("role") == "client":
        uid = user["id"]
    return scan_modules(user_id=uid)

@app.get("/api/v1/modules/{module_id}")
async def get_module(module_id: str, request: Request, client_id: Optional[int] = None):
    uid = None
    user = get_current_user_from_request(request)
    if client_id and user and user.get("role") == "superadmin":
        uid = client_id
    elif user and user.get("role") == "client":
        uid = user["id"]
    m = get_module_by_id(module_id, user_id=uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    return m

@app.post("/api/v1/modules/{module_id}/config")
async def update_module_config(module_id: str, req: ConfigUpdateRequest, request: Request, client_id: Optional[int] = None):
    user = get_current_user_from_request(request)
    if client_id and user and user.get("role") == "superadmin":
        save_tenant_module_config(client_id, module_id, req.config, req.is_active)
        return {"status": "success", "module_id": module_id, "message": f"Beállítások mentve a(z) #{client_id} ügyfélhez."}
    elif user and user.get("role") == "client":
        save_tenant_module_config(user["id"], module_id, req.config, req.is_active)
        return {"status": "success", "module_id": module_id, "message": "Saját fiókod beállításai elmentve."}
    else:
        # Default global config
        m = get_module_by_id(module_id)
        if not m:
            raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
        save_module_config(module_id, req.config, req.is_active)
        return {"status": "success", "module_id": module_id, "message": "Globális beállítások sikeresen mentve."}

@app.post("/api/v1/modules/{module_id}/toggle")
async def toggle_module(module_id: str, request: Request, client_id: Optional[int] = None):
    user = get_current_user_from_request(request)
    uid = None
    if client_id and user and user.get("role") == "superadmin":
        uid = client_id
    elif user and user.get("role") == "client":
        uid = user["id"]

    m = get_module_by_id(module_id, user_id=uid)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")

    cfg = m.get("config", {})
    current_active = cfg.get("_is_active", True)
    new_active = not current_active

    if uid:
        save_tenant_module_config(uid, module_id, cfg, new_active)
    else:
        saved_cfg = m.get("saved_config", {})
        save_module_config(module_id, saved_cfg, new_active)

    return {
        "status": "success",
        "module_id": module_id,
        "is_active": new_active,
        "message": f"Modul sikeresen {'bekapcsolva' if new_active else 'kikapcsolva'}."
    }

@app.post("/api/v1/modules/{module_id}/test")
async def test_module(module_id: str, request: Request, client_id: Optional[int] = None):
    try:
        body = await request.json()
    except Exception:
        body = {}

    user = get_current_user_from_request(request)
    uid = None
    if client_id and user and user.get("role") == "superadmin":
        uid = client_id
    elif user and user.get("role") == "client":
        uid = user["id"]

    if not body:
        m = get_module_by_id(module_id, user_id=uid)
        if m and m.get("test_payload"):
            body = m["test_payload"]

    res = await dispatch_event(module_id, body, tenant_user_id=uid)
    return res

@app.post("/api/v1/webhook/{module_id}")
async def receive_webhook(module_id: str, request: Request, tenant_id: Optional[int] = None):
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw_body": (await request.body()).decode("utf-8", errors="ignore")}

    tid = tenant_id
    if not tid:
        h_tid = request.headers.get("X-Tenant-ID")
        if h_tid:
            try:
                tid = int(h_tid)
            except Exception:
                tid = None

    res = await dispatch_event(module_id, payload, tenant_user_id=tid)
    return res

@app.get("/api/v1/logs")
async def get_logs(limit: int = 50, module_id: Optional[str] = None):
    return get_recent_logs(limit=limit, module_id=module_id)

@app.get("/api/v1/stats")
async def get_dashboard_stats():
    return get_stats()

# --- Auth Endpoints ---
@app.post("/api/v1/auth/register")
async def register(req: RegisterRequest):
    try:
        user = create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            company_name=req.company_name,
            phone=req.phone or "",
            role="client"
        )
        token = create_session(user["id"])
        return {
            "status": "success",
            "token": token,
            "user": user,
            "message": f"Sikeres regisztráció! Üdvözlünk, {user['full_name']}."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Szerverhiba a regisztráció során: {str(e)}")

@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Hibás email cím vagy jelszó!")
    token = create_session(user["id"])
    return {
        "status": "success",
        "token": token,
        "user": user,
        "message": f"Sikeres bejelentkezés! Üdv újra, {user['full_name']}."
    }

@app.post("/api/v1/auth/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        delete_session(auth_header[7:].strip())
    elif "token" in request.query_params:
        delete_session(request.query_params["token"])
    return {"status": "success", "message": "Sikeresen kijelentkeztél."}

@app.get("/api/v1/auth/me")
async def get_me(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}

# --- Integrations Vault Endpoints (Client Third-party Permissions) ---
@app.get("/api/v1/integrations")
async def list_integrations(request: Request):
    user = require_auth(request)
    integrations = get_user_integrations(user["id"], hide_secrets=True)
    return {"status": "success", "integrations": integrations}

@app.post("/api/v1/integrations")
async def save_integration(req: IntegrationSaveRequest, request: Request):
    user = require_auth(request)
    integration_id = save_user_integration(
        user_id=user["id"],
        service_type=req.service_type,
        service_name=req.service_name,
        credentials=req.credentials,
        status="connected",
        notes=req.notes or ""
    )
    return {
        "status": "success",
        "integration_id": integration_id,
        "message": f"'{req.service_name}' kapcsolat adatai sikeresen és biztonságosan elmentve!"
    }

@app.delete("/api/v1/integrations/{integration_id}")
async def remove_integration(integration_id: int, request: Request):
    user = require_auth(request)
    delete_user_integration(user["id"], integration_id)
    return {"status": "success", "message": "Integráció sikeresen eltávolítva."}

# --- Super Admin Management Endpoints ---
@app.get("/api/v1/admin/clients")
async def admin_list_clients(request: Request):
    require_superadmin(request)
    clients = list_all_clients()
    return {"status": "success", "clients": clients}

@app.get("/api/v1/admin/clients/{client_id}")
async def admin_get_client(client_id: int, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    # Szuper adminisztrátorként látjuk a bekötött adatokat a konfiguráció elkészítéséhez
    integrations = get_user_integrations(client_id, hide_secrets=False)
    return {
        "status": "success",
        "client": client,
        "integrations": integrations
    }

@app.get("/api/v1/admin/clients/{client_id}/modules")
async def admin_list_client_modules(client_id: int, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    return scan_modules(user_id=client_id)

@app.get("/api/v1/admin/clients/{client_id}/modules/{module_id}")
async def admin_get_client_module(client_id: int, module_id: str, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    m = get_module_by_id(module_id, user_id=client_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    return m

@app.post("/api/v1/admin/clients/{client_id}/modules/{module_id}/config")
async def admin_update_client_module_config(client_id: int, module_id: str, req: ConfigUpdateRequest, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    save_tenant_module_config(client_id, module_id, req.config, req.is_active)
    return {"status": "success", "module_id": module_id, "client_id": client_id, "message": f"Beállítások mentve a(z) #{client_id} ügyfélhez ({client['company_name']})."}

@app.post("/api/v1/admin/clients/{client_id}/modules/{module_id}/toggle")
async def admin_toggle_client_module(client_id: int, module_id: str, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    m = get_module_by_id(module_id, user_id=client_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    cfg = m.get("config", {})
    current_active = cfg.get("_is_active", True)
    new_active = not current_active
    save_tenant_module_config(client_id, module_id, cfg, new_active)
    return {
        "status": "success",
        "module_id": module_id,
        "client_id": client_id,
        "is_active": new_active,
        "message": f"Modul a(z) #{client_id} ügyfél számára {'bekapcsolva' if new_active else 'kikapcsolva'}."
    }

@app.post("/api/v1/admin/clients/{client_id}/modules/{module_id}/test")
async def admin_test_client_module(client_id: int, module_id: str, request: Request):
    require_superadmin(request)
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="A megadott ügyfél nem található!")
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not body:
        m = get_module_by_id(module_id, user_id=client_id)
        if m and m.get("test_payload"):
            body = m["test_payload"]
    res = await dispatch_event(module_id, body, tenant_user_id=client_id)
    return res

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(">>> AI AUTOMATION HUB INDUL...")
    print(">>> Nyissa meg a bongeszoben: http://localhost:8000")
    print(">>> Swagger API Dokumentacio: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)