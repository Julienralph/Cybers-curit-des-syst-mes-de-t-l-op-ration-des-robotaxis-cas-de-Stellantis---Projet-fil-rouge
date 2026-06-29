import pandas as pd

def check_command(cmd):
    reasons = []

    # Règle 1 : accélération avec obstacle proche
    if cmd["obstacle_dist_m"] < 5 and cmd["commanded_accel"] > 0:
        reasons.append("Obstacle trop proche avec accélération")
        return "DISENGAGE", reasons

    # Règle 2 : virage brutal à haute vitesse
    if cmd["speed_kmh"] > 70 and abs(cmd["steering_angle"]) > 30:
        reasons.append("Virage brutal à haute vitesse")
        return "DISENGAGE", reasons

    # Règle 3 : fréquence de commandes anormale (attaquant automatisé)
    if cmd["cmd_freq_per_sec"] > 15:
        reasons.append("Fréquence de commandes suspecte")
        return "LIMIT", reasons

    # Règle 4 : réaction trop rapide pour un humain
    if cmd["operator_reaction_ms"] < 100:
        reasons.append("Temps de réaction non humain")
        return "LIMIT", reasons

    return "ACCEPT", []


# --- Appliquer sur tout le dataset ---
df = pd.read_csv("commands_dataset.csv")

results = df.apply(lambda row: check_command(row), axis=1)
df["decision"] = results.apply(lambda x: x[0])
df["reason"]   = results.apply(lambda x: ", ".join(x[1]) if x[1] else "")

# --- Stats ---
print("=== Résultats ===")
print(df["decision"].value_counts())
print()

# --- Précision vs labels réels ---
df["correct"] = (
    ((df["decision"] != "ACCEPT") & (df["label"] == "anomaly")) |
    ((df["decision"] == "ACCEPT") & (df["label"] == "normal"))
)
accuracy = df["correct"].mean() * 100
print(f"Précision vs labels réels : {accuracy:.1f}%")

# --- Sauvegarde ---
df.to_csv("commands_heuristics_results.csv", index=False)
print("\nRésultats sauvegardés dans commands_heuristics_results.csv")