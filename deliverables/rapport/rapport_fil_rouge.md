# Cybersécurité d'un Système de Téléopération de Robotaxi
## Rapport de Projet Fil Rouge — Groupe n°6

**[INSÉRER LOGO TÉLÉCOM PARIS + IP PARIS]**

| | |
|---|---|
| **Formation** | Mastère Spécialisé Expert Cybersécurité des Réseaux et des SI |
| **Promotion** | 2025-2026 |
| **Commanditaire** | Stellantis |
| **Groupe** | N°6 |
| **Membres** | [À compléter] · [À compléter] |
| **Date de soutenance** | 30 juin 2026 |

---

## Table des matières

1. Introduction
2. État de l'art
3. Architecture du système de téléopération
4. Analyse des risques
   - 4.1 Crown Jewels Analysis (CJA)
   - 4.2 Analyse des menaces par STRIDE
   - 4.3 TARA — Évaluation et sélection des contremesures
   - 4.4 Approche MORDA
5. Prototype MVP : implémentation technique
6. Mécanismes de sécurité déployés (Blue Team)
7. Simulation d'attaques et contre-mesures (Red Team)
8. Observabilité et métriques de sécurité
9. Discussion et analyse critique
10. Conclusion et perspectives
11. Références bibliographiques

---

## 1. Introduction

L'industrie automobile traverse une période de transformation sans précédent. Véhicules connectés, conduite autonome, flottes robotisées : ces évolutions convergent vers un nouveau paradigme dans lequel la cybersécurité n'est plus une couche optionnelle mais une exigence architecturale fondamentale. Parmi les fonctionnalités les plus prometteuses — et les plus exposées — de ce nouvel écosystème figure la téléopération : la capacité de contrôler à distance un véhicule autonome depuis un poste de commande humain.

Stellantis, comme d'autres grands constructeurs, explore activement la téléopération pour ses flottes de robotaxis. L'enjeu est double : d'un côté, garantir la disponibilité du service et la fluidité de la commande (latence inférieure à 100 ms, continuité du flux vidéo, résilience aux coupures réseau) ; de l'autre, protéger ce canal contre des adversaires qui pourraient exploiter la moindre faille pour prendre le contrôle d'un véhicule en circulation, avec des conséquences potentiellement mortelles.

Ce rapport présente le travail réalisé dans le cadre du projet Fil Rouge du Mastère Spécialisé Expert Cybersécurité à Télécom Paris. Notre mission était de concevoir, implémenter et tester un prototype fonctionnel de système de téléopération sécurisé pour robotaxi, couvrant l'analyse de risques, l'architecture Zero Trust, la protection du canal de communication, et la simulation d'attaques réalistes avec leurs contre-mesures associées.

L'ensemble du système est reproductible en une seule commande (`docker compose up --build`) à partir du dépôt fourni en annexe. Toutes les captures présentées dans ce rapport proviennent d'exécutions réelles du système.

---

## 2. État de l'art

### 2.1 La téléopération de véhicules : définition et enjeux

La téléopération — ou téléconduite — désigne le contrôle à distance d'un véhicule par un opérateur humain qui n'est pas physiquement présent à bord. Contrairement à la conduite autonome totale, elle suppose une boucle de rétroaction entre le véhicule et l'opérateur : le véhicule transmet en temps réel sa télémétrie et son flux vidéo, et l'opérateur envoie des commandes de direction, d'accélération et de freinage [3].

Les contraintes temporelles de ce type de système sont sévères. Un délai de bout en bout supérieur à 300 ms entre la caméra embarquée et l'écran de l'opérateur commence à dégrader significativement les capacités de contrôle humain, et au-delà de 700 ms, le risque d'accident augmente de façon mesurable [3]. Ces contraintes se traduisent directement en exigences de cybersécurité : tout mécanisme de protection qui introduit une latence doit être soigneusement calibré pour rester dans les limites acceptables.

### 2.2 Vecteurs d'attaque spécifiques à la téléopération

Les systèmes de téléopération présentent une surface d'attaque étendue et particulière. Comme le souligne le rapport de référence sur la cybersécurité de la téléconduite fourni par Stellantis [2], plusieurs familles d'attaques sont documentées dans des systèmes comparables (UAVs, metro automatisé, chirurgie à distance) :

- **Attaques sur le canal de commande** : interception (Man-in-the-Middle), injection de fausses commandes, replay d'instructions valides capturées antérieurement.
- **Attaques sur la disponibilité** : saturation par déni de service (DoS), dégradation artificielle de la qualité réseau par injection de latence ou de pertes de paquets.
- **Usurpation d'identité** : un attaquant qui parviendrait à obtenir ou à reproduire les credentials d'un opérateur légitime pourrait prendre le contrôle d'un véhicule sans alerter le système.
- **Altération des données de perception** : falsification du flux vidéo ou des données de télémétrie GPS pour induire l'opérateur en erreur.

### 2.3 Cadres réglementaires et normatifs de référence

La cybersécurité automobile est aujourd'hui encadrée par deux textes majeurs. La norme **ISO/SAE 21434:2021** [6] définit les exigences d'ingénierie cybersécurité pour les véhicules routiers, couvrant l'ensemble du cycle de vie depuis la conception jusqu'au décommissionnement. Elle introduit notamment le concept de TARA (Threat Analysis and Risk Assessment), qui est la méthodologie de référence pour l'évaluation des risques dans ce domaine.

Le **règlement UNECE N°155 (R155)** [7], entré en vigueur en 2022, impose aux constructeurs souhaitant homologuer leurs véhicules en Europe de disposer d'un système de management de la cybersécurité (CSMS) certifié. Il s'applique à tous les véhicules connectés, et la téléopération en est un cas d'usage central.

Enfin, le **NIST SP 800-207** [5] formalise les principes de l'architecture Zero Trust : aucun composant n'est considéré comme intrinsèquement de confiance, chaque accès est vérifié indépendamment, et la micro-segmentation des ressources est privilégiée. Ces principes ont guidé les choix architecturaux de notre prototype.

### 2.4 Protocoles et technologies de référence

Le projet Stellantis [1] préconise l'utilisation de **WebRTC** pour le canal multimédia (flux vidéo, audio) et de **WebSocket sur TLS** pour les commandes de conduite. WebRTC intègre nativement DTLS pour le chiffrement du canal de données et SRTP pour les flux média, offrant une latence optimisée pour les communications temps réel. Le standard **5G**, analysé dans le whitepaper 5GOR [4], apporte la connectivité ultra-fiable et basse latence (URLLC) nécessaire à la téléopération en conditions réelles.

