"""
backend/server.py — FastAPI WebSocket Server

Architecture :
- Routes HTTP pour l'authentification (JWT)
- Routes WebSocket pour la communication temps réel
- Gestion des sessions (1 opérateur = 1 véhicule)
- Relais de commandes (operator → backend → vehicle)
- Collecte de télémétrie (vehicle → backend)

Concepts clés :
- @app.post() / @app.websocket() → décorateurs FastAPI
- asyncio → pour l'asynchrone (important pour WebSocket)
- WebSocketDisconnect → exception quand un client se déconnecte
- Depends → injection de dépendances (auth, session manager)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from contextlib import asynccontextmanager
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import logging
import os
from pydantic import BaseModel, ValidationError
import json


# ========================================================================
# CONFIGURATION
# ========================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter — identifie chaque client par son IP
limiter = Limiter(key_func=get_remote_address)

# Prometheus counters / gauges
_auth_counter  = Counter("teleop_auth_attempts_total", "Tentatives d'authentification", ["result"])
_ws_gauge      = Gauge("teleop_ws_connections_active", "Connexions WebSocket actives", ["type"])
_cmd_counter   = Counter("teleop_commands_relayed_total", "Commandes relayées au véhicule")
_telem_counter = Counter("teleop_telemetry_messages_total", "Messages de télémétrie reçus")
_sec_counter   = Counter("teleop_security_events_total", "Événements de sécurité", ["level"])

# Counters locaux pour /metrics/json (pas besoin de parser le format Prometheus)
_m = {
    "auth_success": 0, "auth_failure": 0, "auth_rate_limited": 0,
    "commands_relayed": 0, "telemetry_received": 0,
    "sec_danger": 0, "sec_warning": 0, "sec_success": 0, "sec_info": 0,
}

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "15"))

# Credentials hardcodés pour la démo (en prod : base de données)
OPERATORS_DB = {
    "operator_001": "secret123",
    "dashboard_operator": "dashboard123",
}

# ========================================================================
# FONCTIONS JWT
# ========================================================================

def create_access_token(operator_id: str) -> str:
    """Créer un token JWT signé avec expiration."""
    payload = {
        "sub": operator_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> str:
    """Vérifier un token JWT et retourner l'operator_id. Lève JWTError si invalide."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    operator_id = payload.get("sub")
    if not operator_id:
        raise JWTError("Token sans subject")
    return operator_id

# ========================================================================
# STRUCTURES DE DONNÉES (placeholder)
# ========================================================================
# En semaine 2, remplacer par les vrais modèles Pydantic
# Pydantic = validation + serialization de données en Python

class LoginRequest(BaseModel):
    operator_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GPSCoordinates(BaseModel):
    lat: float
    lon: float


class TelemetryMessage(BaseModel):
    type: str
    vehicle_id: str
    timestamp: str
    speed: float
    steering_angle: float
    brake_pressure: float
    throttle: float
    gps: GPSCoordinates
    battery: float
    status: str


class CommandMessage(BaseModel):
    type: str
    operator_id: str
    timestamp: str
    throttle: float = 0.0
    steering: float = 0.0
    brake: float = 0.0

class ConnectionManager:
    def __init__(self):
        self.vehicles: dict[str, WebSocket] = {}
        self.operators: dict[str, WebSocket] = {}
        self.observers: list[WebSocket] = []        # dashboards connectés

    async def connect_vehicle(self, vehicle_id: str, ws: WebSocket):
        self.vehicles[vehicle_id] = ws
        _ws_gauge.labels(type="vehicle").set(len(self.vehicles))

    async def connect_operator(self, operator_id: str, ws: WebSocket):
        self.operators[operator_id] = ws
        _ws_gauge.labels(type="operator").set(len(self.operators))

    async def connect_observer(self, ws: WebSocket):
        self.observers.append(ws)

    def disconnect_vehicle(self, vehicle_id: str):
        self.vehicles.pop(vehicle_id, None)
        _ws_gauge.labels(type="vehicle").set(len(self.vehicles))

    def disconnect_operator(self, operator_id: str):
        self.operators.pop(operator_id, None)
        _ws_gauge.labels(type="operator").set(len(self.operators))

    def disconnect_observer(self, ws: WebSocket):
        if ws in self.observers:
            self.observers.remove(ws)

    async def relay_to_operators(self, data: str):
        for op_ws in self.operators.values():
            await op_ws.send_text(data)
        # Le dashboard reçoit aussi la télémétrie
        await self._broadcast_to_observers(data)

    async def relay_to_vehicle(self, vehicle_id: str, data: str):
        ws = self.vehicles.get(vehicle_id)
        if ws:
            await ws.send_text(data)
            _cmd_counter.inc()
            _m["commands_relayed"] += 1
        # Le dashboard voit aussi les commandes envoyées
        await self._broadcast_to_observers(data)

    async def _broadcast_to_observers(self, data: str):
        for ws in list(self.observers):
            try:
                await ws.send_text(data)
            except Exception:
                self.observers.remove(ws)

    async def security_event(self, level: str, message: str):
        """Envoyer un événement de sécurité au dashboard."""
        _sec_counter.labels(level=level).inc()
        key = f"sec_{level}"
        if key in _m:
            _m[key] += 1
        event = json.dumps({"type": "security_event", "level": level, "message": message})
        await self._broadcast_to_observers(event)

