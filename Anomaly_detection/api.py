import pickle
import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest

app = FastAPI()

# --- Charger et réentraîner le modèle au démarrage ---
df = pd.read_csv("commands_dataset.csv")
features = [
    "speed_kmh",
    "commanded_accel",
    "steering_angle",
    "obstacle_dist_m",
    "cmd_freq_per_sec",
    "operator_reaction_ms"
]
X = df[features]
model = IsolationForest(contamination=0.25, random_state=42)
model.fit(X)

# --- Schéma d'une commande ---
class Command(BaseModel):
    speed_kmh: float
    commanded_accel: float
    steering_angle: float
    obstacle_dist_m: float
    cmd_freq_per_sec: float
    operator_reaction_ms: float

# --- Règles heuristiques ---
def check_heuristics(cmd):
    # Freinage d'urgence légitime = toujours ACCEPT
    if cmd.commanded_accel < -1.5 and cmd.obstacle_dist_m < 20:
        return "ACCEPT", "Freinage d'urgence légitime"
    # Règle 1 : accélération avec obstacle proche
    if cmd.obstacle_dist_m < 5 and cmd.commanded_accel > 0:
        return "DISENGAGE", "Obstacle trop proche avec accélération"
    if cmd.obstacle_dist_m < 5 and cmd.commanded_accel > 0:
        return "DISENGAGE", "Obstacle trop proche avec accélération"
    if cmd.speed_kmh > 70 and abs(cmd.steering_angle) > 30:
        return "DISENGAGE", "Virage brutal à haute vitesse"
    if cmd.cmd_freq_per_sec > 15:
        return "LIMIT", "Fréquence de commandes suspecte"
    if cmd.operator_reaction_ms < 100:
        return "LIMIT", "Temps de réaction non humain"
    return None, None

# --- Endpoint principal ---
@app.post("/check_command")
def check_command(cmd: Command):
    # 1. Heuristiques en premier
    decision, reason = check_heuristics(cmd)
    if decision:
        return {
            "decision": decision,
            "reason": reason,
            "source": "heuristic"
        }

    # 2. ML si les heuristiques n'ont rien détecté
    X_input = pd.DataFrame([cmd.dict()])
    prediction = model.predict(X_input)[0]
    if prediction == -1:
        return {
            "decision": "LIMIT",
            "reason": "Anomalie détectée par le modèle ML",
            "source": "ml"
        }

    return {
        "decision": "ACCEPT",
        "reason": "Commande normale",
        "source": "ml"
    }

# --- Endpoint de santé ---
@app.get("/health")
def health():
    return {"status": "ok"}