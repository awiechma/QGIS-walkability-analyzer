# 🚶‍♂️ Walkability Analyzer für QGIS

Ein QGIS-Plugin zur Analyse der Fußgängerfreundlichkeit (Walkability) von Standorten in Münster und darüber hinaus.

![Plugin Status](https://img.shields.io/badge/status-beta-orange)
![QGIS Version](https://img.shields.io/badge/QGIS-3.0+-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.6+-blue)
![License](https://img.shields.io/badge/license-GPL%20v2+-green)

## 🌟 Features

### 🎯 Standort-Auswahl
- **Stadtteil-Modus:** Vordefinierte Münster Stadtteile
- **Koordinaten-Modus:** Manuelle Eingabe von Lat/Lon-Koordinaten
- **Adress-Modus:** Geocodierung von Adressen

### 🗺️ Analyse-Funktionen
- **Isochrone-Berechnung:** Erreichbarkeitsanalyse zu Fuß (5-20 Minuten)
- **POI-Analyse:** Automatische Erfassung von Services via OpenStreetMap
- **Walkability-Score:** Bewertung von 0-100 Punkten
- **Service-Kategorien:** Supermarkt, Apotheke, Arzt, Schule, Restaurant, Bank

### 📊 Ergebnisse
- **QGIS-Layer:** Automatische Visualisierung (Isochrone, POIs, Zentrum)
- **Detaillierte Bewertung:** Service-spezifische Scores und Empfehlungen
- **PDF-Export:** Professionelle Berichte für Präsentationen

### 🔧 Technische Features
- **API-Integration:** OpenRouteService für Routing
- **Datenquellen:** OpenStreetMap via Overpass API
- **Abhängigkeits-Management:** Automatische Installation fehlender Pakete
- **Error-Handling:** Robuste Fehlerbehandlung und Logging

## 🚀 Schnellstart

### 1. Installation
```bash
# 1. Plugin-Ordner kopieren nach:
# Windows: C:\Users\[Username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\walkability_analyzer
# Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/walkability_analyzer

# 2. Python-Abhängigkeiten installieren
pip install requests shapely reportlab pyproj

# 3. QGIS neu starten
# 4. Plugin aktivieren: Plugins → Manage and Install Plugins → Installed
```

### 2. Erste Analyse
1. **Plugin starten:** Toolbar-Icon klicken oder `Plugins` → `Walkability Analyzer`
2. **Standort wählen:** Z.B. "Centrum" aus der Stadtteil-Liste
3. **Services auswählen:** Mindestens Supermarkt, Apotheke, Arzt, Schule
4. **Analyse starten:** "🔍 Analysieren" Button klicken
5. **Ergebnisse betrachten:** Score + automatisch erstellte QGIS-Layer

## 📋 Systemanforderungen

### Software
- **QGIS:** 3.0 oder höher
- **Python:** 3.6 oder höher  
- **Internet:** Für API-Zugriffe erforderlich

### Python-Abhängigkeiten
- `requests` - HTTP-Requests für APIs
- `shapely` - Geometrie-Verarbeitung  
- `reportlab` - PDF-Generierung
- `pyproj` - Koordinaten-Transformationen

## 🏗️ Plugin-Architektur

```
walkability_analyzer/
├── 📁 Core Files
│   ├── __init__.py                     # Plugin-Initialisierung
│   ├── walkability_analyzer.py         # Haupt-Plugin-Klasse
│   ├── config.py                       # Konfiguration & Settings
│   └── metadata.txt                    # Plugin-Metadaten
│
├── 📁 GUI Components  
│   ├── walkability_analyzer_dialog.py          # GUI-Logik
│   └── walkability_analyzer_dialog_base.ui     # UI-Design
│
├── 📁 Analysis Engine
│   ├── walkability_engine.py           # Hauptanalysefunktionalität
│   ├── ors_client.py                   # OpenRouteService Client
│   └── overpass_client.py              # OpenStreetMap Client
│
├── 📁 Export & Utils
│   ├── pdf_exporter.py                 # PDF-Export
│   └── dependency_checker.py           # Abhängigkeits-Management
│
└── 📁 Documentation
    ├── README.md                       # Diese Datei
    ├── INSTALLATION.md                 # Installationsanleitung
    └── requirements.txt                # Python Dependencies
```

## ⚙️ Konfiguration

### API-Keys
Das Plugin nutzt standardmäßig einen kostenlosen OpenRouteService API-Key. Für intensive Nutzung empfiehlt sich ein eigener Key:

```python
# In config.py
ORS_API_KEY = "IHR_EIGENER_API_KEY"
```

### Service-Kategorien erweitern
```python
# In config.py
SERVICE_CATEGORIES = {
    "Neue Kategorie": {
        "weight": 0.15, 
        "min_count": 1, 
        "icon": "🏪"
    }
}
```

### Neue Stadtteile hinzufügen
```python
# In config.py  
MUENSTER_DISTRICTS = {
    "Neuer Stadtteil": [51.9606, 7.6261]  # [lat, lon]
}
```

## 🔍 Analyse-Methodik

### Walkability-Score Berechnung
1. **Service-Erfassung:** POIs in Isochrone via Overpass API
2. **Gewichtung:** Jede Service-Kategorie hat individuelle Gewichtung
3. **Mindestanforderungen:** Definierte Mindestanzahl pro Kategorie
4. **Score-Berechnung:** Gewichteter Durchschnitt aller Service-Scores

### Bewertungsskala
- **80-100 Punkte:** 🟢 Excellent - Sehr gute Walkability
- **60-79 Punkte:** 🟡 Good - Gute Walkability  
- **40-59 Punkte:** 🟠 Fair - Durchschnittliche Walkability
- **0-39 Punkte:** 🔴 Poor - Schlechte Walkability

## 📊 Verwendung

### Standort-Modi

#### 🏘️ Stadtteil-Modus
- Vordefinierte Münster Stadtteile
- Sofort einsatzbereit
- Zentrumskoordinaten bereits hinterlegt

#### 🎯 Koordinaten-Modus  
- Manuelle Lat/Lon-Eingabe
- WGS84 Dezimalgrad-Format
- Validierung und Bereichsprüfung

#### 🏠 Adress-Modus
- Geocodierung via Nominatim
- Intelligente Adresserkennung
- Automatische Münster-Zuordnung

### Analyse-Parameter
- **Gehzeit:** 5-20 Minuten (Slider)
- **Service-Auswahl:** 6 vordefinierte Kategorien
- **Qualitätskontrolle:** Input-Validierung

## 📈 Ergebnisse & Export

### QGIS-Layer
- **Isochrone:** Erreichbares Gebiet (Polygon)
- **Zentrum:** Ausgangspunkt (Stern-Symbol)
- **POIs:** Gefundene Services (kategorisierte Symbole)

### PDF-Berichte
- **Zusammenfassung:** Score und Bewertung
- **Details:** Service-spezifische Ergebnisse  
- **Empfehlungen:** Verbesserungsvorschläge
- **Karten-Referenz:** Layer-Information

## 🐛 Problembehandlung

### Häufige Probleme

#### "Fehlende Abhängigkeiten"
```bash
# Lösung: Python-Pakete installieren
pip install requests shapely reportlab pyproj
```

#### "Keine Verbindung zur API"
- Internetverbindung prüfen
- OpenRouteService Status überprüfen
- API-Limits könnten erreicht sein

#### "Keine POIs gefunden"
- Gehzeit vergrößern  
- Anderer Standort testen
- Service-Auswahl erweitern

#### Plugin erscheint nicht
- Alle Dateien im korrekten Verzeichnis?
- QGIS neu gestartet?
- Plugin in der Plugin-Verwaltung aktiviert?

### Debugging
- **QGIS Log-Panel:** `View` → `Panels` → `Log Messages`
- **Plugin-Nachrichten:** "Walkability" Kategorie
- **Verbose Logging:** Detaillierte Analyse-Schritte

## 🤝 Entwicklung & Beitrag

### Lokale Entwicklung
```bash
# Repository klonen
git clone https://github.com/awiechma/walkability-analyzer.git

# In QGIS Plugin-Verzeichnis verlinken
ln -s /path/to/walkability-analyzer ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

# QGIS mit --debug Flag starten für erweiterte Logs
```

### Testing
```python
# Unittest ausführen
python -m pytest test/

# Plugin in QGIS testen  
# QGIS → Plugin Reloader Plugin nutzen für iterative Entwicklung
```

### Code-Struktur
- **PEP 8:** Python Style Guide befolgen
- **Typing:** Type Hints wo möglich
- **Docstrings:** Google-Style Dokumentation
- **Error Handling:** Try-Catch für alle externen Aufrufe

## 📞 Support & Community

### Kontakt
- **Entwickler:** Amon Wiechmann
- **Email:** awiechma@uni-muenster.de
- **Institution:** Universität Münster

### Bug-Reports & Features
- **Issues:** GitHub Issues für Bug-Reports
- **Features:** Feature-Requests via GitHub
- **Pull Requests:** Beiträge willkommen

### Lizenz
GNU General Public License v2+ - Siehe LICENSE Datei für Details.

## 🎯 Roadmap

### Version 1.1 (Geplant)
- [ ] Erweiterte Service-Kategorien (ÖPNV, Parks, etc.)
- [ ] Batch-Verarbeitung mehrerer Standorte  
- [ ] Zeitliche Analyse (verschiedene Tageszeiten)
- [ ] Barrierefreiheits-Parameter

### Version 1.2 (Ideen)
- [ ] Internationale Städte-Unterstützung
- [ ] Machine Learning Walkability-Prediction
- [ ] Web-Service Integration
- [ ] Mobile App Companion

## 🏆 Danksagungen

- **OpenRouteService:** Kostenlose Routing-API
- **OpenStreetMap:** Community-basierte Geodaten
- **QGIS Community:** Entwicklungstools und -support
- **Universität Münster:** Forschungsunterstützung

---

*Entwickelt mit ❤️ für bessere, fußgängerfreundliche Städte.*