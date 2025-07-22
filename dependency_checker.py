# dependency_checker.py - Prüfung der Python-Abhängigkeiten

import sys
import importlib
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.core import QgsMessageLog, Qgis

class DependencyInstaller(QThread):
    """Background thread für Package-Installation"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, packages):
        super().__init__()
        self.packages = packages
    
    def run(self):
        """Installiere Packages im Hintergrund"""
        try:
            import subprocess
            
            for package in self.packages:
                self.progress.emit(f"Installiere {package}...")
                
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"Fehler bei Installation von {package}:\n{result.stderr}"
                    self.finished.emit(False, error_msg)
                    return
            
            self.finished.emit(True, "Alle Pakete erfolgreich installiert!")
            
        except Exception as e:
            self.finished.emit(False, f"Installation fehlgeschlagen: {str(e)}")

class DependencyDialog(QDialog):
    """Dialog für fehlende Abhängigkeiten"""
    
    def __init__(self, missing_packages, parent=None):
        super().__init__(parent)
        self.missing_packages = missing_packages
        self.installer_thread = None
        self.init_ui()
    
    def init_ui(self):
        """UI initialisieren"""
        self.setWindowTitle("Fehlende Abhängigkeiten - Walkability Analyzer")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔧 Fehlende Python-Pakete")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Beschreibung
        desc_text = (
            "Das Walkability Analyzer Plugin benötigt zusätzliche Python-Pakete.\n"
            f"Folgende {len(self.missing_packages)} Pakete fehlen:"
        )
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet("margin: 10px;")
        layout.addWidget(desc)
        
        # Liste fehlender Pakete
        packages_text = "\n".join([f"• {pkg}" for pkg in self.missing_packages])
        packages_label = QLabel(packages_text)
        packages_label.setStyleSheet("font-family: monospace; margin: 10px; padding: 10px; background: #f0f0f0;")
        layout.addWidget(packages_label)
        
        # Status-Text-Bereich
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.append("Bereit für Installation...")
        layout.addWidget(self.status_text)
        
        # Buttons
        self.install_button = QPushButton("📦 Automatisch installieren")
        self.install_button.clicked.connect(self.auto_install)
        self.install_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        layout.addWidget(self.install_button)
        
        manual_button = QPushButton("📋 Manuelle Anweisungen anzeigen")
        manual_button.clicked.connect(self.show_manual_instructions)
        layout.addWidget(manual_button)
        
        close_button = QPushButton("❌ Abbrechen")
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def auto_install(self):
        """Starte automatische Installation"""
        self.install_button.setEnabled(False)
        self.install_button.setText("⏳ Installiere...")
        
        self.status_text.clear()
        self.status_text.append("🔄 Starte Installation...")
        
        # Installer-Thread starten
        self.installer_thread = DependencyInstaller(self.missing_packages)
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        self.installer_thread.start()
    
    def update_progress(self, message):
        """Update Installation Progress"""
        self.status_text.append(message)
    
    def installation_finished(self, success, message):
        """Installation abgeschlossen"""
        self.install_button.setEnabled(True)
        self.install_button.setText("📦 Automatisch installieren")
        
        if success:
            self.status_text.append(f"✅ {message}")
            QMessageBox.information(self, "Installation erfolgreich", 
                                  "Alle Pakete wurden erfolgreich installiert!\n"
                                  "Bitte starten Sie QGIS neu.")
            self.accept()
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.warning(self, "Installation fehlgeschlagen", 
                              "Automatische Installation fehlgeschlagen.\n"
                              "Bitte verwenden Sie die manuellen Anweisungen.")
    
    def show_manual_instructions(self):
        """Zeige manuelle Installationsanweisungen"""
        instructions = f"""
Manuelle Installation der Python-Pakete:

Option 1: QGIS Python-Konsole
1. Öffnen Sie QGIS
2. Gehen Sie zu Plugins → Python Console
3. Führen Sie folgende Befehle aus:

