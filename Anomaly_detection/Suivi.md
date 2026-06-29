## Suivi du Projet — Détection d'Anomalies

---

### Étape 1 — Génération des données

Quoi : On a créé un dataset de 850 commandes de conduite simulées (`commands_dataset.csv`).

Pourquoi : On n'a pas de vrai robotaxi, donc on simule des données réalistes. Chaque ligne représente une commande envoyée par un opérateur au véhicule, avec 6 caractéristiques :
- `speed_kmh` — vitesse actuelle du véhicule
- `commanded_accel` — accélération demandée par l'opérateur
- `steering_angle` — angle de direction demandé
- `obstacle_dist_m` — distance à l'obstacle devant
- `cmd_freq_per_sec` — fréquence des commandes envoyées
- `operator_reaction_ms` — temps de réaction de l'opérateur

Composition du dataset :
- 500 commandes normales
- 150 anomalies type 1 : accélération avec obstacle < 5m
- 100 anomalies type 2 : virage brutal à haute vitesse (>70 km/h)
- 100 anomalies type 3 : fréquence de commandes trop élevée (attaquant automatisé)

---

### Étape 2 — Règles heuristiques

Quoi : On a codé 4 règles logiques qui analysent chaque commande et rendent un verdict : ACCEPT / LIMIT / DISENGAGE.

Pourquoi : Avant de faire du ML, on pose une baseline simple et explicable. C'est important pour deux raisons : ça fonctionne sans entraînement, et chaque décision est justifiable ("la commande a été bloquée parce que l'obstacle était à 3m").

Les 4 règles :
1. Obstacle < 5m + accélération → DISENGAGE
2. Vitesse > 70 km/h + angle > 30° → DISENGAGE
3. Fréquence > 15 commandes/sec → LIMIT (comportement non humain)
4. Temps de réaction < 100ms → LIMIT (trop rapide pour un humain)

Résultats obtenus :
- 500 ACCEPT, 250 DISENGAGE, 100 LIMIT
- Précision : 100%

Comment interpréter ces résultats : La précision de 100% est normale et attendue — on a construit les règles en connaissant les données. Ce n'est pas du "overfitting", c'est voulu : les heuristiques servent de référence. L'intérêt du ML à l'étape suivante sera de détecter des anomalies que les règles ne couvrent pas, des cas ambigus ou nouveaux.


### Étape 3 — Modèle ML : Isolation Forests

Quoi : On a entraîné un modèle de machine learning (Isolation Forest) pour détecter les anomalies automatiquement, sans règles codées à la main.

Pourquoi : Les heuristiques ne détectent que les cas qu'on a prévus explicitement. Le ML lui apprend seul ce qu'est une commande "normale" et signale tout ce qui s'en écarte — y compris des cas nouveaux ou subtils qu'on n'aurait pas anticipés.

Comment ça marche : L'algorithme lit les 850 commandes et mesure à quel point chaque commande est "isolée" par rapport aux autres. Une commande isolée = anormale. Il ne connaît aucune règle — il les découvre seul.

Résultats obtenus :
- 439 normales bien détectées
- 237 anomalies bien détectées
- 61 faux positifs (commandes normales bloquées à tort)
- 113 faux négatifs (anomalies non détectées)
- Précision globale : 80%

Comment interpréter ces résultats : 80% sans aucune règle explicite, c'est une bonne performance pour un modèle non supervisé. Les 113 faux négatifs sont le point faible — dans un système réel c'est dangereux. C'est pourquoi on ne remplace pas les heuristiques par le ML, on les combine : les heuristiques gèrent les cas évidents, le ML gère les cas subtils et nouveaux.


#### Etape 4 

### Étape 4 — API FastAPI

Quoi : On a transformé notre système de détection en une vraie API accessible via HTTP, tournant sur notre PC.

Pourquoi : Sans API, le détecteur d'anomalies tourne en isolation — c'est juste un script Python. Avec l'API, il devient un composant connecté que ton collègue peut appeler en temps réel depuis sa démo.

Comment ça marche : Le serveur Uvicorn fait tourner l'API sur `http://127.0.0.1:8000`. Quand une commande arrive sur `/check_command`, le système applique d'abord les heuristiques, puis le ML si les heuristiques n'ont rien détecté, et retourne une décision.

Problème rencontré et résolu : Le ML classait le freinage d'urgence légitime comme une anomalie — un faux positif dangereux. On a d'abord corrigé le dataset en ajoutant 50 scénarios de freinage d'urgence normal, mais ça n'a pas suffi car le ML confond "rare" avec "anormal". On a donc ajouté une règle heuristique explicite pour couvrir ce cas.

Résultats obtenus :

| Scénario | Décision | Source |
|---|---|---|
| Conduite normale | ACCEPT | ML |
| Accélération avec obstacle à 3m | DISENGAGE | Heuristique |
| Attaquant automatisé (30 cmd/sec) | LIMIT | Heuristique |
| Freinage d'urgence à 100 km/h | ACCEPT | Heuristique |

Leçon clé :

Leçon clé : Le ML ne remplace pas les heuristiques — les deux sont complémentaires. Les heuristiques apportent le bon sens que le ML ne peut pas déduire seul depuis les données.

Notes perso : 
-1.le Transfer Learning comme une perspective d'amélioration
-2."solation Forest a du mal avec ce cas car un freinage brutal à haute vitesse ressemble statistiquement à une anomalie même avec le nouveau dataset." --- donc le modèle estime que un événement exceptionnel (ex: arrêt d'urgence) dans le monde réel est une anomalie ? --- "Exactement. C'est une limite fondamentale du ML :

Le modèle confond "rare" avec "anormal".

Un freinage d'urgence est rare dans les données — ça n'arrive pas souvent — donc le modèle l'interprète comme une anomalie. Mais dans la réalité, rare ne veut pas dire dangereux, ça peut même être le contraire — c'est la bonne réaction face à un danger.
C'est pourquoi les heuristiques sont indispensables — elles apportent du bon sens que le ML ne peut pas déduire seul depuis les données."


### Étape 5 — Simulation d'attaques

Quoi : On a créé un script `attack_simulation.py` qui simule 4 scénarios d'attaque 
en envoyant des commandes malveillantes à l'API.

Pourquoi : Valider que le système détecte correctement les attaques réelles et 
démontrer concrètement la valeur ajoutée du système lors de la démo finale.

Les 4 scénarios testés :

| Scénario | Décision | Source |
|---|---|---|
| Accélération forcée avec obstacle à 3m | DISENGAGE | Heuristique |
| Flood de commandes (attaquant automatisé) | LIMIT | Heuristique |
| Virage brutal à 110 km/h | DISENGAGE | Heuristique |
| Anomalie subtile (combinaison de facteurs) | LIMIT | ML |

Leçon clé : Le 4ème scénario est le plus important — aucune règle heuristique 
n'est individuellement violée, mais la combinaison de vitesse élevée + forte 
accélération + obstacle à 8m + fréquence limite a alerté le ML. C'est exactement 
la valeur ajoutée du ML : détecter ce que les règles ne couvrent pas.

ok mais en gros il cherche pas à comprendre ce qui se passe. Juste si il voit que il y a quelque chose qui est anormale par rapport aux autres données (par exemple ici la combinaison normales des données d'entrainements).