manager = ConnectionManager()

# ========================================================================
# LIFESPAN (startup/shutdown)
# ========================================================================
# Cette fonction s'exécute au démarrage et à l'arrêt de FastAPI
# Utile pour initialiser les ressources (DB, connexions, etc.)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.

    Syntaxe :
    - yield → code avant le yield = startup
    - code après yield = shutdown
    """
    logger.info("🚀 Backend démarrage...")
    # TODO : initialiser les ressources (DB, monitoring, etc.)
    yield
    logger.info("🛑 Backend arrêt...")
    # TODO : nettoyer les ressources

# ========================================================================
# APPLICATION FASTAPI
# ========================================================================

app = FastAPI(
    title="Teleop Backend",
    description="Backend pour la téléopération sécurisée de robotaxis",
    version="0.1.0",
    lifespan=lifespan
)

# Attacher le limiter à l'app (slowapi le lit depuis app.state)
app.state.limiter = limiter

# Handler personnalisé : 429 + log dans le dashboard de sécurité
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host if request.client else "IP inconnue"
    logger.warning(f"[RATE-LIMIT] Trop de tentatives depuis {client_ip} sur {request.url.path}")
    _auth_counter.labels(result="rate_limited").inc()
    _m["auth_rate_limited"] += 1
    asyncio.create_task(
        manager.security_event("danger", f"🛡️ Brute force bloqué : {client_ip} ({exc.detail})")
    )
    return JSONResponse(
        status_code=429,
        content={"detail": f"Trop de tentatives. Réessayez dans une minute."}
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS middleware — autoriser les requêtes cross-origin
# (important pour WebSocket depuis un navigateur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO : restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# ROUTES HTTP — Authentification
# ========================================================================

@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    """
    Login — émettre un JWT pour un opérateur.

    POST /auth/login
    Body : {"operator_id": "operator_001", "password": "secret123"}
    Retourne : {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 900}

    Rate limit : 5 tentatives par minute par IP. Au-delà → 429 Too Many Requests.
    """
    logger.info(f"[AUTH] Tentative login pour {body.operator_id}")

    expected_password = OPERATORS_DB.get(body.operator_id)
    if not expected_password or expected_password != body.password:
        logger.warning(f"[AUTH] Échec login pour {body.operator_id}")
        _auth_counter.labels(result="failure").inc()
        _m["auth_failure"] += 1
        await manager.security_event("danger", f"❌ Échec login : {body.operator_id} (mauvais credentials)")
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token(body.operator_id)
    logger.info(f"[AUTH] Token émis pour {body.operator_id}")
    _auth_counter.labels(result="success").inc()
    _m["auth_success"] += 1
    await manager.security_event("success", f"✅ Token JWT émis pour {body.operator_id}")
    return TokenResponse(access_token=token, expires_in=JWT_EXPIRY_MINUTES * 60)

@app.post("/auth/refresh")
async def refresh_token():
    """Renouveler le JWT avant expiration."""
    logger.info(f"[AUTH] Refresh token...")
    # TODO : valider le token existant et en émettre un nouveau
    raise HTTPException(status_code=501, detail="Not implemented")

# ========================================================================
# ROUTES HTTP — Health + Metrics
# ========================================================================

@app.get("/health")
async def health():
    """Health check — utilisé par Docker et Prometheus."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Métriques Prometheus — format text/plain pour scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics/json")
