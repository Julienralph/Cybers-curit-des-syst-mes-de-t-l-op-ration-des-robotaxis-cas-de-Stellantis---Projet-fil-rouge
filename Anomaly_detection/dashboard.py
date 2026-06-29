import requests
import time
import os

URL = "http://127.0.0.1:8000/check_command"

SCENARIOS = [
    ("Conduite normale", {
        "speed_kmh": 50, "commanded_accel": 0.5,
        "steering_angle": 10, "obstacle_dist_m": 30,
        "cmd_freq_per_sec": 3, "operator_reaction_ms": 400
    }),
    ("Conduite normale", {
        "speed_kmh": 40, "commanded_accel": 0.3,
        "steering_angle": -5, "obstacle_dist_m": 50,
        "cmd_freq_per_sec": 2, "operator_reaction_ms": 500
    }),
    ("Conduite normale", {
        "speed_kmh": 60, "commanded_accel": 0.2,
        "steering_angle": 5, "obstacle_dist_m": 40,
        "cmd_freq_per_sec": 3, "operator_reaction_ms": 450
    }),
    ("⚠️  ATTAQUE : Accélération forcée", {
        "speed_kmh": 60, "commanded_accel": 2.0,
        "steering_angle": 0, "obstacle_dist_m": 3,
        "cmd_freq_per_sec": 5, "operator_reaction_ms": 300
    }),
    ("Conduite normale", {
        "speed_kmh": 55, "commanded_accel": 0.4,
        "steering_angle": 8, "obstacle_dist_m": 35,
        "cmd_freq_per_sec": 3, "operator_reaction_ms": 420
    }),
    ("⚠️  ATTAQUE : Flood de commandes", {
        "speed_kmh": 50, "commanded_accel": 0.5,
        "steering_angle": 10, "obstacle_dist_m": 25,
        "cmd_freq_per_sec": 35, "operator_reaction_ms": 15
    }),
    ("⚠️  ATTAQUE : Virage brutal", {
        "speed_kmh": 110, "commanded_accel": 0.5,
        "steering_angle": 60, "obstacle_dist_m": 30,
        "cmd_freq_per_sec": 5, "operator_reaction_ms": 300
    }),
    ("Freinage d'urgence légitime", {
        "speed_kmh": 100, "commanded_accel": -2.0,
        "steering_angle": 0, "obstacle_dist_m": 10,
        "cmd_freq_per_sec": 5, "operator_reaction_ms": 300
    }),
    ("⚠️  ATTAQUE : Anomalie subtile", {
        "speed_kmh": 95, "commanded_accel": 1.8,
        "steering_angle": 25, "obstacle_dist_m": 8,
        "cmd_freq_per_sec": 12, "operator_reaction_ms": 150
    }),
]

COLORS = {
    "ACCEPT":    "\033[92m",  # vert
    "LIMIT":     "\033[93m",  # jaune
    "DISENGAGE": "\033[91m",  # rouge
}
RESET = "\033[0m"

os.system("cls")
print("=" * 60)
print("   SYSTÈME DE DÉTECTION D'ANOMALIES — ROBOTAXI TÉLÉOPÉRATION")
print("=" * 60)

for scenario_name, payload in SCENARIOS:
    time.sleep(1.5)
    response = requests.post(URL, json=payload)
    result = response.json()

    decision = result["decision"]
    color = COLORS.get(decision, "")

    print(f"\n{'─'*60}")
    print(f"Scénario   : {scenario_name}")
    print(f"Vitesse    : {payload['speed_kmh']} km/h | "
          f"Accel : {payload['commanded_accel']} | "
          f"Obstacle : {payload['obstacle_dist_m']}m")
    print(f"Décision   : {color}{decision}{RESET} ({result['source']})")
    print(f"Raison     : {result['reason']}")

print(f"\n{'='*60}")
print("FIN DE LA DÉMONSTRATION")
print("="*60)