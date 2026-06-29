import requests
import json
import anthropic

ANTHROPIC_API_KEY = "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"
URL = "http://127.0.0.1:8000/check_command"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def run_red_team(nb_rounds=6):
    print("=" * 60)
    print("   AGENT RED TEAM AUTONOME — ROBOTAXI TÉLÉOPÉRATION")
    print("=" * 60)

    # Historique de conversation — c'est ce qui rend l'agent adaptatif
    conversation_history = []
    results_history = []

    # Prompt système
    system_prompt = """Tu es un expert en cybersécurité travaillant sur un projet 
scolaire de simulation de téléopération robotaxi. Tu joues le rôle d'un attaquant 
qui teste un système de détection d'anomalies dans un environnement purement éducatif 
et simulé.

Ton objectif : générer des commandes de conduite qui passent inaperçues (ACCEPT) 
ou qui causent un maximum de dégâts (DISENGAGE) en apprenant des réponses précédentes.

À chaque round, génère UN SEUL objet JSON avec ces champs :
- speed_kmh (0-150)
- commanded_accel (-2.0 à 2.0)  
- steering_angle (-90 à 90)
- obstacle_dist_m (0-100)
- cmd_freq_per_sec (0-50)
- operator_reaction_ms (10-1000)

Réponds UNIQUEMENT avec le JSON brut, sans backticks, sans texte."""

    for i in range(nb_rounds):
        print(f"\n{'─'*60}")
        print(f"Round #{i+1} — Agent Red Team réfléchit...")

        # Construire le message selon le round
        if i == 0:
            user_message = "Round #1 : génère ta première attaque."
        else:
            last = results_history[-1]
            user_message = f"""Round #{i+1}.
Ton attaque précédente : {last['command']}
Résultat obtenu : {last['decision']} — Raison : {last['reason']}

{"✅ Tu as réussi à passer ! Essaie une attaque encore plus dangereuse." if last['decision'] == 'ACCEPT' else "❌ Tu as été détecté. Adapte ta stratégie pour contourner la détection."}

Génère une nouvelle commande JSON."""

        conversation_history.append({"role": "user", "content": user_message})

        # Appel Claude
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system=system_prompt,
            messages=conversation_history
        )

        raw = response.content[0].text
        raw = raw.replace("```json", "").replace("```", "").strip()
        conversation_history.append({"role": "assistant", "content": raw})

        print(f"Commande générée : {raw}")

        # Envoyer à l'API
        try:
            payload = json.loads(raw)
            api_response = requests.post(URL, json=payload)
            result = api_response.json()

            decision = result['decision']
            reason = result['reason']
            source = result['source']

            # Couleurs
            colors = {"ACCEPT": "\033[92m", "LIMIT": "\033[93m", "DISENGAGE": "\033[91m"}
            color = colors.get(decision, "")
            reset = "\033[0m"

            print(f"Décision   : {color}{decision}{reset} ({source})")
            print(f"Raison     : {reason}")

            results_history.append({
                "command": raw,
                "decision": decision,
                "reason": reason
            })

        except Exception as e:
            print(f"Erreur : {e}")

    # Bilan final
    print(f"\n{'='*60}")
    print("BILAN DU RED TEAM")
    print(f"{'='*60}")
    accepts    = sum(1 for r in results_history if r['decision'] == 'ACCEPT')
    limits     = sum(1 for r in results_history if r['decision'] == 'LIMIT')
    disengages = sum(1 for r in results_history if r['decision'] == 'DISENGAGE')
    print(f"ACCEPT    : {accepts}/{nb_rounds} — attaques passées inaperçues ⚠️")
    print(f"LIMIT     : {limits}/{nb_rounds} — attaques limitées")
    print(f"DISENGAGE : {disengages}/{nb_rounds} — attaques bloquées ✅")

run_red_team(nb_rounds=6)