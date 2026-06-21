"""
technical/operator/operator_client.py — Client simulateur d'opérateur

Responsabilités :
- Simuler un opérateur qui se connecte au backend
- Envoyer des commandes (vitesse, direction, frein)
- Recevoir et afficher la télémétrie du véhicule

Concepts clés :
- Client WebSocket (vs. serveur WebSocket)
- Simulation de saisies utilisateur (automation)
- Pattern de communication request/response
"""

import asyncio
import json
import logging
import os
from datetime import datetime
import aiohttp

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "ws://backend:8000")
BACKEND_HTTP_URL = BACKEND_URL.replace("ws://", "http://")
OPERATOR_ID = os.getenv("OPERATOR_ID", "operator_001")
OPERATOR_PASSWORD = os.getenv("OPERATOR_PASSWORD", "secret123")

# ========================================================================
# CLASSE PRINCIPAL — OPERATOR CLIENT
# ========================================================================

class OperatorClient:
    def __init__(self):
        self.websocket = None
        self.running = False

    async def get_jwt_token(self) -> str:
        """Appeler POST /auth/login pour obtenir un token JWT."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_HTTP_URL}/auth/login",
                json={"operator_id": OPERATOR_ID, "password": OPERATOR_PASSWORD}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Login échoué : HTTP {response.status}")
                data = await response.json()
                logger.info(f"[OPERATOR] Token JWT obtenu ✓")
                return data["access_token"]

    async def connect_to_backend(self):
        """
        Établir la connexion WebSocket avec le backend.
        Flux : POST /auth/login → JWT → WebSocket avec ?token=JWT
        """
        import websockets

        retry_delay = 5
        max_retries = 10
        retries = 0

        while retries < max_retries:
            try:
                logger.info(f"[OPERATOR] Connexion au backend ({BACKEND_URL})...")

                token = await self.get_jwt_token()

                self.websocket = await websockets.connect(
                    f"{BACKEND_URL}/ws/operator/{OPERATOR_ID}?token={token}"
                )

                logger.info(f"[OPERATOR] Connecté au backend ✓")
                retries = 0
                return True

            except Exception as e:
                retries += 1
                logger.warning(f"[OPERATOR] Erreur connexion ({retries}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)

        logger.error(f"[OPERATOR] Impossible de se connecter après {max_retries} tentatives")
        return False

    async def send_commands(self):
        """
        Envoyer des commandes simulées au backend.

        Concepts :
        - Les commandes doivent être validées côté backend (sémantique)
        - Chaque commande doit être signée/authentifiée
        - Throttling : limiter la fréquence pour simuler un humain
        """
        logger.info("[OPERATOR] Boucle d'envoi de commandes démarrée")

        command_sequence = [
            {"throttle": 0.3, "steering": 0, "description": "Accélération douce"},
            {"throttle": 0.5, "steering": 0, "description": "Accélération modérée"},
            {"throttle": 0.0, "steering": 20, "description": "Tourner à droite"},
            {"throttle": 0.3, "steering": 0, "description": "Accélération normale"},
            {"throttle": 0.0, "steering": -20, "description": "Tourner à gauche"},
            {"throttle": 0.0, "brake": 0.5, "description": "Freinage doux"},
            {"throttle": 0.0, "brake": 1.0, "description": "Arrêt complet"},
        ]

        command_index = 0

        while self.running and self.websocket:
            try:
                # Récupérer la prochaine commande (cycle infini)
                cmd_template = command_sequence[command_index % len(command_sequence)]

                # Construire la commande
                command = {
                    "type": "command",
                    "operator_id": OPERATOR_ID,
                    "timestamp": datetime.now().isoformat(),
                    "throttle": cmd_template.get("throttle", 0.0),
                    "steering": cmd_template.get("steering", 0.0),
                    "brake": cmd_template.get("brake", 0.0),
                }

                logger.info(f"[OPERATOR] Envoi: {cmd_template['description']}")

                # Envoyer la commande
                await self.websocket.send(json.dumps(command))

                # Attendre 2 secondes avant la prochaine commande
                # (simulation d'un humain qui prend du temps à réagir)
                await asyncio.sleep(2.0)

                command_index += 1

            except Exception as e:
                logger.error(f"[OPERATOR] Erreur send_commands: {e}")
                break

    async def receive_telemetry(self):
        """Recevoir la télémétrie du véhicule et l'afficher."""
        logger.info("[OPERATOR] Boucle réception télémétrie démarrée")

        while self.running and self.websocket:
            try:
                # Recevoir un message (bloquant)
                message = await self.websocket.recv()

                # TODO : parser le JSON
                # TODO : afficher les informations pertinentes

                logger.info(f"[OPERATOR] Télémétrie reçue: {message[:100]}...")

            except Exception as e:
                logger.error(f"[OPERATOR] Erreur receive_telemetry: {e}")
                break

    async def run(self):
        """Démarrer le client opérateur (point d'entrée principal)."""
        logger.info(f"[OPERATOR] Démarrage du client {OPERATOR_ID}...")
        self.running = True

        # Étape 1 : connexion au backend
        if not await self.connect_to_backend():
            logger.error("[OPERATOR] Impossible de se connecter au backend")
            return

        # Étape 2 : lancer les tâches asynchrones en parallèle
        try:
            await asyncio.gather(
                self.send_commands(),
                self.receive_telemetry()
            )
        except KeyboardInterrupt:
            logger.info("[OPERATOR] Arrêt demandé (Ctrl+C)")
        except Exception as e:
            logger.error(f"[OPERATOR] Erreur fatale: {e}")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()
            logger.info("[OPERATOR] Client arrêté")

# ========================================================================
# POINT D'ENTRÉE
# ========================================================================

if __name__ == "__main__":
    client = OperatorClient()
    asyncio.run(client.run())