import subprocess
import sys
packages = {self.missing_packages}
for pkg in packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

Option 2: Kommandozeile
Öffnen Sie eine Kommandozeile und führen Sie aus:
pip install {' '.join(self.missing_packages)}

Option 3: Conda (falls verwendet)
conda install {' '.join(self.missing_packages)}

Nach der Installation starten Sie QGIS neu.
"""
        
        QMessageBox.information(self, "Manuelle Installation", instructions)

class DependencyChecker:
    """Hauptklasse für Abhängigkeits-Prüfung"""
    
    # Definiere benötigte Pakete
    REQUIRED_PACKAGES = {
        'requests': {
            'import_name': 'requests',
            'pip_name': 'requests',
            'description': 'HTTP-Bibliothek für API-Aufrufe'
        },
        'shapely': {
            'import_name': 'shapely.geometry',
            'pip_name': 'shapely', 
            'description': 'Geometrie-Verarbeitung'
        },
        'reportlab': {
            'import_name': 'reportlab.lib.pagesizes',
            'pip_name': 'reportlab',
            'description': 'PDF-Generierung'
        },
        'pyproj': {
            'import_name': 'pyproj',
            'pip_name': 'pyproj',
            'description': 'Koordinaten-Transformationen'
        }
    }
    
    @classmethod
    def check_dependencies(cls, show_dialog=True):
        """
        Prüfe alle Abhängigkeiten
        
        :param show_dialog: Zeige Dialog bei fehlenden Paketen
        :return: (alle_vorhanden, fehlende_pakete)
        """
        missing_packages = []
        available_packages = []
        
        for pkg_key, pkg_info in cls.REQUIRED_PACKAGES.items():
            try:
                importlib.import_module(pkg_info['import_name'])
                available_packages.append(pkg_key)
                QgsMessageLog.logMessage(f"✅ {pkg_key} available", level=Qgis.Info)
            except ImportError:
                missing_packages.append(pkg_info['pip_name'])
                QgsMessageLog.logMessage(f"❌ {pkg_key} missing", level=Qgis.Warning)
        
        all_available = len(missing_packages) == 0
        
        # Log Ergebnis
        if all_available:
            QgsMessageLog.logMessage("All dependencies satisfied", level=Qgis.Info)
        else:
            QgsMessageLog.logMessage(f"Missing packages: {missing_packages}", level=Qgis.Warning)
        
        # Dialog zeigen falls gewünscht und Pakete fehlen
        if not all_available and show_dialog:
            cls.show_dependency_dialog(missing_packages)
        
        return all_available, missing_packages
    
    @classmethod
    def show_dependency_dialog(cls, missing_packages):
        """Zeige Abhängigkeits-Dialog"""
        try:
            dialog = DependencyDialog(missing_packages)
            result = dialog.exec_()
            return result == QDialog.Accepted
        except Exception as e:
            QgsMessageLog.logMessage(f"Error showing dependency dialog: {str(e)}", level=Qgis.Critical)
            return False
    
    @classmethod
    def check_individual_package(cls, package_key):
        """Prüfe einzelnes Paket"""
        if package_key not in cls.REQUIRED_PACKAGES:
            return False
        
        pkg_info = cls.REQUIRED_PACKAGES[package_key]
        try:
            importlib.import_module(pkg_info['import_name'])
            return True
        except ImportError:
            return False
    
    @classmethod
    def get_package_info(cls):
        """Hole Information über alle Pakete"""
        info = []
        for pkg_key, pkg_data in cls.REQUIRED_PACKAGES.items():
            available = cls.check_individual_package(pkg_key)
            info.append({
                'key': pkg_key,
                'pip_name': pkg_data['pip_name'],
                'description': pkg_data['description'],
                'available': available
            })
        return info

def check_plugin_dependencies():
    """Hauptfunktion für Abhängigkeits-Check"""
    return DependencyChecker.check_dependencies()