Notre prototype s'appuie sur une simulation logicielle de ce canal, en utilisant WebSocket sur TLS 1.3 pour les commandes et la télémétrie, avec JWT pour l'authentification des opérateurs.

---

## 3. Architecture du système de téléopération

### 3.1 Choix d'une simulation logicielle

Conformément aux préconisations du sujet [1], nous avons opté pour une simulation logicielle complète plutôt qu'une implémentation matérielle. Ce choix est cohérent avec les pratiques industrielles : les constructeurs automobiles utilisent des environnements HIL (Hardware-in-the-Loop) simulés pour leurs tests de cybersécurité ISO 21434, précisément parce que l'enjeu cyber porte sur le canal de communication et non sur le hardware embarqué. Notre système est entièrement orchestré via Docker Compose, ce qui garantit sa reproductibilité totale : n'importe qui disposant de Docker peut démarrer le système en une commande.

### 3.2 Zones de confiance (Zero Trust)

L'architecture repose sur le principe Zero Trust [5] : aucune zone, aucun composant, aucune connexion n'est considéré comme intrinsèquement sûr. Nous avons identifié cinq zones de confiance distinctes :

**Zone Véhicule (Trust: HIGH)** — Le véhicule embarque les capteurs (GPS, caméra simulée, CAN Bus), le module de fail-safe et le client WebSocket. La confiance est élevée car le véhicule est un équipement physiquement contrôlé par Stellantis. Toutefois, son CAN Bus interne n'est pas authentifié — comme dans tout véhicule réel actuel — ce qui constitue une limite que nous documenterons dans l'analyse de risques.

**Zone Opérateur (Trust: CONDITIONAL)** — Le poste opérateur envoie les commandes de conduite et reçoit la télémétrie. La confiance est conditionnelle : l'opérateur doit s'authentifier via JWT avant toute interaction, et chaque commande est vérifiée individuellement. Cette zone est exposée au risque d'usurpation d'identité (rogue operator).

**Zone Internet / 5G-LTE (Trust: ZERO)** — Le réseau public est traité comme hostile par définition. C'est dans cette zone que se situent les attaquants potentiels (MITM, DoS, replay). Tous les échanges qui traversent cette zone sont chiffrés.

**Zone Backend (Trust: HIGH)** — Le serveur FastAPI est le cœur du système. Il concentre l'authentification JWT, le relais des commandes, la collecte de télémétrie, la protection par rate limiting, et l'exposition des métriques. Il est isolé dans un réseau Docker dédié (172.20.0.0/16).

**Zone Monitoring (Trust: CONDITIONAL)** — Le dashboard de sécurité et les métriques Prometheus constituent la surface de surveillance du système.

