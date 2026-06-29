import pandas as pd
import numpy as np
import random

np.random.seed(42)
records = []

# --- NORMAL commands (500 samples) ---
for _ in range(500):
    speed = np.random.uniform(0, 80)
    records.append({
        "speed_kmh":        round(speed, 1),
        "commanded_accel":  round(np.random.uniform(-1.0, 1.0), 2),
        "steering_angle":   round(np.random.uniform(-20, 20), 1),
        "obstacle_dist_m":  round(np.random.uniform(15, 100), 1),
        "cmd_freq_per_sec": round(np.random.uniform(1, 8), 1),
        "operator_reaction_ms": round(np.random.uniform(200, 800), 0),
        "label": "normal"
    })

# --- ANOMALY 1: accelerate with obstacle very close (150 samples) ---
for _ in range(150):
    records.append({
        "speed_kmh":        round(np.random.uniform(20, 80), 1),
        "commanded_accel":  round(np.random.uniform(0.5, 2.0), 2),   # accelerating
        "steering_angle":   round(np.random.uniform(-10, 10), 1),
        "obstacle_dist_m":  round(np.random.uniform(0.5, 4.9), 1),   # obstacle very close!
        "cmd_freq_per_sec": round(np.random.uniform(1, 8), 1),
        "operator_reaction_ms": round(np.random.uniform(200, 800), 0),
        "label": "anomaly"
    })

# --- ANOMALY 2: brutal steering at high speed (100 samples) ---
for _ in range(100):
    records.append({
        "speed_kmh":        round(np.random.uniform(70, 130), 1),    # high speed
        "commanded_accel":  round(np.random.uniform(-0.5, 0.5), 2),
        "steering_angle":   round(np.random.uniform(35, 90), 1) * random.choice([-1, 1]),  # brutal turn
        "obstacle_dist_m":  round(np.random.uniform(15, 100), 1),
        "cmd_freq_per_sec": round(np.random.uniform(1, 8), 1),
        "operator_reaction_ms": round(np.random.uniform(200, 800), 0),
        "label": "anomaly"
    })

# --- ANOMALY 3: abnormally high command frequency (100 samples) ---
# Could indicate a compromised/automated attacker flooding commands
for _ in range(100):
    records.append({
        "speed_kmh":        round(np.random.uniform(0, 80), 1),
        "commanded_accel":  round(np.random.uniform(-1.0, 1.0), 2),
        "steering_angle":   round(np.random.uniform(-20, 20), 1),
        "obstacle_dist_m":  round(np.random.uniform(15, 100), 1),
        "cmd_freq_per_sec": round(np.random.uniform(20, 50), 1),     # way too fast = suspect
        "operator_reaction_ms": round(np.random.uniform(10, 50), 0), # too fast for a human
        "label": "anomaly"
    })

# --- Freinage d'urgence légitime (50 samples) ---
for _ in range(50):
    records.append({
        "speed_kmh":        round(np.random.uniform(70, 130), 1),
        "commanded_accel":  round(np.random.uniform(-2.0, -1.5), 2),  # freinage brutal
        "steering_angle":   round(np.random.uniform(-5, 5), 1),        # tout droit
        "obstacle_dist_m":  round(np.random.uniform(5, 15), 1),        # obstacle proche
        "cmd_freq_per_sec": round(np.random.uniform(1, 8), 1),
        "operator_reaction_ms": round(np.random.uniform(200, 800), 0),
        "label": "normal"
    })
    
df = pd.DataFrame(records)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
df.to_csv("commands_dataset.csv", index=False)

print(f"Dataset generated: {len(df)} rows")
print(df["label"].value_counts())
print("\nSample:")
print(df.head(10).to_string())