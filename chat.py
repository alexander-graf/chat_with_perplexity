from Helpingai_T2 import Perplexity
import json
import os
import sys
import subprocess
import random
import requests
import markdown
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QWidget, QTextEdit, QLineEdit, QLabel)
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client
from io import BytesIO

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat & WordPress Publisher")
        self.setGeometry(100, 100, 800, 600)
        
        # Lade WordPress Konfiguration
        self.load_config()

        # Layout erstellen
        layout = QVBoxLayout()
        
        # Chat Eingabe
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Stelle deine Frage...")
        self.chat_input.returnPressed.connect(self.handle_chat)
        layout.addWidget(self.chat_input)
        
        # Antwort Anzeige
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        layout.addWidget(self.response_display)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.send_button = QPushButton("Frage senden")
        self.send_button.clicked.connect(self.handle_chat)
        button_layout.addWidget(self.send_button)
        
        self.post_button = QPushButton("Als WordPress Post veröffentlichen")
        self.post_button.clicked.connect(self.create_post)
        button_layout.addWidget(self.post_button)
        
        layout.addLayout(button_layout)

        # Zentrales Widget setzen
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Speichere den Pfad der letzten Antwort
        self.last_answer_path = None

    def load_config(self):
        config_path = os.path.expanduser("~/.config/wordpress_pyalex.json")
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"Fehler: Konfigurationsdatei nicht gefunden unter {config_path}")
            sys.exit(1)

    def handle_chat(self):
        prompt = self.chat_input.text()
        if not prompt:
            return
            
        self.chat_input.clear()
        self.response_display.clear()
        
        # Speichere die ursprüngliche Frage für den Titel
        self.last_question = prompt
        
        # Generiere eine Antwort mit der Perplexity AI
        for a in Perplexity().generate_answer(prompt):
            if 'final' in a and a['final']:
                final_response = json.loads(a['text'])
                complete_answer = final_response.get('answer', 'Keine Antwort verfügbar.')
                
                # Zeige die Antwort in der GUI
                self.response_display.setText(complete_answer)
                
                # Speichere die Antwort und öffne sie in Okular
                self.last_answer_path = self.save_final_answer(complete_answer)
                self.open_in_okular(self.last_answer_path)
                break

    def save_final_answer(self, answer):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename_prefix = "antwort"
        file_name = f"{filename_prefix}_{timestamp}.md"
        file_path = os.path.join(os.path.expanduser("~/Documents/ai-generiert"), file_name)

        content = f"# Finale Antwort\n\n**Zeitstempel:** {timestamp}\n\n{answer}\n"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"Die finale Antwort wurde in die Datei {file_path} geschrieben.")
        return file_path

    def open_in_okular(self, file_path):
        try:
            subprocess.Popen(['okular', file_path])
        except Exception as e:
            print(f"Fehler beim Öffnen von Okular: {str(e)}")

    def get_random_image(self):
        """Lädt ein zufälliges Bild von Unsplash"""
        try:
            response = requests.get('https://source.unsplash.com/random/800x600')
            if response.status_code == 200:
                return BytesIO(response.content)
        except Exception as e:
            print(f"Fehler beim Laden des Bildes: {str(e)}")
        return None

    def upload_featured_image(self, client):
        """Lädt ein Bild hoch und gibt die ID zurück"""
        image_data = self.get_random_image()
        if not image_data:
            return None

        filename = f'featured-image-{datetime.now().strftime("%Y%m%d-%H%M%S")}.jpg'
        data = {
            'name': filename,
            'type': 'image/jpeg',
            'bits': xmlrpc_client.Binary(image_data.getvalue())
        }

        response = client.call(UploadFile(data))
        return response.get('id')

    def create_post(self):
        if not self.last_answer_path:
            print("Keine Antwort zum Veröffentlichen verfügbar.")
            return

        try:
            # Markdown-Datei lesen und konvertieren
            with open(self.last_answer_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Markdown zu HTML konvertieren
            md = markdown.Markdown(extensions=['extra', 'codehilite'])
            html_content = md.convert(markdown_content)

            # WordPress Client erstellen
            wp_url = self.config['url'].rstrip('/')
            if not wp_url.endswith('/xmlrpc.php'):
                wp_url = f"{wp_url}/xmlrpc.php"
            
            client = Client(
                wp_url,
                self.config['username'],
                self.config['password']
            )

            # Featured Image hochladen
            thumbnail_id = self.upload_featured_image(client)

            # Post erstellen
            post = WordPressPost()
            post.title = self.last_question

            # Formatiere den Content mit Gutenberg-Blöcken
            formatted_content = f"""
<!-- wp:group {{"backgroundColor":"white"}} -->
<div class="wp-block-group has-white-background-color">

<!-- wp:heading -->
<h1>{self.last_question}</h1>
<!-- /wp:heading -->

<!-- wp:separator -->
<hr class="wp-block-separator"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><strong>🤔 Frage:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:quote -->
<blockquote class="wp-block-quote">
<p>{self.last_question}</p>
</blockquote>
<!-- /wp:quote -->

<!-- wp:paragraph -->
<p><strong>🤖 Antwort:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:group {{"backgroundColor":"light-gray"}} -->
<div class="wp-block-group has-light-gray-background-color">
{html_content}
</div>
<!-- /wp:group -->

<!-- wp:separator -->
<hr class="wp-block-separator"/>
<!-- /wp:separator -->

<!-- wp:paragraph {{"textColor":"gray","fontSize":"small"}} -->
<p class="has-gray-color has-text-color has-small-font-size">Generiert mit KI am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr</p>
<!-- /wp:paragraph -->

</div>
<!-- /wp:group -->
"""
            post.content = formatted_content
            post.post_status = 'publish'
            
            # Kategorien und Tags
            post.terms_names = {
                'category': ['AI-Antworten', 'KI-Generiert'],
                'post_tag': ['AI', 'Perplexity', 'KI-Antwort', 'Automatisiert']
            }

            # Featured Image setzen
            if thumbnail_id:
                post.thumbnail = thumbnail_id

            # Custom Fields für Metadaten
            post.custom_fields = [
                {'key': 'ai_generated', 'value': 'true'},
                {'key': 'generation_date', 'value': datetime.now().isoformat()},
                {'key': 'ai_model', 'value': 'Perplexity'}
            ]

            # Post veröffentlichen
            post_id = client.call(NewPost(post))
            print(f"Post erfolgreich veröffentlicht! Post-ID: {post_id}")
            
        except Exception as e:
            print(f"Fehler beim Veröffentlichen: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()