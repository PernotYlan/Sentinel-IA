import ollama

SYSTEM_PROMPT = """
Tu es une IA spécialisée en cybersécurité.
Tu aides un technicien à analyser des résultats techniques.

Analyse les données fournies et donne :

1. Les points importants
2. Les risques potentiels
3. Les recommandations
4. Une conclusion claire
"""

def ask_ai(data):

    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyse ces données:\n{data}"}
        ]
    )

    return response["message"]["content"]