async def metrics_json():
    """Métriques en JSON pour le dashboard HTML."""
    return {**_m, "ws_vehicles": len(manager.vehicles), "ws_operators": len(manager.operators)}

# ========================================================================
# ROUTES WEBSOCKET — Communication temps réel
# ========================================================================

@app.websocket("/ws/vehicle/{vehicle_id}")
async def websocket_vehicle(websocket: WebSocket, vehicle_id: str):
    await websocket.accept()
    await manager.connect_vehicle(vehicle_id, websocket)
    logger.info(f"[WS-VEHICLE] {vehicle_id} connecté ✓")
    await manager.security_event("info", f"🚗 Véhicule {vehicle_id} connecté")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                telemetry = TelemetryMessage(**json.loads(data))
                _telem_counter.inc()
                _m["telemetry_received"] += 1
                logger.info(f"[WS-VEHICLE] télémétrie {vehicle_id}: speed={telemetry.speed} status={telemetry.status}")
                await manager.relay_to_operators(data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"[WS-VEHICLE] Message invalide ignoré: {e}")
    except WebSocketDisconnect:
        logger.warning(f"[WS-VEHICLE] {vehicle_id} déconnecté")
        manager.disconnect_vehicle(vehicle_id)
    except Exception as e:
        logger.error(f"[WS-VEHICLE] Erreur: {e}")
        manager.disconnect_vehicle(vehicle_id)
        await websocket.close(code=1011)


@app.websocket("/ws/operator/{operator_id}")
async def websocket_operator(websocket: WebSocket, operator_id: str, token: str = Query(None)):
    if not token:
        await websocket.accept()
        await websocket.close(code=1008)
        logger.warning(f"[AUTH] Connexion sans token refusée pour {operator_id}")
        await manager.security_event("danger", f"🚫 Connexion refusée : aucun token fourni pour {operator_id}")
        return

    try:
        verified_id = verify_token(token)
    except JWTError:
        await websocket.accept()
        await websocket.close(code=1008)
        logger.warning(f"[AUTH] Connexion WebSocket refusée pour {operator_id} : token invalide")
        await manager.security_event("danger", f"🚫 Connexion refusée : token invalide pour {operator_id}")
        return

    if verified_id != operator_id:
        await websocket.accept()
        await websocket.close(code=1008)
        logger.warning(f"[AUTH] Token ne correspond pas à operator_id {operator_id}")
        await manager.security_event("danger", f"🚫 Usurpation détectée : token de {verified_id} utilisé pour {operator_id}")
        return

    await websocket.accept()
    await manager.connect_operator(operator_id, websocket)
    await manager.security_event("success", f"🔌 Opérateur {operator_id} connecté avec token valide")
    logger.info(f"[WS-OPERATOR] {operator_id} connecté ✓")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = CommandMessage(**json.loads(data))
                logger.info(f"[WS-OPERATOR] commande de {operator_id}: throttle={command.throttle} steering={command.steering} brake={command.brake}")
                await manager.relay_to_vehicle("taxi_42", data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"[WS-OPERATOR] Commande invalide ignorée: {e}")
    except WebSocketDisconnect:
        logger.warning(f"[WS-OPERATOR] {operator_id} déconnecté")
        manager.disconnect_operator(operator_id)
    except Exception as e:
        logger.error(f"[WS-OPERATOR] Erreur: {e}")
        manager.disconnect_operator(operator_id)
        await websocket.close(code=1011)

# ========================================================================
# DASHBOARD
# ========================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Servir le dashboard de monitoring temps réel."""
    html_path = Path(__file__).parent / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket réservé au dashboard — lecture seule, pas d'auth requise."""
    await websocket.accept()
    await manager.connect_observer(websocket)
    logger.info("[DASHBOARD] Observateur connecté")
    try:
        while True:
            await websocket.receive_text()  # garder la connexion ouverte
    except WebSocketDisconnect:
        manager.disconnect_observer(websocket)
        logger.info("[DASHBOARD] Observateur déconnecté")


# ========================================================================
# POINT D'ENTRÉE
# ========================================================================

if __name__ == "__main__":
    import uvicorn

    # À lancer : python server.py
    # Ou en production : uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # reload auto quand tu modifies le fichier (dev only)
    )
