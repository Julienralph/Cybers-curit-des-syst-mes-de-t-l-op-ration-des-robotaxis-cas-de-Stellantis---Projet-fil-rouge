# PROJECT_STATUS.md

Tableau d'avancement du projet fil rouge. Mis à jour chaque fin de journée.

**Dernière mise à jour :** 14 juin 2026, 14h00

---

## Avancement par Security Requirement (SR)

| SR | Menace (STRIDE) | Priorité | GRC | Tech | Validé | Fichier implémentation |
|----|---|---|---|---|---|---|
| SR-01 | T1 - Spoofing opérateur | CRITIQUE | ❌ | ❌ | ❌ | `backend/auth.py` |
| SR-02 | T4 - Info Disclosure (MITM) | CRITIQUE | ❌ | ❌ | ❌ | `docker-compose.yml` (TLS config) |
| SR-03 | T5 - DoS WebSocket | CRITIQUE | ❌ | ❌ | ❌ | `backend/rate_limiter.py` |
| SR-04 | T2 - Tampering (mTLS vehicle) | CRITIQUE | ❌ | ❌ | ❌ | `technical/certs/` + `vehicle_sim.py` |
| SR-05 | T3 - Repudiation (Logs SIEM) | ÉLEVÉ | ❌ | ❌ | ❌ | `backend/logs.py` |
| SR-06 | ZT-CV - Anomaly detection | ÉLEVÉ | ❌ | ❌ | ❌ | `backend/anomaly_detector.py` |
| SR-07 | T6 - Elevation (RBAC) | ÉLEVÉ | ❌ | ❌ | ❌ | `backend/session_manager.py` |
| SR-08 | Safety - Fail-safe | CRITIQUE | ❌ | ❌ | ❌ | `vehicle/failsafe.py` |
| SR-09 | Thème 2 - Monitoring QoS | ÉLEVÉ | ❌ | ❌ | ❌ | `technical/monitoring/` |
| SR-10 | Replay attack | ÉLEVÉ | ❌ | ❌ | ❌ | `backend/auth.py` (nonce) |

**Légende :** ✅ Terminé · 🔄 En cours · ❌ Pas commencé

---

## Semaine 1 (13-14 juin) — Architecture + Setup

**État :** En cours

- [x] Architecture draw.io terminée
- [x] Décisions techniques figées
- [x] Repo GitHub créé
- [x] Structure locale clonée
- [x] `docker-compose.yml` créé
- [x] Dockerfile (backend, vehicle, operator)
- [x] Skeletons Python (server.py, vehicle_sim.py, operator_client.py)
- [x] `.gitignore` + `.env.example` committés
- [ ] Test : `docker compose up` sans erreurs

**À faire demain :**
- Test local du docker-compose
- Premiers commits sur `develop`

---

## Semaine 2 (15-21 juin) — PoC de base

**État :** À venir

**Tâches :**
- [ ] `backend/server.py` : FastAPI + routes WebSocket complètes
- [ ] `backend/auth.py` : JWT complet (génération + vérification, SR-01)
- [ ] `vehicle/vehicle_sim.py` : télémétrie simulée en boucle
- [ ] `operator/operator_client.py` : envoi commandes avec JWT
- [ ] Certificats TLS (OpenSSL)
- [ ] mTLS configuré entre vehicle et backend (SR-04)
- [ ] `backend/session_manager.py` : RBAC (SR-07)
- [ ] **VALIDATION** : `docker compose up` → communication fonctionnelle

---

## Semaine 3 (22-28 juin) — Attaques + Défenses

**État :** À venir

- [ ] `backend/rate_limiter.py` : slowapi (SR-03)
- [ ] `backend/anomaly_detector.py` : règles comportementales (SR-06)
- [ ] `backend/logs.py` : logging structuré SIEM (SR-05)
- [ ] `attacks/dos_simulation.py` : flood WebSocket
- [ ] `attacks/mitm_attempt.py` : mitmproxy avant/après TLS
- [ ] `attacks/replay_attack.py` : capture + rejeu
- [ ] `attacks/latency_injection.sh` : tc netem
- [ ] `vehicle/failsafe.py` : fail-safe automatique (SR-08)
- [ ] `technical/monitoring/` : Prometheus + Grafana (SR-09)
- [ ] **DEMO FLOW** : attaque → défense → métriques Grafana

---

## Semaine 4 (29-30 juin) — Finalisation

**État :** À venir

- [ ] Dashboard Grafana finalisé
- [ ] README.md complet
- [ ] Rapport final (sections Tech)
- [ ] Slides soutenance
- [ ] Répétition démo chronométrée

---

## Blocages actuels

Aucun pour le moment.

---

## Métriques clés

| Métrique | Valeur |
|---|---|
| Jours restants | 16 (jusqu'au 30 juin) |
| Services à implémenter | 3 (backend, vehicle, operator) |
| Security Requirements | 10 |
| SRs achevées | 0 / 10 |
| Fichiers Python | ~15 |

---

## Prochaines étapes immédiates

1. **Commit #1 :** Structure + docker-compose + skeletons
2. **Test local :** `docker compose up` et vérifier aucune erreur
3. **Semaine 2 :** Implémenter le PoC FastAPI + WebSocket

---

## Notes

- Travail en binôme : Tech (Julien) / GRC (binôme)
- Soutenance : 30 juin 2026
- Repo : https://github.com/Julienralph/[long-name]
- Tous les skeletons incluent des commentaires `# TODO` pour les implémentations futures
