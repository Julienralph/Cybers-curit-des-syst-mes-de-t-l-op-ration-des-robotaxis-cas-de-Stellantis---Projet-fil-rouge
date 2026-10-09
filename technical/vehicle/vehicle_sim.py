"""
technical/vehicle/vehicle_sim.py — Simulateur de véhicule

Responsabilités :
- Simuler l'état du CAN Bus (vitesse, accélération, GPS, batterie, etc.)
- Envoyer la télémétrie au backend toutes les 50ms (20 Hz)
- Recevoir et appliquer les commandes du backend
- Implémenter le fail-safe si latence > 700ms

Concepts clés :
- asyncio : programmation asynchrone (non-bloquant)
- websockets : client WebSocket
- State machine : états du véhicule (autonomous, teleoperated, emergency)
"""

import asyncio
import json
import logging
import os
import ssl
from datetime import datetime
from dataclasses import dataclass, asdict

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "ws://backend:8000")
VEHICLE_ID = os.getenv("VEHICLE_ID", "taxi_42")
LATENCY_FAILSAFE_MS = int(os.getenv("LATENCY_FAILSAFE_MS", "700"))

# ========================================================================
# ÉTAT DU VÉHICULE
# ========================================================================
# Simule les capteurs du CAN Bus

@dataclass
class VehicleState:
    """État interne du véhicule."""
    vehicle_id: str
    speed: float = 0.0           # km/h
    steering_angle: float = 0.0  # degrés (-90 à +90)
    brake_pressure: float = 0.0  # 0.0 à 1.0
    throttle: float = 0.0        # 0.0 à 1.0
    gps_lat: float = 48.8566     # coordonnées Paris
    gps_lon: float = 2.3522
    battery: float = 87.0        # %
    status: str = "autonomous"   # autonomous | teleoperated | emergency
    last_cmd_timestamp: float = None

    def to_json(self) -> str:
        """Convertir en JSON pour transmission."""
        return json.dumps(asdict(self))

# ========================================================================
# CLASSE PRINCIPALE — VEHICLE SIMULATOR
# ========================================================================

