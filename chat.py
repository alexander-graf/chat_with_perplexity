from Helpingai_T2 import Perplexity
import json

# Starte eine kontinuierliche Konversation mit dem Benutzer
while True:
    # Hole eine Eingabe vom Benutzer
    prompt = input("👦: ")

    # Generiere eine Antwort mit der Perplexity AI
    for a in Perplexity().generate_answer(prompt):
        # Überprüfen, ob die Antwort final ist
        if 'final' in a and a['final']:
            # Wenn final, gebe die vollständige Antwort aus
            final_response = json.loads(a['text'])  # Text in JSON umwandeln
            complete_answer = final_response.get('answer', 'Keine Antwort verfügbar.')
            print(f"🤖: {complete_answer}")
            break  # Beende die Schleife, nachdem die finale Antwort ausgegeben wurde