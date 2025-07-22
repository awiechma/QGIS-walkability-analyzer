# walkability_analyzer.py - Hauptklasse des Plugins

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsMessageLog, Qgis
import os.path

class WalkabilityAnalyzer:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Declare instance attributes
        self.actions = []
        self.menu = '&Walkability Analyzer'
        self.dlg = None
        self.dependencies_checked = False
        
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        # Fallback icon wenn keine icon.png vorhanden
        if not os.path.exists(icon_path):
            icon_path = ':/images/themes/default/mActionCalculateField.svg'
        
        self.add_action(
            icon_path,
            text='Walkability Analyzer',
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip='Analyze walkability for Münster districts',
            whats_this='Walkability analysis tool for urban planning')

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                '&Walkability Analyzer',
                action)
            self.iface.removeToolBarIcon(action)
        
        # Cleanup
        if self.dlg:
            self.dlg.close()
            self.dlg = None

    def check_dependencies(self):
        """Prüfe Plugin-Abhängigkeiten"""
        try:
            from .dependency_checker import check_plugin_dependencies
            dependencies_ok, missing = check_plugin_dependencies()
            
            if not dependencies_ok:
                QgsMessageLog.logMessage(
                    f"Missing dependencies: {missing}", 
                    level=Qgis.Warning
                )
                return False
            
            QgsMessageLog.logMessage("All dependencies satisfied", level=Qgis.Info)
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Dependency check error: {str(e)}", 
                level=Qgis.Critical
            )
            return False

    def show_startup_error(self, error_message):
        """Zeige Startup-Fehler"""
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Walkability Analyzer - Startup Fehler",
            f"Das Plugin konnte nicht gestartet werden:\n\n{error_message}\n\n"
            "Siehe QGIS Log-Panel für weitere Details."
        )

    def run(self):
        """Run method that performs all the real work"""
        
        try:
            # Create the dialog with elements (after translation) and keep reference
            # Only create GUI ONCE in callback, so that it will only load when the plugin is started
            if self.first_start == True:
                self.first_start = False
                
                # Dependency Check beim ersten Start
                if not self.dependencies_checked:
                    QgsMessageLog.logMessage("Checking plugin dependencies...", level=Qgis.Info)
                    
                    if not self.check_dependencies():
                        error_msg = ("Fehlende Python-Abhängigkeiten!\n\n"
                                   "Das Plugin benötigt zusätzliche Python-Pakete.\n"
                                   "Siehe QGIS Log-Panel für Details oder besuchen Sie die\n"
                                   "Plugin-Dokumentation für Installationsanweisungen.")
                        self.show_startup_error(error_msg)
                        return
                    
                    self.dependencies_checked = True
                
                # Dialog laden
                QgsMessageLog.logMessage("Loading dialog...", level=Qgis.Info)
                
                try:
                    from .walkability_analyzer_dialog import WalkabilityAnalyzerDialog
                    self.dlg = WalkabilityAnalyzerDialog()
                    QgsMessageLog.logMessage("Dialog loaded successfully", level=Qgis.Info)
                    
                except ImportError as e:
                    error_msg = f"Fehler beim Laden der Dialog-Komponenten:\n{str(e)}\n\nMögliche Ursachen:\n- Fehlende Python-Abhängigkeiten\n- Beschädigte Plugin-Dateien"
                    self.show_startup_error(error_msg)
                    QgsMessageLog.logMessage(f"Dialog import error: {str(e)}", level=Qgis.Critical)
                    return
                    
                except Exception as e:
                    error_msg = f"Unerwarteter Fehler beim Dialog-Setup:\n{str(e)}"
                    self.show_startup_error(error_msg)
                    QgsMessageLog.logMessage(f"Dialog setup error: {str(e)}", level=Qgis.Critical)
                    return

            # Show the dialog
            if self.dlg:
                QgsMessageLog.logMessage("Showing dialog...", level=Qgis.Info)
                self.dlg.show()
                
                # Run the dialog event loop
                result = self.dlg.exec_()
                
                QgsMessageLog.logMessage(f"Dialog closed with result: {result}", level=Qgis.Info)
                
                # See if OK was pressed
                if result:
                    QgsMessageLog.logMessage("Dialog accepted", level=Qgis.Info)
                else:
                    QgsMessageLog.logMessage("Dialog cancelled", level=Qgis.Info)
            else:
                QgsMessageLog.logMessage("Dialog not available", level=Qgis.Critical)
                
        except Exception as e:
            error_msg = f"Unerwarteter Plugin-Fehler:\n{str(e)}"
            QgsMessageLog.logMessage(f"Plugin runtime error: {str(e)}", level=Qgis.Critical)
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Plugin Fehler",
                error_msg
            )