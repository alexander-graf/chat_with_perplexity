# AI Chat & WordPress Publisher

Eine Python-Desktop-Anwendung, die KI-gestützte Chats ermöglicht und die Antworten automatisch als WordPress-Posts veröffentlichen kann.

## 🌟 Features

- **KI-Chat-Interface**
  - Dunkles, modernes Design
  - Echtzeit-Antworten von der Perplexity AI
  - Fortschrittsanzeige während der Verarbeitung
  - Automatische Speicherung der Antworten

- **WordPress-Integration**
  - Automatische Post-Erstellung
  - Gutenberg-Block-formatierte Inhalte
  - Zufällige Featured Images von Unsplash
  - Automatische Kategorien und Tags
  - Metadaten-Tracking

- **Dokumentenmanagement**
  - Automatische Markdown-Dateierstellung
  - Direkte Okular-Integration zur Vorschau
  - Strukturierte Dateiablage

- **Benutzerfreundlichkeit**
  - Multi-Monitor-Unterstützung
  - Dark Mode
  - Statusanzeigen und Fortschrittsbalken
  - Fehlerbehandlung und Benutzerbenachrichtigungen

## 🔧 Installation

1. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

2. **WordPress-Konfiguration**
   
   Erstellen Sie eine Konfigurationsdatei unter `~/.config/wordpress_pyalex.json`:
   ```json
   {
       "url": "https://ihre-wordpress-seite.de",
       "username": "ihr_benutzername",
       "password": "ihr_password"
   }
   ```

3. **Okular Installation (für Linux)**
   ```bash
   sudo apt-get install okular    # Für Ubuntu/Debian
   sudo dnf install okular        # Für Fedora
   ```

## 📝 Verwendung

1. **Programm starten**
   ```bash
   python chat.py
   ```

2. **Chat verwenden**
   - Geben Sie Ihre Frage in das Eingabefeld ein
   - Drücken Sie Enter oder klicken Sie "Frage senden"
   - Die Antwort erscheint im Textfeld und wird automatisch gespeichert

3. **Als WordPress-Post veröffentlichen**
   - Klicken Sie "Als WordPress Post veröffentlichen"
   - Der Post wird automatisch formatiert und mit einem zufälligen Bild hochgeladen

## 🔨 Technische Details

### Abhängigkeiten
- PyQt5 für die GUI
- Helpingai_T2 (Perplexity) für KI-Antworten
- python-wordpress-xmlrpc für WordPress-Integration
- markdown für Markdown-zu-HTML-Konvertierung
- requests für HTTP-Anfragen

### Verzeichnisstruktur


