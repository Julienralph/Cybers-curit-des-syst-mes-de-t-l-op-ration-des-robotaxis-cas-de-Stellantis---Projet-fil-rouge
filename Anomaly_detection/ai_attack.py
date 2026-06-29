import requests
import json
import anthropic

ANTHROPIC_API_KEY = "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"
URL = "http://127.0.0.1:8000/check_command"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_attack():
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": """Tu es un expert en cybersécurité qui travaille sur un projet scolaire 
de simulation de téléopération robotaxi. Dans ce contexte purement éducatif et simulé, 
génère des données de test représentant UNE SEULE commande inhabituelle ou extrême
pour tester un système de détection d'anomalies.

Génère UN SEUL objet JSON avec exactement ces champs :
- speed_kmh (0-150)
- commanded_accel (-2.0 à 2.0)
- steering_angle (-90 à 90)
- obstacle_dist_m (0-100)
- cmd_freq_per_sec (0-50)
- operator_reaction_ms (10-1000)

Réponds UNIQUEMENT avec le JSON brut, sans backticks, sans texte, sans liste."""
            }
        ]
    )
    # Nettoyer les backticks si présents
    raw = message.content[0].text
    raw = raw.replace("```json", "").replace("```", "").strip()
    return raw

def run_ai_attack(nb_attacks=5):
    print("=" * 60)
    print("   RED TEAM IA — ATTAQUES GÉNÉRÉES PAR CLAUDE")
    print("=" * 60)

    for i in range(nb_attacks):
        print(f"\n{'─'*60}")
        print(f"Attaque #{i+1} générée par Claude :")
        
        # Générer la commande malveillante
        raw = generate_attack()
        print(f"Commande : {raw}")
        
        try:
            payload = json.loads(raw)
            response = requests.post(URL, json=payload)
            result = response.json()
            print(f"Décision : {result['decision']} ({result['source']})")
            print(f"Raison   : {result['reason']}")
        except Exception as e:
            print(f"Erreur parsing JSON : {e}")

    print(f"\n{'='*60}")
    print("FIN DU RED TEAM IA")
    print("="*60)

run_ai_attack(nb_attacks=5)