from Helpingai_T2 import Perplexity
import json
import os
from datetime import datetime

# Funktion zum Speichern der finalen Antwort in einer Markdown-Datei
def save_final_answer(answer):
    # Hole die aktuelle Zeit im deutschen Format für den Dateinamen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Definiere den Vortext für den Dateinamen
    filename_prefix = "antwort"
    # Erstelle den Dateinamen
    file_name = f"{filename_prefix}_{timestamp}.md"
    file_path = os.path.join(os.path.expanduser("~/Documents/"), file_name)

    # Erstelle den Inhalt der Markdown-Datei
    content = f"# Finale Antwort\n\n**Zeitstempel:** {timestamp}\n\n{answer}\n"

    # Schreibe den Inhalt in die Datei
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Die finale Antwort wurde in die Datei {file_path} geschrieben.")

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

            # Speichere die finale Antwort in einer Markdown-Datei
            save_final_answer(complete_answer)
            break  # Beende die Schleife, nachdem die finale Antwort ausgegeben wurde