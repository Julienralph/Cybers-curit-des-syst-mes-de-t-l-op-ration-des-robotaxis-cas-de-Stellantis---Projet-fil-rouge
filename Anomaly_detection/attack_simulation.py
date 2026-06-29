import requests
import json

URL = "http://127.0.0.1:8000/check_command"

def send_command(scenario_name, payload):
    response = requests.post(URL, json=payload)
    result = response.json()
    print(f"\n{'='*50}")
    print(f"Scénario : {scenario_name}")
    print(f"Commande : {json.dumps(payload, indent=2)}")
    print(f"Décision : {result['decision']} ({result['source']})")
    print(f"Raison   : {result['reason']}")

# --- Attaque 1 : Injection de commande (accélération forcée) ---
send_command("Injection de commande - Accélération forcée", {
    "speed_kmh": 60,
    "commanded_accel": 2.0,
    "steering_angle": 0,
    "obstacle_dist_m": 3,
    "cmd_freq_per_sec": 5,
    "operator_reaction_ms": 300
})

# --- Attaque 2 : Opérateur compromis (flood de commandes) ---
send_command("Opérateur compromis - Flood de commandes", {
    "speed_kmh": 50,
    "commanded_accel": 0.5,
    "steering_angle": 10,
    "obstacle_dist_m": 25,
    "cmd_freq_per_sec": 35,
    "operator_reaction_ms": 15
})

# --- Attaque 3 : Virage brutal à haute vitesse ---
send_command("Virage brutal - Tentative de sortie de route", {
    "speed_kmh": 110,
    "commanded_accel": 0.5,
    "steering_angle": 60,
    "obstacle_dist_m": 30,
    "cmd_freq_per_sec": 5,
    "operator_reaction_ms": 300
})

# --- Attaque 4 : Commande subtile (détectable uniquement par ML) ---
send_command("Anomalie subtile - Détectable uniquement par ML", {
    "speed_kmh": 95,
    "commanded_accel": 1.8,
    "steering_angle": 25,
    "obstacle_dist_m": 8,
    "cmd_freq_per_sec": 12,
    "operator_reaction_ms": 150
})