**[INSÉRER ICI : Diagramme d'architecture draw.io — Architecture principale du système de robotaxis]**

### 3.3 Trust Boundaries et mécanismes associés

Trois frontières de sécurité (Trust Boundaries) ont été formalisées :

| Trust Boundary | Position | Menace principale | Protection implémentée |
|---|---|---|---|
| TB-1 | Véhicule ↔ Internet | MITM, injection commandes | TLS 1.3 + vérification CA |
| TB-2 | Internet ↔ Opérateur | Usurpation, vol de token | JWT (expiration 15 min) + TLS 1.3 |
| TB-3 | Tout → Backend | DoS, credential stuffing | TLS 1.3 + Rate limiting (5 req/min/IP) |

### 3.4 Flux de données

Le système comporte quatre flux principaux :

- **Télémétrie** (Véhicule → Backend → Dashboard) : émise à 20 Hz (toutes les 50 ms), contenant vitesse, angle de braquage, pression de frein, position GPS, niveau de batterie et statut du véhicule. Ce flux est protégé par TLS 1.3.
- **Commandes** (Opérateur → Backend → Véhicule) : chaque commande est émise via WebSocket, accompagnée d'un token JWT vérifié par le backend avant relais. Le backend valide le token à chaque message, pas uniquement à la connexion initiale.
- **Authentification** (Opérateur ↔ Backend) : login HTTPS POST avec identifiants, retour d'un JWT signé HS256 avec expiration à 15 minutes.
- **Métriques** (Backend → Dashboard) : exposition des compteurs Prometheus via HTTP, visualisés en temps réel sur le dashboard.

---

## 4. Analyse des risques

### 4.1 Crown Jewels Analysis (CJA)

La Crown Jewels Analysis est une méthodologie développée par le MITRE pour identifier les cyber-actifs les plus critiques à la mission d'un système [9]. Son principe est simple : avant d'évaluer les risques, il faut comprendre ce que le système doit absolument protéger pour accomplir sa mission. Nous appliquons ici la démarche en trois étapes : décomposition de la mission, identification des actifs critiques, et analyse d'impact.

#### Décomposition de la mission

La mission centrale du système est la suivante : **permettre à un opérateur humain distant de prendre le contrôle sécurisé d'un véhicule autonome, avec une latence inférieure à 700 ms et une continuité de service garantie même sous conditions dégradées.**

Cette mission se décompose en quatre fonctions critiques :

1. **Authentifier l'opérateur** — seul un opérateur légitime et identifié peut émettre des commandes.
2. **Relayer les commandes en temps réel** — les instructions de conduite doivent parvenir au véhicule avec une latence inférieure au seuil de fail-safe.
3. **Fournir la télémétrie à l'opérateur** — l'opérateur doit disposer d'une vision fidèle et temps réel de l'état du véhicule.
4. **Activer le fail-safe en cas de perte de contrôle** — si le canal de commande est interrompu, le véhicule doit passer en mode sécurisé de façon autonome.

#### Identification des Crown Jewels

| Rang | Actif cyber | Localisation | Impact mission si compromis |
|---|---|---|---|
| 1 | Canal WebSocket de commandes | TB-1 et TB-2 | Prise de contrôle malveillante ou blocage total |
| 2 | Module d'authentification JWT | Backend | Contournement de l'identité opérateur |
| 3 | Module fail-safe | Véhicule | Absence de reprise sécurisée en cas d'attaque |
| 4 | Flux de télémétrie | TB-1 | Opérateur aveugle ou trompé sur l'état réel |
| 5 | Clé secrète JWT | Backend (env. variable) | Forge de tokens illimitée |

#### Mission Impact Analysis

Pour chaque Crown Jewel, nous évaluons l'impact d'une perte de disponibilité, d'intégrité, ou de confidentialité :

**Canal WebSocket de commandes** : une compromission en intégrité (injection de fausses commandes) ou en disponibilité (déni de service) se traduit directement par un risque de collision ou d'accident. Il s'agit de l'actif le plus critique du système. Notre contre-mesure principale : TLS 1.3 (confidentialité + intégrité) et fail-safe (résilience si disponibilité compromise).

**Module d'authentification JWT** : si un attaquant peut obtenir ou forger un token valide, il dispose d'un accès complet aux commandes pendant toute la durée de validité du token. Notre réponse : expiration à 15 minutes, vérification à chaque message (pas seulement à la connexion), et rate limiting sur le point d'entrée `/auth/login`.

**Module fail-safe** : si ce module est désactivé ou bloqué (par une attaque de latence, par exemple), le véhicule reste en attente de commandes indéfiniment au lieu de passer en mode autonome sécurisé. Notre implémentation déclenche l'état d'urgence automatiquement après 700 ms sans commande reçue.

**Flux de télémétrie** : une altération des données GPS ou de vitesse envoyées à l'opérateur constitue une attaque de type spoofing qui peut provoquer des décisions de conduite dangereuses sans que l'opérateur ne s'en rende compte. Contremesure : TLS 1.3 + validation de format (Pydantic) à la réception.

**Clé JWT** : si la clé secrète est compromise, un attaquant peut forger des tokens valides pour n'importe quel opérateur, sans limite de temps. Contremesure : stockage exclusif en variable d'environnement (jamais dans le code), rotation recommandée en production.

### 4.2 Analyse des menaces par STRIDE

STRIDE est une méthodologie de modélisation des menaces développée par Microsoft [8], structurée autour de six catégories : **S**poofing (usurpation), **T**ampering (altération), **R**epudiation (répudiation), **I**nformation Disclosure (divulgation), **D**enial of Service (déni de service), **E**levation of Privilege (élévation de privilèges).

Nous appliquons STRIDE à chaque composant du système, en nous appuyant sur les flux de données identifiés à la section 3.4.

#### Tableau STRIDE complet

| Zone | Composant | Catégorie STRIDE | Menace détaillée | Flux concerné | Contre-mesure |
|---|---|---|---|---|---|
| Vehicle Zone | CAN Bus | Tampering | Injection de messages malveillants sur le bus interne (non authentifié) | Cmds internes | Validation sémantique amont + défense en profondeur |
| Vehicle Zone | GPS | Spoofing | Falsification des coordonnées GPS envoyées au backend | Télémétrie | TLS + validation Pydantic |
| Vehicle Zone | Fail-Safe Module | Tampering | Désactivation du module pour maintenir le véhicule sous commande | Télémétrie | Logique embarquée, timeout côté véhicule |
| Vehicle Zone | Client WebSocket | Denial of Service | Saturation de la connexion pour épuiser le fail-safe | Cmds + Télémétrie | Fail-safe autonome (700 ms) |
| Internet / 5G-LTE | Canal réseau | Information Disclosure | Interception du trafic non chiffré (avant TLS) | Tous | TLS 1.3 obligatoire sur tous les flux |
| Internet / 5G-LTE | Canal réseau | Tampering | Man-in-the-Middle : modification des commandes en transit | Cmds | TLS 1.3 + vérification certificat CA |
| Internet / 5G-LTE | Canal réseau | Tampering | Replay Attack : réutilisation d'un token JWT valide capturé | Cmds + Auth | Expiration JWT 15 min |
| Internet / 5G-LTE | Canal réseau | Denial of Service | Flood de connexions pour saturer le backend | Tous | Rate limiting 5 req/min/IP |
| Operator Zone | Auth JWT Client | Spoofing | Usurpation d'identité : connexion avec credentials volés | Auth | Rate limiting + alertes dashboard |
| Operator Zone | Auth JWT Client | Tampering | Modification du token JWT en transit | Auth | Signature HS256 + TLS |
| Operator Zone | Interface commande | Tampering | Injection de commandes physiquement dangereuses (steering > 90°) | Cmds | Validation sémantique (à implémenter) |
| Operator Zone | Rogue Operator | Elevation of Privilege | Opérateur malveillant légitime envoyant des commandes dangereuses | Cmds | Monitoring comportemental |
| Backend Zone | WebSocket Signaling | Denial of Service | Force brute sur /auth/login pour saturer ou deviner le mot de passe | Cmds + Auth | Rate limiting slowapi (5/min) |
| Backend Zone | JWT Auth Verify | Spoofing | Vol de token JWT par capture réseau (avant TLS) | Auth | TLS obligatoire + expiration courte |
| Backend Zone | Session Manager | Repudiation | Accès non autorisé à un autre véhicule que celui assigné | Cmds | Vérification operator_id dans JWT |
| Backend Zone | Rate Limiter | Denial of Service | Contournement du rate limiter via rotation d'IPs | Tous | (Recommandation : fail2ban en prod) |

#### Analyse des menaces prioritaires

Trois menaces ressortent comme prioritaires au regard des Crown Jewels identifiés en 4.1 :

**MITM avant activation TLS** : avant que le chiffrement ne soit mis en place, Wireshark permet de capturer le contenu exact des messages WebSocket en clair, incluant les commandes de conduite et les tokens JWT. C'est la menace qui justifie l'ensemble du dispositif TLS de notre prototype. La Figure 8 du rapport de captures en est la démonstration directe.

**Replay Attack** : une fois un token JWT capturé (par MITM ou par compromission du poste opérateur), un attaquant peut s'en servir pour se connecter et envoyer des commandes sans connaître le mot de passe. La fenêtre d'opportunité est limitée à la durée de validité du token (15 minutes), mais cela peut suffire pour causer des dommages significatifs.

**DoS par brute force** : une attaque par dictionnaire sur `/auth/login`, même peu sophistiquée, peut saturer le serveur et empêcher les opérateurs légitimes de se connecter, rendant le véhicule incontrôlable. Sans rate limiting, notre propre script de test montre que 20 tentatives successives s'exécutent en quelques secondes.

### 4.3 TARA — Évaluation des risques et sélection des contremesures

La méthode TARA (Threat Analysis and Risk Assessment), prescrite par l'ISO 21434 [6] et détaillée dans la documentation Stellantis [2], fournit un cadre structuré pour évaluer chaque menace et sélectionner des contremesures proportionnées.

Pour chaque menace, nous évaluons :
- **Probabilité** (Faible / Moyenne / Élevée) : faisabilité technique et motivation de l'attaquant
- **Impact** (Moyen / Grave) : conséquences sur la sécurité, la disponibilité, l'intégrité
- **Niveau de risque** (1 à 4)
- **Contremesure** : mécanisme de protection sélectionné
- **Risque résiduel** : niveau de risque après application de la contremesure

| Zone | Menace | Probabilité | Impact | Risque (1-4) | Contremesure implémentée | Risque résiduel |
|---|---|---|---|---|---|---|
| Internet/5G | Interception en clair (avant TLS) | Élevée | Grave | 4 | TLS 1.3 obligatoire + CA privée | 1 |
| Internet/5G | Man-in-the-Middle (MITM) | Moyenne | Grave | 3 | TLS + vérification certificat CA | 1 |
| Internet/5G | Replay Attack (token expiré) | Moyenne | Grave | 3 | JWT expiration 15 min | 2 |
| Internet/5G | DoS Flood réseau | Élevée | Grave | 4 | Rate limiting + fail-safe véhicule | 2 |
| Backend Zone | Brute force /auth/login | Élevée | Moyen | 3 | Rate limiting 5 req/min/IP + alerte | 1 |
| Operator Zone | Connexion sans token | Élevée | Grave | 4 | Rejet WebSocket (code 1008) + alerte | 1 |
| Operator Zone | Token invalide / expiré | Moyenne | Grave | 3 | Vérification JWT + rejet + alerte | 1 |
| Operator Zone | Usurpation (operator_id ≠ token) | Faible | Grave | 2 | Vérification croisée sub/operator_id | 1 |
| Vehicle Zone | Perte de commande (latence) | Élevée | Grave | 4 | Fail-safe automatique 700 ms | 2 |
| Vehicle Zone | Injection CAN Bus | Faible | Grave | 2 | Validation sémantique amont | 2 |

**Analyse des risques résiduels :** Deux risques demeurent à niveau 2 après nos contremesures. Le premier est la replay attack avec un token non encore expiré (fenêtre de 15 minutes) : en production, il conviendrait d'implémenter une blacklist de tokens révoqués côté backend. Le second est le fail-safe : si l'attaquant injecte une latence inférieure à 700 ms de façon continue, le fail-safe ne se déclenche pas. La recommandation est de coupler le fail-safe à la vérification de la cohérence sémantique des commandes.

### 4.4 Approche MORDA

MORDA (Mission Oriented Risk and Design Analysis) est une méthodologie développée pour l'analyse des risques de systèmes d'information critiques orientés mission [1]. Elle structure l'analyse autour de la mission, des fonctions critiques qui la supportent, et des flux d'information dont dépendent ces fonctions.

#### Décomposition par flux d'information critique

| Flux | Fonction supportée | Actifs impliqués | Adversaire potentiel | Impact si compromis |
|---|---|---|---|---|
| Flux d'authentification | Contrôle d'accès opérateur | JWT, clé secrète, /auth/login | Cybercriminel externe, insider | Prise de contrôle non autorisée |
| Flux de commandes | Contrôle du véhicule | Canal WSS, JWT dans URL | Attaquant réseau, opérateur malveillant | Accident, collision |
| Flux de télémétrie | Conscience situationnelle opérateur | Canal WSS, GPS, capteurs | Attaquant réseau | Décisions erronées de conduite |
| Flux de fail-safe | Résilience et récupération | Timer 700 ms, état véhicule | DoS réseau, injection latence | Maintien sous contrôle malveillant |

#### Analyse des dépendances critiques

L'application de MORDA révèle une dépendance critique qui n'apparaît pas directement dans STRIDE : **la fonction de contrôle du véhicule dépend de la disponibilité simultanée de trois flux** (authentification, commandes, télémétrie). Si l'un d'eux est dégradé, la mission entière est compromise. Cela justifie le déploiement de mécanismes de résilience à chaque niveau : TLS pour l'intégrité des flux, fail-safe pour la résilience en cas de rupture, et métriques Prometheus pour la détection précoce de dégradation.

L'analyse MORDA confirme également que le **backend** est le point de concentration de toutes les dépendances critiques : il est à la fois le point de passage obligé de tous les flux et le composant le plus exposé aux attaques externes. Cela justifie le niveau de confiance HIGH attribué à la zone Backend et les multiples couches de protection qui y sont déployées.

---

## 5. Prototype MVP : implémentation technique

### 5.1 Vue d'ensemble de l'implémentation

Le prototype est composé de trois services Docker communiquant via un réseau isolé (`teleop_network`, subnet 172.20.0.0/16). Chaque service est conteneurisé de façon indépendante, ce qui reproduit la segmentation réseau recommandée par le principe Zero Trust.

**[INSÉRER ICI : capture docker compose ps montrant les 3 services healthy — Figure 6]**

```
Commande de démarrage :
  docker compose up --build

Services démarrés :
  backend   → FastAPI + WebSocket, port 8000 (HTTPS/WSS)
  vehicle   → Simulateur Python, connexion WSS vers backend
  operator  → Client Python, connexion WSS avec JWT
```

### 5.2 Backend FastAPI

Le backend est le composant central du système. Il est implémenté avec FastAPI (Python 3.11+), un framework asynchrone qui supporte nativement les WebSockets et expose une API HTTP pour l'authentification.

**Routes HTTP :**
- `POST /auth/login` : authentification par credentials, retour d'un JWT signé HS256
- `GET /health` : healthcheck utilisé par Docker pour la disponibilité du service
- `GET /metrics` : exposition des métriques au format Prometheus text/plain
- `GET /metrics/json` : métriques en JSON pour le dashboard HTML
- `GET /dashboard` : interface de monitoring temps réel

**Routes WebSocket :**
- `WS /ws/vehicle/{vehicle_id}` : connexion du simulateur véhicule
- `WS /ws/operator/{operator_id}?token={jwt}` : connexion opérateur avec authentification
- `WS /ws/dashboard` : connexion du dashboard (lecture seule)

La logique de relais est simple : les messages de télémétrie reçus du véhicule sont diffusés à tous les opérateurs et observateurs connectés ; les commandes reçues des opérateurs sont relayées vers le véhicule cible après vérification du token JWT.

### 5.3 Simulateur véhicule

Le simulateur véhicule reproduit le comportement d'un robotaxi en opération. Il maintient un état interne cohérent (vitesse, angle de braquage, pression de frein, GPS, batterie, statut) et l'envoie au backend toutes les 50 ms (20 Hz), reproduisant la fréquence de télémétrie d'un véhicule réel.

L'état du véhicule suit une machine à états à trois niveaux :
- **AUTONOMOUS** : état nominal, le véhicule opère de façon autonome
- **TELEOPERATED** : un opérateur a pris le contrôle et envoie des commandes
- **EMERGENCY** : aucune commande reçue depuis plus de 700 ms, le véhicule s'arrête de façon sécurisée

La transition vers EMERGENCY est le mécanisme de fail-safe central de notre architecture. Elle est déclenchée automatiquement par le simulateur, indépendamment de tout ordre du backend, ce qui garantit que même une compromission totale du backend ne peut pas maintenir le véhicule en mouvement indéfiniment.

**[INSÉRER ICI : Figure 7 — Logs backend montrant les transitions d'état autonomous → teleoperated → emergency]**

### 5.4 Authentification JWT

L'authentification des opérateurs repose sur JSON Web Tokens (JWT), standard RFC 7519. Chaque token contient les claims suivants :
- `sub` : identifiant de l'opérateur
- `iat` : heure d'émission
- `exp` : heure d'expiration (15 minutes après émission)

Les tokens sont signés avec l'algorithme HS256, utilisant une clé secrète de 32 caractères minimum stockée en variable d'environnement. La bibliothèque `python-jose[cryptography]` est utilisée pour la génération et la vérification.

Contrairement à certaines implémentations qui ne vérifient le token qu'à la connexion WebSocket initiale, notre backend vérifie le token **avant même d'accepter la connexion** : si le token est absent, invalide ou expiré, la connexion est rejetée immédiatement (code WebSocket 1008) et un événement de sécurité est émis vers le dashboard.

Le token est transmis en paramètre de l'URL WebSocket (`?token=...`), ce qui nécessite obligatoirement le chiffrement TLS pour éviter son exposition en clair dans les logs réseau.

### 5.5 Chiffrement TLS 1.3

Toutes les communications du système sont chiffrées avec TLS 1.3. Nous avons généré une infrastructure à clés publiques (PKI) minimaliste avec une CA privée auto-signée :

```
# Structure de la PKI :
CA privée     (ca.key + ca.crt)       → autorité racine
  └── Serveur (server.key + server.crt, CN=backend) → backend TLS
  └── Client  (client.key + client.crt)             → véhicule + opérateur
```

Le choix d'une CA auto-signée plutôt qu'une CA publique (Let's Encrypt, etc.) est justifié par le contexte : notre système est un démonstrateur en réseau privé Docker, sans nom de domaine public. En production, Stellantis disposerait d'une PKI d'entreprise avec des certificats émis par une autorité interne.

Le dashboard HTML détecte automatiquement le protocole utilisé et bascule entre `ws://` et `wss://` selon que la page est servie en HTTP ou HTTPS, évitant les erreurs de contenu mixte imposées par les navigateurs modernes.

**[INSÉRER ICI : capture page "Votre connexion n'est pas privée" et Wireshark TLS chiffré — page 5 du PDF captures]**

---

## 6. Mécanismes de sécurité déployés (Blue Team)

### 6.1 Protection contre le brute force : Rate Limiting

Le rate limiting est implémenté avec la bibliothèque `slowapi` (version 0.1.9), qui s'intègre nativement à FastAPI. La limite configurée est de **5 tentatives par minute par adresse IP** sur le point d'entrée `/auth/login`.

Le mécanisme fonctionne comme suit : après 5 tentatives échouées dans la fenêtre d'une minute, toute nouvelle tentative depuis la même IP reçoit une réponse HTTP 429 (Too Many Requests). Simultanément, un événement de sécurité de niveau "danger" est émis vers le dashboard de monitoring, permettant à un administrateur de détecter l'attaque en temps réel.

Ce choix de 5 tentatives par minute est délibérément conservateur. Un utilisateur légitime qui aurait oublié son mot de passe dispose de suffisamment d'essais pour corriger une faute de frappe, tandis qu'un attaquant par dictionnaire est bloqué dès la sixième tentative, limitant le débit d'attaque à un maximum de 5 × 60 = 300 mots de passe par heure, ce qui rend impraticable toute attaque par dictionnaire sérieuse.

**[INSÉRER ICI : Figure 2 et Figure 3 — Script DoS et dashboard avec alertes brute force]**

### 6.2 Authentification WebSocket et rejection explicite

La vérification du token JWT sur les connexions WebSocket est implémentée avec une subtilité technique importante : FastAPI ne peut pas retourner une réponse HTTP 401 ou 403 avant d'avoir accepté une connexion WebSocket (le protocole WebSocket impose un handshake HTTP d'abord). Notre implémentation :

1. Accepte la connexion WebSocket (`await websocket.accept()`)
2. Vérifie immédiatement le token
3. Si absent ou invalide : ferme la connexion avec le code 1008 (Policy Violation)
4. Émet un événement de sécurité visible sur le dashboard

Ce comportement est visible dans les captures : une tentative de connexion sans token génère immédiatement une alerte "Connexion refusée : aucun token fourni" sur le dashboard, prouvant que la protection est active et monitorée.

**[INSÉRER ICI : Figure 4 et Figure 5 — Refus connexion sans token + alerte dashboard]**

### 6.3 Fail-safe et résilience

Le module fail-safe est implémenté côté véhicule, ce qui est un choix architectural délibéré : même si le backend est compromis ou indisponible, le véhicule peut initier lui-même sa mise en sécurité.

Le timer est de **700 ms** : si aucune commande valide n'est reçue pendant cette durée, le véhicule passe automatiquement en état EMERGENCY et applique un arrêt progressif simulé. Ce seuil est cohérent avec les contraintes de sécurité de la téléopération telles que documentées dans les références [3] et [1].

En pratique, le simulateur opérateur envoie des commandes heartbeat toutes les 400 ms (soit bien en deçà du seuil de 700 ms) pour maintenir le véhicule en état TELEOPERATED. Si la connexion de l'opérateur est interrompue, le fail-safe se déclenche automatiquement après 700 ms, comme le montrent les logs backend.

### 6.4 Monitoring en temps réel : Dashboard de sécurité

Le dashboard de sécurité est accessible depuis `https://localhost:8000/dashboard`. Il affiche en temps réel :
- La télémétrie du véhicule (vitesse, GPS, batterie, statut)
- Les commandes en cours
- Les connexions actives (véhicule, opérateurs, dashboard)
- Un journal des événements de sécurité (authentifications, rejets, alertes)
- Les métriques Prometheus (voir section 8)

Tous ces éléments sont mis à jour sans rechargement de page via la connexion WebSocket dédiée `/ws/dashboard`.

**[INSÉRER ICI : Figure 1 — Dashboard principal]**

---

## 7. Simulation d'attaques et contre-mesures (Red Team)

### 7.1 Scénario 1 : Interception du trafic avant TLS (MITM simulé)

**Contexte de l'attaque**

Avant l'activation du chiffrement TLS, les communications WebSocket transitent en clair sur le réseau. Un attaquant positionné sur le chemin réseau (ou simplement sur le même réseau local, ce qui est le cas dans notre environnement Docker) peut capturer et analyser l'intégralité du trafic avec Wireshark.

**Démonstration**

Avec le filtre Wireshark `websocket`, les trames échangées entre le client et le serveur sont visibles en clair. En développant le payload d'une trame, on peut lire directement le JSON de télémétrie :

```json
{"type": "telemetry", "vehicle_id": "taxi_42", "speed": 0.0, 
 "steering_angle": 0.0, "brake_pressure": 0.0, "throttle": 0.0,
 "gps": {"lat": 48.8566, "lon": 2.3522}, "battery": 87.0, 
 "status": "autonomous", "timestamp": "2026-06-29T15:22.554464"}
```

Un attaquant peut donc connaître en temps réel la position exacte du véhicule, son état, et les commandes de l'opérateur. De plus, si un token JWT transite en clair dans l'URL WebSocket, il est directement visible et exploitable pour une attaque par replay.

**[INSÉRER ICI : Figure 8 — Capture Wireshark trafic JSON en clair]**

**Contre-mesure : TLS 1.3**

Après activation du chiffrement, le même filtre Wireshark ne montre plus que des paquets `TLSv1.2 Application Data` (le header TLS affiche 1.2 pour rétrocompatibilité mais la négociation effective est TLS 1.3). Le contenu est indéchiffrable. Le filtre `websocket` ne retourne plus aucun résultat, car les frames WebSocket sont désormais encapsulées dans des enveloppes TLS opaques.

**[INSÉRER ICI : Capture Wireshark TLS chiffré — page 5 du PDF captures]**

### 7.2 Scénario 2 : Attaque DoS par brute force

**Contexte de l'attaque**

Le script `attacks/dos_attack.py` simule un attaquant qui tente de deviner le mot de passe d'un opérateur en envoyant une série rapide de requêtes sur `/auth/login` avec des mots de passe issus d'un dictionnaire de 20 entrées communes.

**Déroulement de l'attaque**

```
[01] password='password'  → 401 Unauthorized (mauvais mot de passe)
[02] password='123456'    → 401 Unauthorized
[03] password='admin'     → 401 Unauthorized
[04] password='secret'    → 401 Unauthorized
[05] password='operator'  → 401 Unauthorized
[06] password='teleop'    → 🛡️ 429 Too Many Requests (BLOQUÉ par rate limiter)
[07] password='robotaxi'  → 429 Too Many Requests
...
[20] password='fleet'     → 429 Too Many Requests
```

Les 5 premières tentatives retournent HTTP 401 (identifiants invalides). À partir de la 6ème tentative, le rate limiter bloque toutes les requêtes depuis cette IP avec HTTP 429.

**Impact observable sur le dashboard**

Le dashboard affiche en temps réel les alertes générées par cette attaque :
- "❌ Échec login : operator_001 (mauvais credentials)" — pour chaque tentative échouée
- "🛡️ Brute force bloqué : 172.20.0.1 (5 per 1 minute)" — dès l'activation du rate limiter

**[INSÉRER ICI : Figure 2 (script) et Figure 3 (dashboard avec alertes)]**

**Résultats quantifiés**

| Métrique | Valeur |
|---|---|
| Tentatives total | 20 |
| Mauvais mot de passe (401) | 5 |
| Bloquées par rate limiter (429) | 15 |
| Temps pour bloquer l'attaque | < 1,5 seconde |
| Débit maximum autorisé | 5 req/min = 7 200 mots de passe/jour |

### 7.3 Scénario 3 : Attaque par rejeu (Replay Attack)

**Contexte de l'attaque**

Ce scénario illustre le risque concret d'un token JWT capturé par MITM (avant activation TLS) et réutilisé ultérieurement. L'attaquant n'a pas besoin du mot de passe : il lui suffit d'avoir capturé un token valide pendant la fenêtre d'écoute.

Le script `attacks/replay_attack.py` simule ce scénario en trois étapes :
1. Obtention d'un token via login légitime (simule la capture MITM)
2. Attente optionnelle (paramétrable via `WAIT_EXPIRY`)
3. Tentative de connexion avec le token "volé" et envoi de commandes malveillantes

**Démonstration — Phase 1 : Attaque réussie (token valide)**

Sans attendre l'expiration du token (JWT_EXPIRY_MINUTES=1 pour la démo) :

```bash
WAIT_EXPIRY=0 python3 replay_attack.py

[ÉTAPE 1] Récupération du token intercepté...
[+] Token obtenu : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[ÉTAPE 2] Utilisation immédiate du token intercepté
[ÉTAPE 3] Connexion WebSocket avec le token volé...
[+] CONNEXION ÉTABLIE — l'attaquant contrôle le véhicule !
[!] Accélération maximale (throttle=1.0)
[!] Virage brutal à droite (steering=90°)
[!] Désactivation des freins à pleine vitesse (brake=0.0)
[RÉSULTAT] ATTAQUE RÉUSSIE
```

**Démonstration — Phase 2 : Contre-mesure (token expiré)**

En attendant 70 secondes après l'obtention du token (avec JWT_EXPIRY_MINUTES=1, le token expire après 60 secondes) :

```bash
WAIT_EXPIRY=70 python3 replay_attack.py

[ÉTAPE 1] Récupération du token intercepté...
[+] Token obtenu : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[ÉTAPE 2] Simulation : l'attaquant attend 70s avant de rejouer le token...
          ⏳ 70s restantes...
          ⏳ 65s restantes...
          ...
[ÉTAPE 3] Connexion WebSocket avec le token expiré...
[RÉSULTAT] ATTAQUE ÉCHOUÉE → received 1008 (policy violation) then connection closed
           Le token a expiré — connexion refusée.
```

**[INSÉRER ICI : vidéo Démo replay_attack.mp4 ou captures de terminal]**
**[INSÉRER ICI : Figure 9 — docker-compose avec JWT_EXPIRY_MINUTES=1]**

**Enseignements de ce scénario**

Ce scénario démontre que la durée de vie des tokens JWT est un paramètre de sécurité critique. Une expiration longue (par exemple 24 heures, fréquente dans les applications web grand public) offrirait à un attaquant une fenêtre d'exploitation très large. Pour un système de téléopération, 15 minutes représente un bon équilibre entre sécurité (fenêtre d'exploitation limitée) et expérience utilisateur (l'opérateur peut maintenir une session active).

---

## 8. Observabilité et métriques de sécurité

### 8.1 Exposition Prometheus

Le backend expose ses métriques au format Prometheus text/plain sur l'endpoint `/metrics`. Ce format est le standard de facto pour la collecte de métriques dans les environnements cloud et conteneurisés. Il peut être scrapé directement par un serveur Prometheus qui stockerait les données en série temporelle pour une analyse historique.

Les métriques exposées sont :

```
# HELP teleop_auth_attempts_total Tentatives d'authentification
# TYPE teleop_auth_attempts_total counter
teleop_auth_attempts_total{result="success"} 3.0
teleop_auth_attempts_total{result="failure"} 5.0
teleop_auth_attempts_total{result="rate_limited"} 15.0

# HELP teleop_ws_connections_active Connexions WebSocket actives
# TYPE teleop_ws_connections_active gauge
teleop_ws_connections_active{type="vehicle"} 1.0
teleop_ws_connections_active{type="operator"} 1.0

# HELP teleop_commands_relayed_total Commandes relayées au véhicule
# TYPE teleop_commands_relayed_total counter
teleop_commands_relayed_total 247.0

# HELP teleop_telemetry_messages_total Messages de télémétrie reçus
# TYPE teleop_telemetry_messages_total counter
teleop_telemetry_messages_total 2253.0

# HELP teleop_security_events_total Événements de sécurité
# TYPE teleop_security_events_total counter
teleop_security_events_total{level="danger"} 6.0
teleop_security_events_total{level="success"} 3.0
```

Cette instrumentation est réalisée avec la bibliothèque Python `prometheus-client` (version 0.19.0), déjà incluse dans les dépendances du backend. Chaque compteur est incrémenté au bon moment dans le code : le compteur `auth_attempts_total{result="rate_limited"}` est incrémenté dans le handler du rate limiter, `commands_relayed_total` l'est dans la méthode de relais vers le véhicule, etc.

### 8.2 Dashboard de métriques intégré

En complément du format Prometheus brut, le dashboard HTML affiche un panneau de métriques actualisé toutes les 5 secondes via un appel à `/metrics/json`. Ce panneau présente 8 compteurs clés :

| Compteur | Signification sécurité |
|---|---|
| Auth réussies | Nombre de sessions légitimes ouvertes |
| Auth échouées | Indicateur de tentatives de brute force |
| Rate limited (429) | Quantification des attaques bloquées |
| Commandes relayées | Volume de trafic de contrôle |
| Télémétrie reçue | Santé du canal véhicule → backend |
| Véhicules connectés | État de la flotte en temps réel |
| Opérateurs connectés | Nombre de sessions actives |
| Alertes danger | Cumul des événements de sécurité critiques |

**[INSÉRER ICI : Figure 10 — Dashboard avec panneau métriques Prometheus]**

### 8.3 Apport de l'observabilité pour la cybersécurité

L'instrumentation Prometheus illustre un principe essentiel de la sécurité opérationnelle : **ce qu'on ne mesure pas, on ne peut pas le détecter ni le corriger**. Dans notre système, les métriques permettent de détecter en temps réel une attaque DoS (pic sur `auth_rate_limited`), une tentative de connexion non autorisée (pic sur `security_events{level="danger"}`), ou une dégradation du canal de télémétrie (chute de `telemetry_messages_total`).

En production, ces métriques seraient consommées par un serveur Prometheus qui les stockerait en série temporelle, permettant l'analyse historique et la corrélation d'événements. Un Alert Manager pourrait déclencher des notifications automatiques dès que certains seuils sont franchis (par exemple, plus de 10 alertes danger en 5 minutes).

---

## 9. Discussion et analyse critique

### 9.1 Ce que nous avons réalisé

Notre prototype couvre les dimensions suivantes demandées par le sujet [1] :

- **Sécurisation du canal de communication** : TLS 1.3 sur tous les flux, JWT avec expiration courte, rejet explicite des connexions non authentifiées. Démontré par comparaison Wireshark avant/après TLS.
- **Simulation du système** : trois composants Docker (véhicule, backend, opérateur) communiquant en temps réel, avec télémétrie à 20 Hz et machine d'état cohérente.
- **Attaques et contre-mesures** : deux scénarios d'attaque réalistes démontrés (DoS/brute force et replay), avec contre-mesures actives et visualisation en temps réel.
- **Détection des anomalies (partiel)** : le dashboard détecte et affiche les connexions non autorisées et les tentatives de brute force. Une détection comportementale sémantique (commandes incohérentes) n'a pas été implémentée dans le temps imparti.
- **Résilience et fail-safe** : mécanisme automatique de passage en mode EMERGENCY après 700 ms sans commande.
- **Métriques et observabilité** : endpoint Prometheus standardisé + dashboard live.

### 9.2 Ce qui aurait nécessité plus de temps

**Détection d'anomalie comportementale** : le sujet [1] invite à aller au-delà de la sécurité du canal pour vérifier la cohérence sémantique des commandes (vitesse excessive, braquage impossible, contradictions accélération/frein). C'est le point le plus avancé du sujet, qui se rapproche de l'IA appliquée à la sécurité.

**WebRTC pour le flux vidéo** : notre prototype simule le flux vidéo via la télémétrie texte. L'implémentation réelle d'un flux WebRTC (DTLS + SRTP) aurait requis une infrastructure plus conséquente (TURN/STUN servers, encodage vidéo).

**Netem pour les attaques de latence** : le sujet prévoit l'injection de latence réseau avec `tc netem` pour simuler une dégradation de QoS. Cette attaque est documentée dans notre architecture mais n'a pas été démontrée en live.

**PKI d'entreprise** : notre CA auto-signée est suffisante pour le prototype mais ne simule pas une vraie PKI d'entreprise avec révocation (OCSP), certificats clients distincts par opérateur, et politique de renouvellement.

### 9.3 Comparaison avec des industries comparables

Le sujet [1] encourage la comparaison avec des industries similaires. On peut noter que les systèmes de téléopération militaire (UAVs, drones de combat) ont résolu certains de ces problèmes avec des décennies d'avance. Le protocole MAVLink, utilisé par de nombreux drones civils, utilise par exemple des signatures HMAC sur chaque message de commande, un mécanisme similaire à notre JWT mais appliqué au niveau de chaque paquet. Les systèmes de télémédecine robotisée (chirurgie à distance Da Vinci) utilisent des liens dédiés chiffrés de bout en bout avec des SLA de latence garantis par contrat avec les opérateurs télécom — une approche qui n'est pas transposable à la téléopération de masse de robotaxis, mais dont les principes inspirent les exigences de qualité de service.

---

## 10. Conclusion et perspectives

Ce projet nous a permis d'explorer de façon concrète et reproductible les enjeux de cybersécurité d'un système de téléopération de robotaxi. Partant d'une architecture Zero Trust formalisée et d'une analyse de risques structurée (CJA, STRIDE, TARA, MORDA), nous avons implémenté un prototype fonctionnel qui démontre l'applicabilité de mécanismes de sécurité standards dans un contexte temps réel exigeant.

Les trois attaques simulées — interception avant TLS, brute force sur l'authentification, et replay de token JWT — illustrent des menaces réelles et documentées dans la littérature [2]. Leurs contre-mesures respectives (TLS 1.3, rate limiting, expiration JWT) sont proportionnées, implémentées et démontrées fonctionnellement.

Au-delà du prototype, ce travail soulève plusieurs questions ouvertes pour des développements futurs :

**Comment détecter un opérateur malveillant légitime ?** Un opérateur authentifié qui enverrait des commandes dangereuses (accélération soudaine dans une zone piétonne, par exemple) ne peut être détecté ni par le chiffrement ni par l'authentification. La réponse réside dans la vérification sémantique des commandes par rapport à l'état du véhicule et à la représentation de la scène, un problème qui touche à l'intelligence artificielle appliquée à la sécurité.

**Comment garantir la disponibilité en cas d'attaque distribuée ?** Notre rate limiter est efficace contre un seul attaquant. Une attaque DDoS distribuée depuis des milliers d'IPs différentes nécessiterait une infrastructure de mitigation en amont (CDN, WAF, scrubbing center) que notre prototype ne simule pas.

**Quelle conformité réglementaire ?** En vue d'un déploiement réel chez Stellantis, le système devrait être évalué au regard d'ISO 21434 [6] et du règlement UNECE R155 [7], qui imposent notamment une TARA formelle auditée, une gestion du cycle de vie cybersécurité, et un processus de réponse aux incidents documenté.

Ce projet représente une première brique d'un système qui, pour être déployé en production, requerra des années de travail supplémentaire — mais une brique qui démontre la faisabilité technique et la pertinence des approches choisies.

---

## 11. Références bibliographiques

[1] Stellantis / Télécom Paris. *Projet Fil Rouge : Cybersecurity of Teleoperation System for Robotaxi*. Document de sujet, MS Expert Cybersécurité, Télécom Paris, 2025-2026.

[2] Stellantis (annexe). *Tele-driving cyber security risk assessment*. Document de référence fourni dans le cadre du Fil Rouge.

[3] (Annexe sujet). *A survey on remote operation of road vehicles*. Document de référence fourni dans le cadre du Fil Rouge.

[4] 5GOR Whitepaper. *Autonomous vehicles teleoperation*. Document de référence fourni dans le cadre du Fil Rouge.

[5] Rose, S., Borchert, O., Mitchell, S., Connelly, S. *Zero Trust Architecture*. NIST Special Publication 800-207. National Institute of Standards and Technology, 2020. Disponible sur : https://doi.org/10.6028/NIST.SP.800-207

[6] ISO/SAE. *ISO/SAE 21434:2021 — Road vehicles — Cybersecurity engineering*. International Organization for Standardization, 2021.

[7] UNECE. *Regulation No 155 — Uniform provisions concerning the approval of vehicles with regards to cyber security and cyber security management system*. United Nations Economic Commission for Europe, 2021.

[8] Microsoft. *The STRIDE Threat Model*. Microsoft Security Development Lifecycle documentation. Disponible sur : https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats

[9] MITRE. *Crown Jewels Analysis*. MITRE Systems Engineering Guide. Disponible dans : MITRE Systems Engineering Guide Book, pp. 167-200. https://www.mitre.org/sites/default/files/publications/se-guide-book-interactive.pdf

[10] MITRE. *Mission-Oriented Risk and Design Analysis of Critical Information Systems (MORDA)*. MITRE Technical Report.

[11] Tiangolo, S. *FastAPI framework documentation*. Disponible sur : https://fastapi.tiangolo.com

[12] python-jose contributors. *Python JOSE — JSON Object Signing and Encryption library*. Version 3.3.0. Disponible sur : https://python-jose.readthedocs.io

[13] Prometheus Authors. *prometheus-client — Prometheus instrumentation library for Python*. Version 0.19.0. Disponible sur : https://github.com/prometheus/client_python

[14] Laurent Senta. *slowapi — A rate limiter for Starlette and FastAPI*. Version 0.1.9. Disponible sur : https://github.com/laurents/slowapi

---

## Annexes

### Annexe A : Commandes de reproduction du système

```bash
# Prérequis : Docker Desktop installé

# 1. Cloner le dépôt
git clone [URL du dépôt]
cd teleop-cybersec

# 2. Démarrer le système complet
docker compose up --build

# 3. Accéder au dashboard
# Ouvrir https://localhost:8000/dashboard dans un navigateur
# (Accepter l'avertissement certificat auto-signé)

# 4. Voir les métriques Prometheus
# Ouvrir https://localhost:8000/metrics

# 5. Simuler une attaque DoS (depuis WSL ou Linux)
cd attacks
python3 -m venv venv && source venv/bin/activate
pip install aiohttp websockets
python3 dos_attack.py

# 6. Simuler une attaque replay (token valide)
WAIT_EXPIRY=0 python3 replay_attack.py

# 7. Simuler une attaque replay (token expiré, nécessite JWT_EXPIRY_MINUTES=1)
# Dans docker-compose.yml : JWT_EXPIRY_MINUTES=1, puis relancer
docker compose up --build
WAIT_EXPIRY=70 python3 replay_attack.py
```

### Annexe B : Variables d'environnement

| Variable | Valeur démo | Description |
|---|---|---|
| JWT_SECRET | change_me_in_prod_use_32_char_minimum | Clé de signature JWT |
| JWT_ALGORITHM | HS256 | Algorithme de signature |
| JWT_EXPIRY_MINUTES | 15 (1 pour démo replay) | Durée de vie des tokens |
| BACKEND_URL | wss://backend:8000 | URL WebSocket du backend |
| LATENCY_FAILSAFE_MS | 700 | Seuil fail-safe en millisecondes |
| CA_CERT_PATH | /certs/ca.crt | Chemin du certificat CA |

### Annexe C : Stack technique

| Composant | Technologie | Version |
|---|---|---|
| Backend API | FastAPI | 0.110.0 |
| Runtime async | Uvicorn | 0.27.0 |
| Authentification | python-jose | 3.3.0 |
| Rate limiting | slowapi | 0.1.9 |
| Métriques | prometheus-client | 0.19.0 |
| WebSocket | websockets | 12.0 |
| Containerisation | Docker Compose | 2.x |
| Chiffrement | OpenSSL / TLS 1.3 | - |
| Attaques | aiohttp | 3.9.1 |
