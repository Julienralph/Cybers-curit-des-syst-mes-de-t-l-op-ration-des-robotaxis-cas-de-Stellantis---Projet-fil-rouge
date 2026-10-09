"""
attacks/dos_attack.py — Simulation d'une attaque DoS / Brute Force

Scénario :
    Un attaquant envoie des dizaines de requêtes rapides sur /auth/login
    pour tenter de deviner le mot de passe (brute force) ou saturer le serveur.

Contre-mesure démontrée :
    Le rate limiter slowapi bloque après 5 tentatives par minute par IP.
    Les requêtes 6+ reçoivent HTTP 429 Too Many Requests.
    Le dashboard affiche l'alerte "Brute force bloqué" en temps réel.

Usage :
    pip install aiohttp
    python attacks/dos_attack.py
"""

import asyncio
import aiohttp
import ssl
import time

BACKEND_HTTPS = "https://localhost:8000"

# Désactivation SSL (attaquant sans notre CA)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# Mots de passe testés par l'attaquant (dictionnaire)
PASSWORDS = [
    "password", "123456", "admin", "secret", "operator",
    "teleop", "robotaxi", "stellantis", "hack", "root",
    "qwerty", "letmein", "welcome", "test", "pass123",
    "secure", "access", "control", "remote", "fleet",
]


async def send_login(session: aiohttp.ClientSession, attempt: int, password: str) -> int:
    try:
        async with session.post(
            f"{BACKEND_HTTPS}/auth/login",
            json={"operator_id": "operator_001", "password": password},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            status = resp.status
            if status == 200:
                label = "✅ SUCCÈS (mot de passe trouvé !)"
            elif status == 401:
                label = "❌ Mauvais mot de passe"
            elif status == 429:
                label = "🛡️  BLOQUÉ par rate limiter (429)"
            else:
                label = f"HTTP {status}"
            print(f"  [{attempt:02d}] password='{password}' → {label}")
            return status
    except Exception as e:
        print(f"  [{attempt:02d}] Erreur réseau : {e}")
        return 0


async def dos_attack():
    print("=" * 60)
    print("   SIMULATION — DoS / BRUTE FORCE ATTACK")
    print("=" * 60)
    print(f"\n[*] Cible : {BACKEND_HTTPS}/auth/login")
    print(f"[*] Utilisateur ciblé : operator_001")
    print(f"[*] Nombre de tentatives : {len(PASSWORDS)}")
    print(f"[*] Rate limit attendu : 5 req/minute → blocage à partir de la 6e\n")

    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    stats = {200: 0, 401: 0, 429: 0}

    async with aiohttp.ClientSession(connector=connector) as session:
        for i, pwd in enumerate(PASSWORDS, start=1):
            status = await send_login(session, i, pwd)
            if status in stats:
                stats[status] += 1
            await asyncio.sleep(0.3)

    print("\n" + "=" * 60)
    print("RÉSULTATS")
    print(f"  Succès (200)       : {stats[200]}")
    print(f"  Mauvais pwd (401)  : {stats[401]}")
    print(f"  Bloqué (429)       : {stats[429]}")
    print("\nCONTRE-MESURE : Rate limiting slowapi")
    print("  → Max 5 tentatives/minute/IP")
    print("  → Alerte 'Brute force bloqué' visible sur le dashboard")
    print("  → Attaquant doit attendre 1 minute entre chaque série")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(dos_attack())
