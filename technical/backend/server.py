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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os
from datetime import datetime

# ========================================================================
# CONFIGURATION
# ========================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "15"))

# ========================================================================
# STRUCTURES DE DONNÉES (placeholder)
# ========================================================================
# En semaine 2, remplacer par les vrais modèles Pydantic
# Pydantic = validation + serialization de données en Python

class LoginRequest:
    """Placeholder pour la requête de login"""
    pass

class TokenResponse:
    """Placeholder pour la réponse JWT"""
    pass

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

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Login — émettre un JWT pour un opérateur.

    POST /auth/login
    {
      "operator_id": "operator_001",
      "password": "..."
    }

    Retourne :
    {
      "access_token": "eyJhbGc...",
      "token_type": "bearer",
      "expires_in": 900
    }

    Concepts :
    - JWT (JSON Web Token) = stateless authentication
    - Payload JWT = données du token (operator_id, vehicle_id, expiry, etc.)
    - Signature = preuve que le token vient du backend
    """
    logger.info(f"[AUTH] Tentative login...")
    # TODO : implémenter l'authentification réelle
    raise HTTPException(status_code=501, detail="Not implemented")

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
    """
    WebSocket du véhicule.

    Concepts :
    - WebSocket = connexion bidirectionnelle persistent (vs HTTP request/response)
    - Le véhicule se connecte et reçoit les commandes du backend
    - Le véhicule envoie la télémétrie en continu

    Flow :
    1. Vehicle: ws://backend:8000/ws/vehicle/taxi_42
    2. Backend: await websocket.accept()
    3. Vehicle: envoie télémétrie (20 Hz, toutes les 50ms)
    4. Backend: reçoit + relaye aux opérateurs
    """
    logger.info(f"[WS-VEHICLE] Connexion véhicule {vehicle_id}")

    try:
        await websocket.accept()
        logger.info(f"[WS-VEHICLE] {vehicle_id} connecté ✓")

        # Boucle de réception des messages
        while True:
            # Recevoir les données du véhicule
            data = await websocket.receive_text()
            # TODO : parser les données (JSON)
            # TODO : valider les données
            # TODO : relayer aux opérateurs supervisant ce véhicule
            logger.info(f"[WS-VEHICLE] {vehicle_id}: {data[:50]}...")

    except WebSocketDisconnect:
        logger.warning(f"[WS-VEHICLE] {vehicle_id} déconnecté")
        # TODO : nettoyer la session
    except Exception as e:
        logger.error(f"[WS-VEHICLE] Erreur: {e}")
        await websocket.close(code=1011)


@app.websocket("/ws/operator/{operator_id}")
async def websocket_operator(websocket: WebSocket, operator_id: str):
    """
    WebSocket de l'opérateur.

    L'opérateur se connecte, envoie des commandes, et reçoit la télémétrie
    du véhicule qu'il supervise.
    """
    logger.info(f"[WS-OPERATOR] Connexion opérateur {operator_id}")

    try:
        await websocket.accept()
        logger.info(f"[WS-OPERATOR] {operator_id} connecté ✓")

        while True:
            # Recevoir les commandes de l'opérateur
            data = await websocket.receive_text()
            # TODO : parser JSON
            # TODO : vérifier que l'opérateur a le droit de contrôler ce véhicule (RBAC)
            # TODO : valider la commande (sémantique)
            # TODO : relayer au véhicule
            logger.info(f"[WS-OPERATOR] {operator_id}: {data[:50]}...")

    except WebSocketDisconnect:
        logger.warning(f"[WS-OPERATOR] {operator_id} déconnecté")
    except Exception as e:
        logger.error(f"[WS-OPERATOR] Erreur: {e}")
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
