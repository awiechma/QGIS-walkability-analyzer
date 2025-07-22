# overpass_client.py - OpenStreetMap POI Client über Overpass API

import requests
import json
from qgis.core import QgsMessageLog, Qgis
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj

class OverpassClient:
    """Client für Overpass API zum Abrufen von OpenStreetMap POIs"""
    
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.session = requests.Session()
        
        # Service-Mapping: Plugin-Name -> OSM-Tags
        self.service_mappings = {
            "Supermarkt": [
                "shop=supermarket",
                "shop=convenience", 
                "shop=grocery"
            ],
            "Apotheke": [
                "amenity=pharmacy"
            ],
            "Arzt": [
                "amenity=doctors",
                "amenity=clinic",
                "amenity=hospital",
                "healthcare=doctor"
            ],
            "Schule": [
                "amenity=school",
                "amenity=kindergarten"
            ],
            "Restaurant": [
                "amenity=restaurant",
                "amenity=fast_food",
                "amenity=cafe"
            ],
            "Bank": [
                "amenity=bank",
                "amenity=atm"
            ]
        }
    
    def create_overpass_query(self, bbox, service_types):
        """
        Erstelle Overpass-Abfrage für gegebene Bounding Box und Services
        
        :param bbox: [south, west, north, east]
        :param service_types: Liste der Service-Typen
        :return: Overpass QL Query String
        """
        
        # Basis-Query
        query = f"[out:json][timeout:25];\n(\n"
        
        # Für jeden Service-Typ
        for service_type in service_types:
            if service_type in self.service_mappings:
                for tag in self.service_mappings[service_type]:
                    # Nodes
                    query += f'  node["{tag}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});\n'
                    # Ways
                    query += f'  way["{tag}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});\n'
        
        query += ");\nout center meta;"
        
        return query
    
    def polygon_to_bbox(self, polygon_coords):
        """
        Konvertiere Polygon-Koordinaten zu Bounding Box
        
        :param polygon_coords: Liste von [lon, lat] Koordinaten
        :return: [south, west, north, east]
        """
        lons = [coord[0] for coord in polygon_coords]
        lats = [coord[1] for coord in polygon_coords]
        
        return [min(lats), min(lons), max(lats), max(lons)]
    
    def get_pois_in_area(self, isochrone_geojson, service_types):
        """
        Hole POIs innerhalb einer Isochrone
        
        :param isochrone_geojson: GeoJSON der Isochrone
        :param service_types: Liste der Service-Typen
        :return: Dictionary mit POIs pro Service-Typ
        """
        
        try:
            # Extrahiere Polygon aus Isochrone
            if 'features' not in isochrone_geojson or len(isochrone_geojson['features']) == 0:
                QgsMessageLog.logMessage("No isochrone features found", level=Qgis.Warning)
                return {}
            
            feature = isochrone_geojson['features'][0]
            if feature['geometry']['type'] != 'Polygon':
                QgsMessageLog.logMessage("Isochrone is not a polygon", level=Qgis.Warning)
                return {}
            
            coords = feature['geometry']['coordinates'][0]  # Äußerer Ring
            
            # Bounding Box berechnen
            bbox = self.polygon_to_bbox(coords)
            
            # Overpass-Query erstellen
            query = self.create_overpass_query(bbox, service_types)
            
            QgsMessageLog.logMessage(f"Overpass Query: {len(query)} chars", level=Qgis.Info)
            
            # Query ausführen
            response = self.session.post(
                self.base_url,
                data={'data': query},
                timeout=30
            )
            
            if response.status_code != 200:
                QgsMessageLog.logMessage(f"Overpass API Error: {response.status_code}", level=Qgis.Critical)
                return {}
            
            data = response.json()
            
            # POIs nach Service-Typ gruppieren
            results = {service_type: [] for service_type in service_types}
            
            # Polygon für Punkt-in-Polygon-Test erstellen
            polygon = Polygon(coords)
            
            # Elemente verarbeiten
            for element in data.get('elements', []):
                # Koordinaten extrahieren
                if element['type'] == 'node':
                    lat, lon = element['lat'], element['lon']
                elif element['type'] == 'way' and 'center' in element:
                    lat, lon = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                # Punkt-in-Polygon-Test
                point = Point(lon, lat)
                if not polygon.contains(point):
                    continue
                
                # Tags analysieren und Service-Typ bestimmen
                tags = element.get('tags', {})
                
                for service_type in service_types:
                    if service_type in self.service_mappings:
                        for mapping in self.service_mappings[service_type]:
                            key, value = mapping.split('=')
                            if key in tags and (tags[key] == value or value == "*"):
                                
                                poi = {
                                    'id': element['id'],
                                    'lat': lat,
                                    'lon': lon,
                                    'name': tags.get('name', 'Unbenannt'),
                                    'type': element['type'],
                                    'service_type': service_type,
                                    'osm_type': f"{key}={tags.get(key, 'unknown')}",
                                    'tags': tags
                                }
                                
                                results[service_type].append(poi)
                                break  # Nur einmal pro Service-Typ zählen
            
            # Zusammenfassung loggen
            total_pois = sum(len(pois) for pois in results.values())
            QgsMessageLog.logMessage(f"Found {total_pois} POIs total", level=Qgis.Info)
            
            for service_type, pois in results.items():
                QgsMessageLog.logMessage(f"  {service_type}: {len(pois)} POIs", level=Qgis.Info)
            
            return results
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Overpass query error: {str(e)}", level=Qgis.Critical)
            return {}
    
    def get_poi_details(self, poi_id, poi_type):
        """
        Hole detaillierte Informationen zu einem POI
        
        :param poi_id: OSM ID des POIs
        :param poi_type: 'node' oder 'way'
        :return: Detaillierte POI-Informationen
        """
        
        try:
            query = f"[out:json]; {poi_type}({poi_id}); out meta;"
            
            response = self.session.post(
                self.base_url,
                data={'data': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('elements'):
                    return data['elements'][0]
            
            return None
            
        except Exception as e:
            QgsMessageLog.logMessage(f"POI details error: {str(e)}", level=Qgis.Warning)
            return None