# walkability_analyzer_dialog.py - GUI-Logik

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog
from qgis.PyQt.QtCore import pyqtSlot
from qgis.core import QgsMessageLog, Qgis
import os
from datetime import datetime
from .config import MUENSTER_DISTRICTS, SERVICE_CATEGORIES, TIME_LIMITS

# UI-Datei laden
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'walkability_analyzer_dialog_base.ui'))

class WalkabilityAnalyzerDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(WalkabilityAnalyzerDialog, self).__init__(parent)
        self.setupUi(self)
        
        # Variablen für Ergebnisse
        self.current_analysis = None
        self.current_layers = []
        
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
        
        # Ergebnisse-Bereich leeren
        self.textBrowser_results.clear()
        self.textBrowser_results.append("Bereit für Analyse...")
        
        # Buttons initial konfigurieren
        self.pushButton_export.setEnabled(False)
        
    def connect_signals(self):
        """Event-Handler verbinden"""
        
        # Slider-Änderung
        self.slider_time.valueChanged.connect(self.update_time_label)
        
        # Button-Klicks
        self.pushButton_analyze.clicked.connect(self.analyze_walkability)
        self.pushButton_export.clicked.connect(self.export_pdf)
        self.pushButton_reset.clicked.connect(self.reset_analysis)
        self.pushButton_close.clicked.connect(self.close)
    
    def update_time_label(self):
        """Zeit-Label aktualisieren"""
        time_value = self.slider_time.value()
        self.label_time.setText(f"{time_value} Minuten")
    
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
            # GUI-Werte auslesen
            district = self.comboBox_district.currentText()
            time_limit = self.slider_time.value()
            services = self.get_selected_services()
            
            # Validierung
            if not district:
                QMessageBox.warning(self, "Fehler", "Bitte wählen Sie einen Stadtteil aus!")
                return
            
            if not services:
                QMessageBox.warning(self, "Fehler", "Bitte wählen Sie mindestens einen Service aus!")
                return
            
            # Ergebnisse-Bereich leeren
            self.textBrowser_results.clear()
            self.textBrowser_results.append(f"🔍 Analysiere {district}...")
            self.textBrowser_results.append(f"⏱️ Maximale Gehzeit: {time_limit} Minuten")
            self.textBrowser_results.append(f"🏪 Services: {', '.join(services)}")
            self.textBrowser_results.append("─" * 50)
            
            # Hier kommt die echte Analyse-Logik (Schritt 4)
            self.perform_analysis(district, time_limit, services)
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Analyse: {str(e)}")
            QgsMessageLog.logMessage(f"Walkability Analysis Error: {str(e)}", 
                                   level=Qgis.Critical)
    
    def perform_analysis(self, district, time_limit, services):
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
            
            # Hauptanalyse
            result = analyzer.analyze_district(district, time_limit, services)
            
            # Ergebnisse anzeigen
            self.display_results(result)
            
            # Layer zu QGIS hinzufügen
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
            self.textBrowser_results.append("• Excellent! Dieser Stadtteil hat eine sehr gute Walkability.")
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
        default_name = f"Walkability_{self.current_analysis['district']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF speichern", default_name, "PDF-Dateien (*.pdf)")
        
        if file_path:
            try:
                # PDF-Export durchführen
                from .pdf_exporter import export_walkability_pdf
                from datetime import datetime
                
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
        self.textBrowser_results.clear()
        self.textBrowser_results.append("Bereit für Analyse...")
        self.pushButton_export.setEnabled(False)
        
        # Bestehende Layer entfernen
        # TODO: Layer-Management implementieren