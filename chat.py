from Helpingai_T2 import Perplexity
import json
import os
import sys
import subprocess
import random
import requests
import markdown
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QWidget, QTextEdit, QLineEdit, QLabel, QMessageBox,
                            QProgressBar, QStatusBar)
from PyQt5.QtCore import QTimer
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
        
        # Initialisiere Statusvariablen
        self.is_processing = False
        self.last_question = None
        self.last_answer_path = None
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        # Hauptwidget und Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
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
        self.send_button = QPushButton("Frage senden")
        self.send_button.clicked.connect(self.handle_chat)
        layout.addWidget(self.send_button)
        
        self.post_button = QPushButton("Als WordPress Post veröffentlichen")
        self.post_button.clicked.connect(self.create_post)
        self.post_button.setEnabled(False)  # Erst aktivieren, wenn Antwort vorliegt
        layout.addWidget(self.post_button)

    def load_config(self):
        """Lädt die WordPress-Konfiguration und validiert sie"""
        config_path = os.path.expanduser("~/.config/wordpress_pyalex.json")
        try:
            print(f"Versuche Konfiguration zu laden von: {config_path}")
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")
            
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            print("Geladene Konfiguration:", {
                'url': self.config.get('url', 'FEHLT'),
                'username': self.config.get('username', 'FEHLT'),
                'password': '***' if 'password' in self.config else 'FEHLT'
            })
            
            # Validiere erforderliche Felder
            required_fields = ['url', 'username', 'password']
            missing_fields = [field for field in required_fields if not self.config.get(field)]
            
            if missing_fields:
                raise ValueError(f"Fehlende oder leere Konfigurationsfelder: {', '.join(missing_fields)}")
            
            # Validiere URL-Format
            if not self.config['url'].startswith(('http://', 'https://')):
                self.config['url'] = 'https://' + self.config['url']
                print(f"URL korrigiert zu: {self.config['url']}")
            
            self.status_bar.showMessage("Konfiguration erfolgreich geladen")
            
        except FileNotFoundError as e:
            print(f"FEHLER: {str(e)}")
            self.show_error(f"Konfigurationsdatei nicht gefunden unter {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"FEHLER: Ungültiges JSON-Format: {str(e)}")
            self.show_error("Ungültiges JSON-Format in der Konfigurationsdatei")
            sys.exit(1)
        except Exception as e:
            print(f"FEHLER beim Laden der Konfiguration: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            self.show_error(f"Fehler beim Laden der Konfiguration: {str(e)}")
            sys.exit(1)

    def handle_chat(self):
        """Verarbeitet die Chatanfrage mit Fehlerbehandlung und UI-Updates"""
        if self.is_processing:
            self.show_warning("Bitte warten Sie, bis die aktuelle Anfrage abgeschlossen ist.")
            return

        prompt = self.chat_input.text().strip()
        if not prompt:
            self.show_warning("Bitte geben Sie eine Frage ein.")
            return

        self.is_processing = True
        self.update_ui_state(processing=True)
        
        try:
            self.last_question = prompt
            self.chat_input.clear()
            self.response_display.clear()
            
            # Starte Progress Bar
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Unbestimmter Fortschritt
            
            # Verarbeite die Antwort
            for a in Perplexity().generate_answer(prompt):
                if 'final' in a and a['final']:
                    final_response = json.loads(a['text'])
                    complete_answer = final_response.get('answer', 'Keine Antwort verfügbar.')
                    
                    self.response_display.setText(complete_answer)
                    self.last_answer_path = self.save_final_answer(complete_answer)
                    self.open_in_okular(self.last_answer_path)
                    break
                    
            self.post_button.setEnabled(True)
            self.status_bar.showMessage("Antwort erfolgreich generiert")
            
        except json.JSONDecodeError:
            self.show_error("Fehler beim Verarbeiten der AI-Antwort")
        except Exception as e:
            self.show_error(f"Fehler bei der Verarbeitung: {str(e)}")
            traceback.print_exc()
        finally:
            self.is_processing = False
            self.update_ui_state(processing=False)
            self.progress.setVisible(False)

    def update_ui_state(self, processing=False):
        """Aktualisiert den UI-Zustand basierend auf der Verarbeitung"""
        self.send_button.setEnabled(not processing)
        self.chat_input.setEnabled(not processing)
        self.post_button.setEnabled(not processing and self.last_answer_path is not None)
        
        if processing:
            self.status_bar.showMessage("Verarbeite Anfrage...")
        else:
            self.status_bar.showMessage("Bereit")

    def show_error(self, message):
        """Zeigt eine Fehlermeldung an"""
        QMessageBox.critical(self, "Fehler", message)

    def show_warning(self, message):
        """Zeigt eine Warnmeldung an"""
        QMessageBox.warning(self, "Warnung", message)

    def show_success(self, message):
        """Zeigt eine Erfolgsmeldung an"""
        QMessageBox.information(self, "Erfolg", message)

    def save_final_answer(self, answer):
        """Speichert die Antwort mit Fehlerbehandlung"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename_prefix = "antwort"
            file_name = f"{filename_prefix}_{timestamp}.md"
            save_dir = os.path.expanduser("~/Documents/ai-generiert")
            
            # Erstelle Verzeichnis falls nicht vorhanden
            os.makedirs(save_dir, exist_ok=True)
            
            file_path = os.path.join(save_dir, file_name)
            content = f"# Finale Antwort\n\n**Zeitstempel:** {timestamp}\n\n{answer}\n"

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)

            self.status_bar.showMessage(f"Antwort gespeichert: {file_path}")
            return file_path
            
        except Exception as e:
            self.show_error(f"Fehler beim Speichern der Antwort: {str(e)}")
            return None

    def open_in_okular(self, file_path):
        """Öffnet die Datei in Okular mit Fehlerbehandlung"""
        if not file_path:
            return
            
        try:
            subprocess.Popen(['okular', file_path])
        except FileNotFoundError:
            self.show_warning("Okular ist nicht installiert oder nicht im PATH")
        except Exception as e:
            self.show_error(f"Fehler beim Öffnen von Okular: {str(e)}")

    def get_random_image(self):
        """Lädt ein zufälliges Bild mit Timeout und Fehlerbehandlung"""
        try:
            response = requests.get('https://source.unsplash.com/random/800x600', 
                                  timeout=10)
            if response.status_code == 200:
                return BytesIO(response.content)
        except requests.Timeout:
            self.show_warning("Zeitüberschreitung beim Laden des Bildes")
        except Exception as e:
            self.show_error(f"Fehler beim Laden des Bildes: {str(e)}")
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
            self.show_warning("Keine Antwort zum Veröffentlichen verfügbar.")
            return

        try:
            self.status_bar.showMessage("Bereite Post vor...")
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

            self.status_bar.showMessage("Lade Featured Image hoch...")
            # Featured Image hochladen
            thumbnail_id = self.upload_featured_image(client)

            # Post erstellen
            post = WordPressPost()
            post.title = self.last_question
            
            if not post.title:
                post.title = "KI-generierte Antwort"  # Fallback-Titel

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
            self.status_bar.showMessage("Veröffentliche Post...")
            post_id = client.call(NewPost(post))
            self.show_success(f"Post erfolgreich veröffentlicht!\nPost-ID: {post_id}")
            self.status_bar.showMessage("Post erfolgreich veröffentlicht")
            
        except Exception as e:
            error_msg = f"Fehler beim Veröffentlichen: {str(e)}"
            self.show_error(error_msg)
            traceback.print_exc()
            self.status_bar.showMessage("Fehler beim Veröffentlichen")

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()