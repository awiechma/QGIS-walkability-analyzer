# walkability_analyzer_dialog.py - Erweiterte GUI-Logik

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog
from qgis.PyQt.QtCore import pyqtSlot, QThread, pyqtSignal
from qgis.core import QgsMessageLog, Qgis
import os
import re
import requests
from datetime import datetime
from .config import MUENSTER_DISTRICTS, SERVICE_CATEGORIES, is_valid_coordinate, is_in_muenster_area, NOMINATIM_URL

# UI-Datei laden
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'walkability_analyzer_dialog_base.ui'))

class GeocodeWorker(QThread):
    """Background worker for geocoding addresses"""
    finished = pyqtSignal(bool, dict)
    
    def __init__(self, address):
        super().__init__()
        self.address = address
        
    def run(self):
        """Perform geocoding in background"""
        try:
            result = self.geocode_address(self.address)
            if result:
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, {})
        except Exception as e:
            QgsMessageLog.logMessage(f"Geocoding error: {str(e)}", level=Qgis.Warning)
            self.finished.emit(False, {})
    
    def geocode_address(self, address):
        """Geocode address using Nominatim"""
        try:
            # Add Münster to improve results if not present
            if 'münster' not in address.lower() and '48' not in address:
                address += ', Münster, Germany'
            
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'de',
                'addressdetails': 1
            }
            
            response = requests.get(NOMINATIM_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    return {
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result['display_name']
                    }
            
            return None
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Geocoding request error: {str(e)}", level=Qgis.Warning)
            return None

class WalkabilityAnalyzerDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(WalkabilityAnalyzerDialog, self).__init__(parent)
        self.setupUi(self)
        
        # Variablen für Ergebnisse
        self.current_analysis = None
        self.current_layers = []
        self.current_coordinates = None
        self.geocode_worker = None
        
        # GUI initialisieren
        self.init_gui()
        
        # Event-Handler verbinden
        self.connect_signals()
    
    def init_gui(self):
        """GUI-Komponenten initialisieren"""
        
        # Stadtteil-Dropdown füllen
        self.comboBox_district.clear()
        self.comboBox_district.addItems(sorted(MUENSTER_DISTRICTS.keys()))
        
        # Zeit-Slider konfigurieren
        self.slider_time.setMinimum(5)
        self.slider_time.setMaximum(20)
        self.slider_time.setValue(15)
        self.slider_time.setSingleStep(1)
        self.update_time_label()
        
        # Service-Checkboxen standardmäßig aktivieren
        self.checkBox_supermarket.setChecked(True)
        self.checkBox_pharmacy.setChecked(True)
        self.checkBox_doctor.setChecked(True)
        self.checkBox_school.setChecked(True)
        self.checkBox_restaurant.setChecked(False)
        self.checkBox_bank.setChecked(False)
        
        # Tab standardmäßig auf Stadtteil setzen
        self.tabWidget_location.setCurrentIndex(0)
        
        # Ergebnisse-Bereich leeren
        self.textBrowser_results.clear()
        self.textBrowser_results.append("Bereit für Analyse...")
        
        # Buttons initial konfigurieren
        self.pushButton_export.setEnabled(False)
        self.pushButton_geocode.setEnabled(True)
        
        # Koordinaten-Validierung
        self.lineEdit_latitude.textChanged.connect(self.validate_coordinates)
        self.lineEdit_longitude.textChanged.connect(self.validate_coordinates)
        
        # Address validation
        self.lineEdit_address.textChanged.connect(self.validate_address)
        
    def connect_signals(self):
        """Event-Handler verbinden"""
        
        # Slider-Änderung
        self.slider_time.valueChanged.connect(self.update_time_label)
        
        # Tab-Wechsel
        self.tabWidget_location.currentChanged.connect(self.on_location_tab_changed)
        
        # Button-Klicks
        self.pushButton_analyze.clicked.connect(self.analyze_walkability)
        self.pushButton_export.clicked.connect(self.export_pdf)
        self.pushButton_reset.clicked.connect(self.reset_analysis)
        self.pushButton_close.clicked.connect(self.close)
        self.pushButton_geocode.clicked.connect(self.geocode_address)
        
        # Stadtteil-Änderung
        self.comboBox_district.currentTextChanged.connect(self.on_district_changed)
    
    def update_time_label(self):
        """Zeit-Label aktualisieren"""
        time_value = self.slider_time.value()
        self.label_time.setText(f"{time_value} Minuten")
    
    def on_location_tab_changed(self, index):
        """Behandle Tab-Wechsel"""
        tab_names = ["Stadtteil", "Koordinaten", "Adresse"]
        current_tab = tab_names[index] if index < len(tab_names) else "Unbekannt"
        
        QgsMessageLog.logMessage(f"Location tab changed to: {current_tab}", level=Qgis.Info)
    
    def on_district_changed(self, district_name):
        """Behandle Stadtteil-Änderung"""
        if district_name and district_name in MUENSTER_DISTRICTS:
            lat, lon = MUENSTER_DISTRICTS[district_name]
            self.current_coordinates = [lon, lat]
            QgsMessageLog.logMessage(f"District selected: {district_name} ({lat}, {lon})", level=Qgis.Info)
    
    def validate_coordinates(self):
        """Validiere eingegebene Koordinaten"""
        lat_text = self.lineEdit_latitude.text().strip()
        lon_text = self.lineEdit_longitude.text().strip()
        
        if not lat_text or not lon_text:
            self.current_coordinates = None
            return
        
        try:
            lat = float(lat_text)
            lon = float(lon_text)
            
            if is_valid_coordinate(lat, lon):
                self.current_coordinates = [lon, lat]
                
                # Prüfe ob in Münster-Bereich
                if not is_in_muenster_area(lat, lon):
                    self.label_coord_info.setText(
                        "<i style='color: orange;'>⚠️ Koordinaten liegen außerhalb des Münster-Bereichs. "
                        "Ergebnisse können eingeschränkt sein.</i>"
                    )
                else:
                    self.label_coord_info.setText(
                        "<i style='color: green;'>✅ Gültige Koordinaten im Münster-Bereich.</i>"
                    )
            else:
                self.current_coordinates = None
                self.label_coord_info.setText(
                    "<i style='color: red;'>❌ Ungültige Koordinaten.</i>"
                )
                
        except ValueError:
            self.current_coordinates = None
            self.label_coord_info.setText(
                "<i style='color: red;'>❌ Koordinaten müssen Zahlen sein.</i>"
            )
    
    def validate_address(self):
        """Validiere Adress-Eingabe"""
        address = self.lineEdit_address.text().strip()
        
        if address:
            self.pushButton_geocode.setEnabled(True)
        else:
            self.pushButton_geocode.setEnabled(False)
            self.current_coordinates = None
    
    def geocode_address(self):
        """Geocodiere eingegebene Adresse"""
        address = self.lineEdit_address.text().strip()
        
        if not address:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine Adresse ein!")
            return
        
        # UI während Geocoding deaktivieren
        self.pushButton_geocode.setEnabled(False)
        self.pushButton_geocode.setText("🔄 Suche...")
        
        self.label_geocode_result.setText("🔄 Geocodierung läuft...")
        
        # Background worker starten
        self.geocode_worker = GeocodeWorker(address)
        self.geocode_worker.finished.connect(self.on_geocode_finished)
        self.geocode_worker.start()
    
    def on_geocode_finished(self, success, result):
        """Behandle Geocoding-Ergebnis"""
        # UI wieder aktivieren
        self.pushButton_geocode.setEnabled(True)
        self.pushButton_geocode.setText("🔍 Suchen")
        
        if success and result:
            lat = result['lat']
            lon = result['lon']
            display_name = result['display_name']
            
            self.current_coordinates = [lon, lat]
            
            # Ergebnis anzeigen
            if is_in_muenster_area(lat, lon):
                self.label_geocode_result.setText(
                    f"<b style='color: green;'>✅ Gefunden:</b><br/>{display_name}<br/>"
                    f"<i>Koordinaten: {lat:.6f}, {lon:.6f}</i>"
                )
            else:
                self.label_geocode_result.setText(
                    f"<b style='color: orange;'>⚠️ Gefunden (außerhalb Münster):</b><br/>{display_name}<br/>"
                    f"<i>Koordinaten: {lat:.6f}, {lon:.6f}</i>"
                )
        else:
            self.current_coordinates = None
            self.label_geocode_result.setText(
                "<b style='color: red;'>❌ Adresse nicht gefunden</b><br/>"
                "<i>Versuchen Sie eine andere Schreibweise oder fügen Sie 'Münster' hinzu.</i>"
            )
        
        # Worker aufräumen
        if self.geocode_worker:
            self.geocode_worker.deleteLater()
            self.geocode_worker = None
    
    def get_current_coordinates(self):
        """Hole aktuell ausgewählte/eingegebene Koordinaten"""
        current_tab = self.tabWidget_location.currentIndex()
        
        if current_tab == 0:  # Stadtteil
            district = self.comboBox_district.currentText()
            if district and district in MUENSTER_DISTRICTS:
                lat, lon = MUENSTER_DISTRICTS[district]
                return [lon, lat], district
        elif current_tab == 1:  # Koordinaten
            if self.current_coordinates:
                lat, lon = self.current_coordinates[1], self.current_coordinates[0]
                location_name = f"Koordinaten ({lat:.4f}, {lon:.4f})"
                return self.current_coordinates, location_name
        elif current_tab == 2:  # Adresse
            if self.current_coordinates:
                address = self.lineEdit_address.text().strip()
                return self.current_coordinates, f"Adresse: {address}"
        
        return None, None
    
    def get_selected_services(self):
        """Ausgewählte Services zurückgeben"""
        services = []
        if self.checkBox_supermarket.isChecked():
            services.append("Supermarkt")
        if self.checkBox_pharmacy.isChecked():
            services.append("Apotheke")
        if self.checkBox_doctor.isChecked():
            services.append("Arzt")
        if self.checkBox_school.isChecked():
            services.append("Schule")
        if self.checkBox_restaurant.isChecked():
            services.append("Restaurant")
        if self.checkBox_bank.isChecked():
            services.append("Bank")
        return services
    
    def analyze_walkability(self):
        """Hauptanalyse-Funktion"""
        try:
            # Koordinaten und Location-Name holen
            coordinates, location_name = self.get_current_coordinates()
            
            if not coordinates:
                QMessageBox.warning(self, "Fehler", 
                    "Bitte wählen Sie einen Standort aus:\n"
                    "• Stadtteil aus der Liste\n"
                    "• Gültige Koordinaten eingeben\n"
                    "• Adresse geocodieren")
                return
            
            time_limit = self.slider_time.value()
            services = self.get_selected_services()
            
            # Validierung
            if not services:
                QMessageBox.warning(self, "Fehler", "Bitte wählen Sie mindestens einen Service aus!")
                return
            
            # Ergebnisse-Bereich leeren
            self.textBrowser_results.clear()
            self.textBrowser_results.append(f"🔍 Analysiere {location_name}...")
            self.textBrowser_results.append(f"📍 Koordinaten: {coordinates[1]:.6f}, {coordinates[0]:.6f}")
            self.textBrowser_results.append(f"⏱️ Maximale Gehzeit: {time_limit} Minuten")
            self.textBrowser_results.append(f"🏪 Services: {', '.join(services)}")
            self.textBrowser_results.append("─" * 50)
            
            # Hier kommt die echte Analyse-Logik
            self.perform_analysis(location_name, coordinates, time_limit, services)
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Analyse: {str(e)}")
            QgsMessageLog.logMessage(f"Walkability Analysis Error: {str(e)}", 
                                   level=Qgis.Critical)
    
    def perform_analysis(self, location_name, coordinates, time_limit, services):
        """Echte Walkability-Analyse durchführen"""
        
        try:
            # Analyzer importieren
            from .walkability_engine import get_walkability_analyzer
            analyzer = get_walkability_analyzer()
            
            # Analyse durchführen
            self.textBrowser_results.append("🔄 Starte Analyse...")
            
            # API-Verbindung testen
            if not analyzer.ors_client.test_connection():
                self.textBrowser_results.append("❌ Keine Verbindung zur OpenRouteService API!")
                self.textBrowser_results.append("Bitte prüfen Sie Ihre Internetverbindung und den API-Key.")
                return
            
            # Hauptanalyse mit benutzerdefinierten Parametern
            result = analyzer.analyze_custom_location(location_name, coordinates, time_limit, services)
            
            # Ergebnisse anzeigen
            self.display_results(result)
            
            # Layer zu QGIS hinzufügen
            if 'layers' in result:
                analyzer.add_layers_to_project(result['layers'])
            
            # Ergebnisse für Export speichern
            self.current_analysis = result
            self.pushButton_export.setEnabled(True)
            
            self.textBrowser_results.append("✅ Analyse abgeschlossen!")
            
        except Exception as e:
            self.textBrowser_results.append(f"❌ Fehler bei der Analyse: {str(e)}")
            QgsMessageLog.logMessage(f"Analysis Error: {str(e)}", level=Qgis.Critical)
    
    def display_results(self, result):
        """Analyse-Ergebnisse anzeigen"""
        
        score = result['score']
        services = result['services']
        
        self.textBrowser_results.append("")
        self.textBrowser_results.append("🏆 ERGEBNISSE:")
        self.textBrowser_results.append("=" * 50)
        
        # Gesamtscore
        total_score = score['total_score']
        self.textBrowser_results.append(f"📊 Walkability-Score: {total_score:.1f}/100")
        
        # Rating
        if total_score >= 80:
            rating = "🟢 Excellent - Sehr gute Walkability"
        elif total_score >= 60:
            rating = "🟡 Good - Gute Walkability"
        elif total_score >= 40:
            rating = "🟠 Fair - Durchschnittliche Walkability"
        else:
            rating = "🔴 Poor - Schlechte Walkability"
        
        self.textBrowser_results.append(f"⭐ Bewertung: {rating}")
        self.textBrowser_results.append("")
        
        # Details pro Service-Typ
        self.textBrowser_results.append("📋 Details pro Service-Typ:")
        self.textBrowser_results.append("-" * 30)
        
        for service_type, service_score in score['service_scores'].items():
            count = service_score['count']
            raw_score = service_score['raw_score']
            min_count = service_score['min_count']
            
            # Status-Icon
            if count >= min_count:
                status = "✅"
            else:
                status = "❌"
            
            self.textBrowser_results.append(
                f"{status} {service_type}: {count} gefunden "
                f"(Score: {raw_score:.1f}/100, Min: {min_count})"
            )
        
        self.textBrowser_results.append("")
        self.textBrowser_results.append(f"🎯 Gesamt-Services: {score['total_services']}")
        self.textBrowser_results.append("")
        
        # Empfehlungen
        self.textBrowser_results.append("💡 Empfehlungen:")
        self.textBrowser_results.append("-" * 15)
        
        if total_score >= 80:
            self.textBrowser_results.append("• Excellent! Dieser Standort hat eine sehr gute Walkability.")
        elif total_score >= 60:
            self.textBrowser_results.append("• Gute Walkability. Kleinere Verbesserungen möglich.")
        elif total_score >= 40:
            self.textBrowser_results.append("• Durchschnittliche Walkability. Mehr Services wären hilfreich.")
        else:
            self.textBrowser_results.append("• Schlechte Walkability. Deutlich mehr Services nötig.")
        
        # Spezifische Empfehlungen
        for service_type, service_score in score['service_scores'].items():
            if service_score['count'] < service_score['min_count']:
                self.textBrowser_results.append(f"• Mehr {service_type} benötigt")
        
        self.textBrowser_results.append("")
        self.textBrowser_results.append("🗺️ Karten-Layer wurden zu QGIS hinzugefügt.")
    
    def export_pdf(self):
        """PDF-Export"""
        if not self.current_analysis:
            QMessageBox.warning(self, "Fehler", "Keine Analyse-Ergebnisse zum Exportieren!")
            return
        
        # Datei-Dialog
        location_name = self.current_analysis.get('location_name', 'Unknown').replace(' ', '_')
        default_name = f"Walkability_{location_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF speichern", default_name, "PDF-Dateien (*.pdf)")
        
        if file_path:
            try:
                # PDF-Export durchführen
                from .pdf_exporter import export_walkability_pdf
                
                self.textBrowser_results.append(f"📄 Exportiere PDF: {file_path}")
                
                # PDF erstellen
                export_walkability_pdf(self.current_analysis, file_path)
                
                self.textBrowser_results.append("✅ PDF erfolgreich erstellt!")
                
                # Erfolgs-Dialog
                QMessageBox.information(self, "Export erfolgreich", 
                                      f"PDF wurde erfolgreich gespeichert:\n{file_path}")
                
            except Exception as e:
                error_msg = f"Fehler beim PDF-Export: {str(e)}"
                self.textBrowser_results.append(f"❌ {error_msg}")
                QMessageBox.critical(self, "Export-Fehler", error_msg)
    
    def reset_analysis(self):
        """Analyse zurücksetzen"""
        self.current_analysis = None
        self.current_layers = []
        self.current_coordinates = None
        
        # GUI zurücksetzen
        self.lineEdit_latitude.clear()
        self.lineEdit_longitude.clear()
        self.lineEdit_address.clear()
        self.label_geocode_result.setText("Adresse eingeben und auf 'Suchen' klicken für Geocodierung.")
        self.label_coord_info.setText("Geben Sie Koordinaten im WGS84-Format ein (Dezimalgrad).")
        
        self.textBrowser_results.clear()
        self.textBrowser_results.append("Bereit für Analyse...")
        self.pushButton_export.setEnabled(False)
        
        QgsMessageLog.logMessage("Analysis reset", level=Qgis.Info)
    
    def closeEvent(self, event):
        """Behandle Dialog-Schließen"""
        # Cleanup bei Dialog-Schließung
        if self.geocode_worker and self.geocode_worker.isRunning():
            self.geocode_worker.terminate()
            self.geocode_worker.wait()
        
        # Temporäre Daten aufräumen
        self.current_analysis = None
        self.current_layers = []
        self.current_coordinates = None
        
        event.accept()
    
    def show_warning(self, title, message):
        """Zeige Warnung"""
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title, message):
        """Zeige Fehler"""
        QMessageBox.critical(self, title, message)
        
    def show_info(self, title, message):
        """Zeige Information"""
        QMessageBox.information(self, title, message)
    
    def is_analysis_ready(self):
        """Prüfe ob Analyse bereit ist"""
        coordinates, _ = self.get_current_coordinates()
        services = self.get_selected_services()
        
        return coordinates is not None and len(services) > 0
    
    def update_analyze_button(self):
        """Aktualisiere Analyse-Button Status"""
        ready = self.is_analysis_ready()
        self.pushButton_analyze.setEnabled(ready)
        
        if ready:
            self.pushButton_analyze.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px; }"
            )
        else:
            self.pushButton_analyze.setStyleSheet(
                "QPushButton { background-color: #cccccc; color: #666666; font-weight: bold; border-radius: 5px; }"
            )
    
    def get_analysis_summary_text(self):
        """Erstelle Zusammenfassungstext der aktuellen Einstellungen"""
        coordinates, location_name = self.get_current_coordinates()
        services = self.get_selected_services()
        time_limit = self.slider_time.value()
        
        if not coordinates or not services:
            return "Nicht bereit für Analyse"
        
        summary_parts = []
        summary_parts.append(f"📍 Standort: {location_name}")
        summary_parts.append(f"⏱️ Gehzeit: {time_limit} Min")
        summary_parts.append(f"🏪 Services: {len(services)} ausgewählt")
        
        return " | ".join(summary_parts)
    
    def log_user_action(self, action):
        """Logge Benutzeraktionen für Debugging"""
        QgsMessageLog.logMessage(f"User Action: {action}", level=Qgis.Info)
    
    def validate_analysis_inputs(self):
        """Validiere alle Eingaben vor der Analyse"""
        coordinates, location_name = self.get_current_coordinates()
        
        if not coordinates:
            return False, "Kein gültiger Standort ausgewählt"
        
        if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 2:
            return False, "Ungültige Koordinaten-Format"
        
        try:
            lon, lat = coordinates
            if not is_valid_coordinate(lat, lon):
                return False, "Koordinaten außerhalb gültiger Bereiche"
        except:
            return False, "Koordinaten-Parsing-Fehler"
        
        services = self.get_selected_services()
        if not services:
            return False, "Mindestens ein Service muss ausgewählt sein"
        
        time_limit = self.slider_time.value()
        if not (5 <= time_limit <= 20):
            return False, "Zeitlimit muss zwischen 5 und 20 Minuten liegen"
        
        return True, "Alle Eingaben gültig"
    
    def get_location_description(self):
        """Erstelle ausführliche Standort-Beschreibung"""
        current_tab = self.tabWidget_location.currentIndex()
        
        if current_tab == 0:  # Stadtteil
            district = self.comboBox_district.currentText()
            if district and district in MUENSTER_DISTRICTS:
                lat, lon = MUENSTER_DISTRICTS[district]
                return {
                    'type': 'district',
                    'name': district,
                    'coordinates': [lon, lat],
                    'description': f"Stadtteil {district}",
                    'source': 'predefined'
                }
        elif current_tab == 1:  # Koordinaten
            if self.current_coordinates:
                lat, lon = self.current_coordinates[1], self.current_coordinates[0]
                return {
                    'type': 'coordinates',
                    'name': f"Koordinaten ({lat:.4f}, {lon:.4f})",
                    'coordinates': self.current_coordinates,
                    'description': f"Benutzerdefinierte Koordinaten: {lat:.6f}, {lon:.6f}",
                    'source': 'user_input'
                }
        elif current_tab == 2:  # Adresse
            if self.current_coordinates:
                address = self.lineEdit_address.text().strip()
                lat, lon = self.current_coordinates[1], self.current_coordinates[0]
                return {
                    'type': 'address',
                    'name': address,
                    'coordinates': self.current_coordinates,
                    'description': f"Geocodierte Adresse: {address}",
                    'source': 'geocoded'
                }
        
        return None
    
    def create_detailed_log_entry(self, event_type, details=None):
        """Erstelle detaillierten Log-Eintrag"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        location_info = self.get_location_description()
        
        log_data = {
            'timestamp': timestamp,
            'event': event_type,
            'location': location_info,
            'settings': {
                'time_limit': self.slider_time.value(),
                'services': self.get_selected_services(),
                'tab_index': self.tabWidget_location.currentIndex()
            }
        }
        
        if details:
            log_data['details'] = details
        
        # Als kompakte JSON-Zeile loggen
        import json
        log_line = json.dumps(log_data, separators=(',', ':'))
        QgsMessageLog.logMessage(f"DETAILED: {log_line}", level=Qgis.Info)
        
        return log_data