# walkability_engine.py - Hauptanalysefunktionalität

import json
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject, 
    QgsSymbol, QgsRendererRange, QgsGraduatedSymbolRenderer,
    QgsSimpleMarkerSymbolLayer, QgsMarkerSymbol, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsMessageLog, Qgis, QgsFillSymbol
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

from .ors_client import ORSClient
from .overpass_client import OverpassClient
from .config import MUENSTER_DISTRICTS, SERVICE_CATEGORIES

class WalkabilityAnalyzer:
    """Hauptklasse für Walkability-Analyse"""
    
    def __init__(self):
        self.ors_client = ORSClient()
        self.overpass_client = OverpassClient()
    
    def analyze_district(self, district_name, time_limit, service_types):
        """
        Führe vollständige Walkability-Analyse für einen Stadtteil durch
        
        :param district_name: Name des Stadtteils
        :param time_limit: Maximale Gehzeit in Minuten
        :param service_types: Liste der zu analysierenden Service-Typen
        :return: Analyse-Ergebnisse
        """
        
        try:
            # Koordinaten des Stadtteils abrufen
            if district_name not in MUENSTER_DISTRICTS:
                raise ValueError(f"Stadtteil '{district_name}' nicht gefunden")
            
            lat, lon = MUENSTER_DISTRICTS[district_name]
            coordinates = [lon, lat]  # ORS erwartet [lon, lat]
            
            QgsMessageLog.logMessage(f"Analyzing {district_name} at {lat}, {lon}", level=Qgis.Info)
            
            # 1. Isochrone berechnen
            isochrone_data = self.ors_client.get_isochrone(coordinates, time_limit)
            
            if not isochrone_data:
                raise Exception("Konnte keine Isochrone berechnen")
            
            # 2. POIs in Isochrone finden
            pois_data = self.overpass_client.get_pois_in_area(isochrone_data, service_types)
            
            # 3. Score berechnen
            score_data = self.calculate_walkability_score(pois_data, service_types)
            
            # 4. QGIS-Layer erstellen
            layers = self.create_qgis_layers(district_name, isochrone_data, pois_data, coordinates)
            
            # 5. Ergebnisse zusammenstellen
            result = {
                'district': district_name,
                'coordinates': coordinates,
                'time_limit': time_limit,
                'service_types': service_types,
                'isochrone': isochrone_data,
                'services': pois_data,
                'score': score_data,
                'layers': layers
            }
            
            return result
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Analysis error: {str(e)}", level=Qgis.Critical)
            raise
    
    def calculate_walkability_score(self, pois_data, service_types):
        """
        Berechne Walkability-Score basierend auf verfügbaren Services
        
        :param pois_data: Dictionary mit POIs pro Service-Typ
        :param service_types: Liste der analysierten Service-Typen
        :return: Score-Daten
        """
        
        service_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        total_services = 0
        
        for service_type in service_types:
            if service_type in SERVICE_CATEGORIES:
                config = SERVICE_CATEGORIES[service_type]
                weight = config['weight']
                min_count = config['min_count']
                
                # Anzahl gefundener Services
                found_count = len(pois_data.get(service_type, []))
                total_services += found_count
                
                # Score berechnen (0-100)
                if found_count == 0:
                    raw_score = 0.0
                elif found_count >= min_count:
                    # Vollpunktzahl wenn Minimum erreicht, Bonus für mehr
                    raw_score = 100.0 + min(50.0, (found_count - min_count) * 10)
                    raw_score = min(100.0, raw_score)  # Maximal 100
                else:
                    # Teilpunktzahl wenn unter Minimum
                    raw_score = (found_count / min_count) * 70.0  # Max 70% wenn unter Minimum
                
                service_scores[service_type] = {
                    'count': found_count,
                    'min_count': min_count,
                    'raw_score': raw_score,
                    'weight': weight,
                    'weighted_score': raw_score * weight
                }
                
                total_weighted_score += raw_score * weight
                total_weight += weight
        
        # Gesamtscore berechnen
        if total_weight > 0:
            total_score = total_weighted_score / total_weight
        else:
            total_score = 0.0
        
        return {
            'total_score': total_score,
            'service_scores': service_scores,
            'total_services': total_services,
            'total_weight': total_weight
        }
    
    def create_qgis_layers(self, district_name, isochrone_data, pois_data, center_coords):
        """
        Erstelle QGIS-Layer für Visualisierung
        
        :param district_name: Name des Stadtteils
        :param isochrone_data: Isochrone GeoJSON
        :param pois_data: POI-Daten
        :param center_coords: Zentrumskoordinaten
        :return: Dictionary mit erstellten Layern
        """
        
        layers = {}
        
        try:
            # 1. Isochrone-Layer
            isochrone_layer = self.create_isochrone_layer(district_name, isochrone_data)
            if isochrone_layer:
                layers['isochrone'] = isochrone_layer
            
            # 2. Zentrum-Layer  
            center_layer = self.create_center_layer(district_name, center_coords)
            if center_layer:
                layers['center'] = center_layer
            
            # 3. POI-Layer
            poi_layer = self.create_poi_layer(district_name, pois_data)
            if poi_layer:
                layers['pois'] = poi_layer
                
            return layers
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Layer creation error: {str(e)}", level=Qgis.Critical)
            return {}
    
    def create_isochrone_layer(self, district_name, isochrone_data):
        """Erstelle Isochrone-Layer"""
        
        try:
            # Temporäre Datei für GeoJSON
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False)
            json.dump(isochrone_data, temp_file, indent=2)
            temp_file.close()
            
            # Layer erstellen
            layer_name = f"Walkability_Isochrone_{district_name}"
            layer = QgsVectorLayer(temp_file.name, layer_name, "ogr")
            
            if not layer.isValid():
                QgsMessageLog.logMessage("Isochrone layer is invalid", level=Qgis.Critical)
                os.unlink(temp_file.name)
                return None
            
            # Styling
            symbol = QgsFillSymbol.createSimple({
                'color': '70,130,180,100',  # Semi-transparent blue
                'outline_color': '30,80,120,255',
                'outline_width': '2'
            })
            layer.renderer().setSymbol(symbol)
            
            # Aufräumen
            os.unlink(temp_file.name)
            
            return layer
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Isochrone layer error: {str(e)}", level=Qgis.Critical)
            return None
    
    def create_center_layer(self, district_name, center_coords):
        """Erstelle Zentrum-Layer"""
        
        try:
            layer_name = f"Walkability_Center_{district_name}"
            layer = QgsVectorLayer("Point?crs=EPSG:4326", layer_name, "memory")
            
            # Feld hinzufügen
            layer.dataProvider().addAttributes([
                {'name': 'district', 'type': QVariant.String},
                {'name': 'lon', 'type': QVariant.Double},
                {'name': 'lat', 'type': QVariant.Double}
            ])
            layer.updateFields()
            
            # Feature erstellen
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(center_coords[0], center_coords[1]))
            feature.setAttributes([district_name, center_coords[0], center_coords[1]])
            
            layer.dataProvider().addFeatures([feature])
            layer.updateExtents()
            
            # Styling
            symbol = QgsMarkerSymbol.createSimple({
                'name': 'star',
                'color': 'red',
                'size': '8',
                'outline_color': 'black',
                'outline_width': '1'
            })
            layer.renderer().setSymbol(symbol)
            
            return layer
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Center layer error: {str(e)}", level=Qgis.Critical)
            return None
    
    def create_poi_layer(self, district_name, pois_data):
        """Erstelle POI-Layer"""
        
        try:
            layer_name = f"Walkability_POIs_{district_name}"
            layer = QgsVectorLayer("Point?crs=EPSG:4326", layer_name, "memory")
            
            # Felder hinzufügen
            layer.dataProvider().addAttributes([
                {'name': 'name', 'type': QVariant.String},
                {'name': 'service_type', 'type': QVariant.String},
                {'name': 'osm_type', 'type': QVariant.String},
                {'name': 'osm_id', 'type': QVariant.String}
            ])
            layer.updateFields()
            
            # Features erstellen
            features = []
            for service_type, pois in pois_data.items():
                for poi in pois:
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(poi['lon'], poi['lat']))
                    feature.setAttributes([
                        poi['name'],
                        service_type,
                        poi['osm_type'],
                        str(poi['id'])
                    ])
                    features.append(feature)
            
            layer.dataProvider().addFeatures(features)
            layer.updateExtents()
            
            # Kategorisierte Symbolisierung nach Service-Typ
            self.apply_poi_categorized_renderer(layer)
            
            return layer
            
        except Exception as e:
            QgsMessageLog.logMessage(f"POI layer error: {str(e)}", level=Qgis.Critical)
            return None
    
    def apply_poi_categorized_renderer(self, layer):
        """Wende kategorisierte Symbolisierung auf POI-Layer an"""
        
        try:
            # Service-Typ Farben
            colors = {
                'Supermarkt': QColor(34, 139, 34),    # Forest Green
                'Apotheke': QColor(220, 20, 60),      # Crimson Red
                'Arzt': QColor(65, 105, 225),         # Royal Blue
                'Schule': QColor(255, 140, 0),        # Dark Orange
                'Restaurant': QColor(138, 43, 226),    # Blue Violet
                'Bank': QColor(184, 134, 11)          # Dark Goldenrod
            }
            
            # Kategorien erstellen
            categories = []
            for service_type, color in colors.items():
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle',
                    'color': color.name(),
                    'size': '6',
                    'outline_color': 'black',
                    'outline_width': '0.5'
                })
                category = QgsRendererCategory(service_type, symbol, service_type)
                categories.append(category)
            
            # Renderer erstellen und anwenden
            renderer = QgsCategorizedSymbolRenderer('service_type', categories)
            layer.setRenderer(renderer)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"POI renderer error: {str(e)}", level=Qgis.Warning)
    
    def add_layers_to_project(self, layers):
        """Füge Layer zum QGIS-Projekt hinzu"""
        
        try:
            project = QgsProject.instance()
            
            # Layer-Reihenfolge: POIs, Zentrum, Isochrone (von oben nach unten)
            layer_order = ['pois', 'center', 'isochrone']
            
            for layer_key in layer_order:
                if layer_key in layers:
                    layer = layers[layer_key]
                    project.addMapLayer(layer)
                    QgsMessageLog.logMessage(f"Added layer: {layer.name()}", level=Qgis.Info)
            
            # Zoom zu allen Layern
            if layers:
                # Nehme Isochrone-Layer als Extent-Basis
                if 'isochrone' in layers:
                    extent = layers['isochrone'].extent()
                    project.instance().mapCanvas().setExtent(extent)
                    project.instance().mapCanvas().refresh()
                    
        except Exception as e:
            QgsMessageLog.logMessage(f"Add layers error: {str(e)}", level=Qgis.Critical)


# Factory-Funktion für den Dialog
def get_walkability_analyzer():
    """Factory-Funktion für WalkabilityAnalyzer"""
    return WalkabilityAnalyzer()