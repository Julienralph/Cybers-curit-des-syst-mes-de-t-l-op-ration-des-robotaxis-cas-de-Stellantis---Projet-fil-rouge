# Cybersécurité des systèmes de téléopération pour robotaxis

**Projet fil rouge — Mastère Spécialisé Expert Cybersécurité, Télécom Paris 2025-2026**

Commanditaire : **Stellantis**

Soutenance : **30 juin 2026**

---

## Vue d'ensemble

Ce projet implémente une **architecture Zero Trust** pour un système de téléopération sécurisée de robotaxis. L'enjeu cybersécurité porte sur la **sécurisation du canal de communication** entre le véhicule, l'opérateur et le serveur de coordination.

### Thématiques retenues

| # | Thème | Responsable | Livrable |
|---|---|---|---|
| 1 | Sécurisation du canal (WebRTC/TLS) | Tech | Demo MITM bloqué, rapport vulnérabilités |
| 2 | Attaques latence/QoS (DoS, Netem) | Tech | Dashboard Grafana, métriques |
| 5 | Architecture Zero Trust | Tech + GRC | Diagramme + politique sécurité |

### Standards de référence

- **ISO 21434** — Cybersécurité automobile
- **UNECE R155** — Règlement véhicules connectés
- **NIST Zero Trust** — Architecture stateless (SP 800-207)

---

## Architecture

```
┌─────────────────────────────────────────┐
│   INTERNET (Trust: ZERO)                │
│   [MITM] [DoS] [Replay] [Non chiffré]   │
└─────────────────────────────────────────┘
  │ mTLS 1.3 + DTLS/SRTP          │ JWT + mTLS
  ▼                                ▼
┌────────────────┐          ┌──────────────────┐
│  VEHICLE ZONE  │          │  OPERATOR ZONE   │
│  Trust: HIGH   │          │  Trust: COND.    │
└────────┬───────┘          └─────────┬────────┘
         │                           │
         └────── TLS 1.3 ────────────┘
                    │
          ┌─────────▼────────┐
          │  BACKEND ZONE    │
          │  FastAPI         │
          │  WebSocket       │
          │  JWT Auth        │
          │  Rate Limiter    │
          │  Anomaly Det.    │
          └─────────┬────────┘
                    │ Metrics
          ┌─────────▼────────┐
          │   MONITORING     │
          │  Prometheus      │
          │  Grafana         │
          └──────────────────┘
```

---

## Stack technique

- **Backend :** Python 3.11, FastAPI, WebSocket async
- **Simulation :** Python 3.11, asyncio
- **Crypto :** OpenSSL (TLS 1.3, mTLS, certificats)
- **Auth :** JWT (python-jose)
- **Protection :** Rate limiting (slowapi), Anomaly detection
- **Monitoring :** Prometheus, Grafana
- **Infrastructure :** Docker Compose

---

## Quickstart

### Prérequis

- Docker Desktop (24+)
- Docker Compose (2.x)
- Git

### Démarrer le système

```bash
# 1. Cloner le repo
git clone https://github.com/Julienralph/[repo-name].git
cd [repo-name]

# 2. Copier .env.example
cp .env.example .env

# 3. Générer les certificats TLS (OpenSSL)
mkdir -p technical/certs
cd technical/certs

# CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 365 \
  -subj "/CN=Teleop-CA/O=TelecomParis/C=FR"

# Certificat serveur
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/CN=backend/O=TelecomParis/C=FR"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365

# Certificat client
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
  -subj "/CN=vehicle/O=TelecomParis/C=FR"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days 365

cd ../..

# 4. Lancer les services
docker compose up --build

# 5. Logs
docker compose logs -f backend
```

---

## Structure du projet

```
technical/
  ├── backend/          # FastAPI server
  ├── vehicle/          # Simulateur véhicule
  ├── operator/         # Client opérateur
  ├── certs/            # Certificats TLS
  ├── monitoring/       # Prometheus + Grafana
  └── attacks/          # Scripts d'attaque (semaine 3)

grc/                    # Partie GRC (binôme)
  ├── threat-modeling/
  ├── risk-assessment/
  └── compliance/

architecture/           # Diagrammes partagés
deliverables/           # Rapport + slides
```

---

## Documentation

- **CLAUDE_CONTEXT.md** — Contexte détaillé pour Claude Code (lire EN PREMIER)
- **PROJECT_STATUS.md** — Tableau d'avancement mis à jour chaque soir
- **architecture/system_diagram.drawio** — Diagramme complet
- **technical/certs/.gitkeep** — Placeholder (certificats ignorés par git)

---

## Security Requirements (SRs)

| SR | Menace | Implémentation | Status |
|----|--------|---|---|
| SR-01 | Spoofing opérateur | JWT auth | ❌ |
| SR-02 | MITM | TLS 1.3 | ❌ |
| SR-03 | DoS | Rate limiting | ❌ |
| SR-04 | mTLS vehicle | Certificats client | ❌ |
| SR-05 | Logs SIEM | Logging structuré | ❌ |
| SR-06 | Anomaly detection | Règles comportement | ❌ |
| SR-07 | RBAC | Session manager | ❌ |
| SR-08 | Fail-safe | Arrêt auto latence | ❌ |
| SR-09 | Monitoring QoS | Grafana | ❌ |
| SR-10 | Replay attack | Nonce + timestamp | ❌ |

---

## Commandes utiles

```bash
# Démarrer
docker compose up

# Arrêter
docker compose down

# Logs
docker compose logs -f backend

# Shell dans un conteneur
docker compose exec backend bash

# Nettoyer (volumes, images)
docker compose down -v
```

---

## Calendrier

- **Semaine 1 (13-14 juin) :** Architecture + Setup
- **Semaine 2 (15-21 juin) :** PoC de base
- **Semaine 3 (22-28 juin) :** Attaques + Défenses
- **Semaine 4 (29-30 juin) :** Finalisation + Soutenance

---

## Auteurs

- **Tech (Julien Ralph)** — Backend, WebSocket, Sécurité canal
- **GRC (Prénom Binôme)** — STRIDE, TARA, Conformité

---

## License

Confidentiel — Projet académique Stellantis / Télécom Paris 2026
