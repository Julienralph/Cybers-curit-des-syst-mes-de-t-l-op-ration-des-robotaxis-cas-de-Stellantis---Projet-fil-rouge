import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

# --- Chargement des données ---
df = pd.read_csv("commands_dataset.csv")

# Features utilisées par le modèle
features = [
    "speed_kmh",
    "commanded_accel",
    "steering_angle",
    "obstacle_dist_m",
    "cmd_freq_per_sec",
    "operator_reaction_ms"
]

X = df[features]
y_true = df["label"].apply(lambda x: 1 if x == "anomaly" else 0)

# --- Entraînement ---
# contamination = proportion d'anomalies estimée dans les données
model = IsolationForest(contamination=0.35, random_state=42)
model.fit(X)

# --- Prédiction ---
# Isolation Forest retourne : -1 (anomalie) ou 1 (normal)
raw_preds = model.predict(X)
y_pred = [1 if p == -1 else 0 for p in raw_preds]

# --- Résultats ---
print("=== Matrice de confusion ===")
print(confusion_matrix(y_true, y_pred))
print()
print("=== Rapport de classification ===")
print(classification_report(y_true, y_pred, target_names=["normal", "anomaly"]))

# --- Sauvegarde ---
df["ml_prediction"] = ["anomaly" if p == 1 else "normal" for p in y_pred]
df.to_csv("commands_ml_results.csv", index=False)
print("Résultats sauvegardés dans commands_ml_results.csv")