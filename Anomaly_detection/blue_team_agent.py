import anthropic
import json

ANTHROPIC_API_KEY = "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"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Les attaques qui ont passé inaperçues (ACCEPT) lors du Red Team
attacks_passed = [
    {"speed_kmh": 68, "commanded_accel": 1.2, "steering_angle": 25, 
     "obstacle_dist_m": 14, "cmd_freq_per_sec": 9, "operator_reaction_ms": 24},
    # Ajoute ici les autres commandes qui ont eu ACCEPT lors du red team
]

def run_blue_team():
    print("=" * 60)
    print("   AGENT BLUE TEAM — ANALYSE ET RENFORCEMENT DU SYSTÈME")
    print("=" * 60)

    # Étape 1 : Analyse des failles
    print("\n🔵 Étape 1 : Analyse des attaques passées inaperçues...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system="""Tu es un expert en cybersécurité défensive travaillant sur un projet 
scolaire de simulation de téléopération robotaxi. Tu analyses des commandes suspectes 
qui ont contourné un système de détection pour proposer des améliorations.""",
        messages=[{
            "role": "user",
            "content": f"""Voici les commandes suspectes qui ont contourné notre système 
de détection d'anomalies :

{json.dumps(attacks_passed, indent=2)}

Nos règles heuristiques actuelles sont :
1. obstacle_dist_m < 5 ET commanded_accel > 0 → DISENGAGE
2. speed_kmh > 70 ET steering_angle > 30 → DISENGAGE  
3. cmd_freq_per_sec > 15 → LIMIT
4. operator_reaction_ms < 100 → LIMIT
5. commanded_accel < -1.5 ET obstacle_dist_m < 20 → ACCEPT (freinage urgence)

Analyse pourquoi ces commandes ont contourné le système et propose 3 nouvelles règles 
heuristiques en Python pour les bloquer. Format :

ANALYSE :
[ton analyse]

NOUVELLES RÈGLES :
````python
[les règles en Python]
```"""
        }]
    )

    analysis = response.content[0].text
    print(analysis)

    # Étape 2 : Rapport de recommandations
    print(f"\n{'─'*60}")
    print("🔵 Étape 2 : Génération du rapport de recommandations...")

    response2 = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system="""Tu es un expert en cybersécurité défensive travaillant sur un projet 
scolaire de simulation de téléopération robotaxi.""",
        messages=[{
            "role": "user",
            "content": f"""Sur la base de cette analyse :

{analysis}

Génère un rapport de recommandations court (5-8 lignes) pour renforcer le système, 
incluant des améliorations au niveau du ML et des heuristiques."""
        }]
    )

    print(response2.content[0].text)
    print(f"\n{'='*60}")
    print("FIN DE L'ANALYSE BLUE TEAM")
    print("="*60)

run_blue_team()