class VehicleSimulator:
    def __init__(self):
        self.state = VehicleState(vehicle_id=VEHICLE_ID)
        self.websocket = None
        self.running = False

    async def connect_to_backend(self):
        """
        Établir la connexion WebSocket avec le backend.

        Concepts :
        - Retry logic : reconnexion automatique si déconnexion
        - mTLS : certificats client/CA
        """
        import websockets

        retry_delay = 5
        max_retries = 10
        retries = 0

        while retries < max_retries:
            try:
                logger.info(f"[VEHICLE] Connexion au backend ({BACKEND_URL})...")

                ssl_context = ssl.create_default_context()
                ssl_context.load_verify_locations(os.getenv("CA_CERT_PATH", "/certs/ca.crt"))

                self.websocket = await websockets.connect(
                    f"{BACKEND_URL}/ws/vehicle/{VEHICLE_ID}",
                    ssl=ssl_context
                )

                logger.info(f"[VEHICLE] Connecté au backend ✓")
                retries = 0  # reset counter on success
                return True

            except Exception as e:
                retries += 1
                logger.warning(f"[VEHICLE] Erreur connexion ({retries}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)

        logger.error(f"[VEHICLE] Impossible de se connecter après {max_retries} tentatives")
        return False

    async def send_telemetry(self):
        """Envoyer la télémétrie au backend toutes les 50ms (20 Hz)."""
        logger.info("[VEHICLE] Boucle télémétrie démarrée (20 Hz = 50ms)")

        while self.running and self.websocket:
            try:
                # Préparer les données de télémétrie
                telemetry = {
                    "type": "telemetry",
                    "vehicle_id": self.state.vehicle_id,
                    "timestamp": datetime.now().isoformat(),
                    "speed": self.state.speed,
                    "steering_angle": self.state.steering_angle,
                    "brake_pressure": self.state.brake_pressure,
                    "throttle": self.state.throttle,
                    "gps": {
                        "lat": self.state.gps_lat,
                        "lon": self.state.gps_lon
                    },
                    "battery": self.state.battery,
                    "status": self.state.status
                }

                # Envoyer au backend
                await self.websocket.send(json.dumps(telemetry))
                # logger.debug(f"[VEHICLE] Télémétrie envoyée: speed={self.state.speed}")

                # Attendre 50ms avant la prochaine télémétrie (20 Hz)
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"[VEHICLE] Erreur send_telemetry: {e}")
                break

    async def receive_commands(self):
        """Recevoir les commandes du backend et les appliquer."""
        logger.info("[VEHICLE] Boucle réception commandes démarrée")

        while self.running and self.websocket:
            try:
                # Recevoir un message (bloquant jusqu'à reception)
                message = await self.websocket.recv()

                # TODO : parser et valider le JSON
                # TODO : vérifier la signature JWT si nécessaire
                # TODO : valider la plausibilité de la commande (sémantique)
                # TODO : appliquer la commande à vehicle_state

                logger.info(f"[VEHICLE] Commande reçue: {message[:100]}...")

                # Mettre à jour timestamp pour fail-safe + repasser en téleopération
                self.state.last_cmd_timestamp = datetime.now().timestamp()
                self.state.status = "teleoperated"

            except Exception as e:
                logger.error(f"[VEHICLE] Erreur receive_commands: {e}")
                break

    async def check_failsafe(self):
        """
        Vérifier si le fail-safe doit s'activer.

        SR-08 : Si pas de commande depuis 700ms → arrêt automatique
        """
        while self.running:
            try:
                current_time = datetime.now().timestamp()

                if self.state.last_cmd_timestamp:
                    elapsed_ms = (current_time - self.state.last_cmd_timestamp) * 1000

                    if elapsed_ms > LATENCY_FAILSAFE_MS:
                        logger.critical(f"[VEHICLE] FAIL-SAFE ACTIVÉ ! Latence > {LATENCY_FAILSAFE_MS}ms")
                        # TODO : implémenter l'arrêt (freinage d'urgence)
                        self.state.status = "emergency"
                        self.state.throttle = 0.0
                        self.state.brake_pressure = 1.0

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"[VEHICLE] Erreur check_failsafe: {e}")

    async def simulate_physics(self):
        """
        Simuler la physique basique du véhicule.

        (Optionnel — pour rendre la simulation plus réaliste)
        """
        while self.running:
            try:
                # Simulation très simple : accélération/décélération
                max_speed = 120.0  # km/h

                if self.state.throttle > 0:
                    # Accélérer progressivement
                    self.state.speed = min(
                        self.state.speed + self.state.throttle * 2,
                        max_speed
                    )
                elif self.state.brake_pressure > 0:
                    # Freiner
                    self.state.speed = max(
                        self.state.speed - self.state.brake_pressure * 5,
                        0.0
                    )
                else:
                    # Décélération passive (friction)
                    self.state.speed = max(self.state.speed - 0.5, 0.0)

                # Consommation batterie (très simple)
                if self.state.speed > 0:
                    self.state.battery -= 0.01

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"[VEHICLE] Erreur simulate_physics: {e}")

    async def run(self):
        """Démarrer le simulateur (point d'entrée principal)."""
        logger.info(f"[VEHICLE] Démarrage du simulateur {VEHICLE_ID}...")
        self.running = True

        # Étape 1 : connexion au backend
        if not await self.connect_to_backend():
            logger.error("[VEHICLE] Impossible de se connecter au backend")
            return

        # Étape 2 : lancer les tâches asynchrones en parallèle
        try:
            await asyncio.gather(
                self.send_telemetry(),
                self.receive_commands(),
                self.check_failsafe(),
                self.simulate_physics()
            )
        except KeyboardInterrupt:
            logger.info("[VEHICLE] Arrêt demandé (Ctrl+C)")
        except Exception as e:
            logger.error(f"[VEHICLE] Erreur fatale: {e}")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()
            logger.info("[VEHICLE] Simulateur arrêté")

# ========================================================================
# POINT D'ENTRÉE
# ========================================================================

if __name__ == "__main__":
    simulator = VehicleSimulator()
    asyncio.run(simulator.run())
