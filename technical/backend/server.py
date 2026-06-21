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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
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

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "15"))

# Credentials hardcodés pour la démo (en prod : base de données)
OPERATORS_DB = {
    "operator_001": "secret123",
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
        self.vehicles: dict[str, WebSocket] = {}    # vehicle_id → WebSocket
        self.operators: dict[str, WebSocket] = {}   # operator_id → WebSocket

    async def connect_vehicle(self, vehicle_id: str, ws: WebSocket):
        self.vehicles[vehicle_id] = ws

    async def connect_operator(self, operator_id: str, ws: WebSocket):
        self.operators[operator_id] = ws

    def disconnect_vehicle(self, vehicle_id: str):
        self.vehicles.pop(vehicle_id, None)

    def disconnect_operator(self, operator_id: str):
        self.operators.pop(operator_id, None)

    async def relay_to_operators(self, data: str):
        """Envoie la télémétrie du véhicule à tous les opérateurs connectés."""
        for op_ws in self.operators.values():
            await op_ws.send_text(data)

    async def relay_to_vehicle(self, vehicle_id: str, data: str):
        """Envoie une commande d'un opérateur vers un véhicule spécifique."""
        ws = self.vehicles.get(vehicle_id)
        if ws:
            await ws.send_text(data)

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
async def login(request: LoginRequest):
    """
    Login — émettre un JWT pour un opérateur.

    POST /auth/login
    Body : {"operator_id": "operator_001", "password": "secret123"}
    Retourne : {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 900}
    """
    logger.info(f"[AUTH] Tentative login pour {request.operator_id}")

    expected_password = OPERATORS_DB.get(request.operator_id)
    if not expected_password or expected_password != request.password:
        logger.warning(f"[AUTH] Échec login pour {request.operator_id}")
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token(request.operator_id)
    logger.info(f"[AUTH] Token émis pour {request.operator_id}")
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
    """
    Exposition des métriques Prometheus.

    Prometheus va scraper cette route toutes les 15 secondes
    et collecter les métriques (latence, erreurs, etc.)
    """
    # TODO : utiliser prometheus_client pour exporter les métriques
    logger.info("[METRICS] Exposition des métriques...")
    return {"todo": "Prometheus metrics"}

# ========================================================================
# ROUTES WEBSOCKET — Communication temps réel
# ========================================================================

@app.websocket("/ws/vehicle/{vehicle_id}")
async def websocket_vehicle(websocket: WebSocket, vehicle_id: str):
    await websocket.accept()
    await manager.connect_vehicle(vehicle_id, websocket)
    logger.info(f"[WS-VEHICLE] {vehicle_id} connecté ✓")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                telemetry = TelemetryMessage(**json.loads(data))
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
async def websocket_operator(websocket: WebSocket, operator_id: str, token: str = Query(...)):
    try:
        verified_id = verify_token(token)
    except JWTError:
        await websocket.close(code=1008)  # 1008 = Policy Violation
        logger.warning(f"[AUTH] Connexion WebSocket refusée pour {operator_id} : token invalide")
        return

    if verified_id != operator_id:
        await websocket.close(code=1008)
        logger.warning(f"[AUTH] Token ne correspond pas à operator_id {operator_id}")
        return

    await websocket.accept()
    await manager.connect_operator(operator_id, websocket)
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
