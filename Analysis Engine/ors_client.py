# ors_client.py - OpenRouteService API Client

import requests
import json
from qgis.core import QgsMessageLog, Qgis
from .config import ORS_API_KEY, ORS_ISOCHRONE_URL, ORS_BASE_URL

class ORSClient:
    """OpenRouteService API Client für Isochrone und Routing"""
    
    def __init__(self):
        self.api_key = ORS_API_KEY
        self.base_url = ORS_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self):
        """Teste die Verbindung zur ORS API"""
        try:
            # Teste mit einer einfachen Isochrone-Anfrage für Münster Centrum
            test_coords = [7.6261347, 51.9606649]  # [lon, lat] für Münster
            
            response = self.session.post(
                ORS_ISOCHRONE_URL,
                json={
                    'locations': [test_coords],
                    'range': [300],  # 5 Minuten
                    'range_type': 'time'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                QgsMessageLog.logMessage("ORS Connection: OK", level=Qgis.Info)
                return True
            else:
                QgsMessageLog.logMessage(f"ORS Connection failed: {response.status_code}", level=Qgis.Warning)
                return False
                
        except Exception as e:
            QgsMessageLog.logMessage(f"ORS Connection error: {str(e)}", level=Qgis.Critical)
            return False
    
    def get_isochrone(self, coordinates, time_minutes):
        """
        Berechne Isochrone für gegebene Koordinaten und Zeit
        
        :param coordinates: [lon, lat]
        :param time_minutes: Zeit in Minuten
        :return: GeoJSON der Isochrone oder None
        """
        try:
            time_seconds = time_minutes * 60
            
            payload = {
                'locations': [coordinates],
                'range': [time_seconds],
                'range_type': 'time',
                'units': 'm'
            }
            
            QgsMessageLog.logMessage(f"ORS Request: {coordinates}, {time_minutes}min", level=Qgis.Info)
            
            response = self.session.post(
                ORS_ISOCHRONE_URL,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'features' in data and len(data['features']) > 0:
                    QgsMessageLog.logMessage("Isochrone successfully retrieved", level=Qgis.Info)
                    return data
                else:
                    QgsMessageLog.logMessage("No isochrone features found", level=Qgis.Warning)
                    return None
            else:
                error_msg = f"ORS API Error {response.status_code}: {response.text}"
                QgsMessageLog.logMessage(error_msg, level=Qgis.Critical)
                return None
                
        except requests.exceptions.Timeout:
            QgsMessageLog.logMessage("ORS API timeout", level=Qgis.Critical)
            return None
        except Exception as e:
            QgsMessageLog.logMessage(f"ORS API error: {str(e)}", level=Qgis.Critical)
            return None
    
    def get_multiple_isochrones(self, coordinates, time_minutes_list):
        """
        Berechne mehrere Isochronen für verschiedene Zeiten
        
        :param coordinates: [lon, lat]
        :param time_minutes_list: Liste von Zeiten in Minuten
        :return: Liste von GeoJSON Isochronen
        """
        results = []
        
        for time_min in time_minutes_list:
            isochrone = self.get_isochrone(coordinates, time_min)
            if isochrone:
                # Füge Zeit-Info zu den Properties hinzu
                for feature in isochrone['features']:
                    feature['properties']['time_minutes'] = time_min
                results.append(isochrone)
        
        return results
    
    def get_directions(self, start_coords, end_coords):
        """
        Berechne Route zwischen zwei Punkten
        
        :param start_coords: [lon, lat]
        :param end_coords: [lon, lat]
        :return: Routing-Ergebnis oder None
        """
        try:
            url = f"{ORS_BASE_URL}/directions/foot-walking"
            
            payload = {
                'coordinates': [start_coords, end_coords],
                'format': 'geojson',
                'instructions': False
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                QgsMessageLog.logMessage(f"Directions API Error: {response.status_code}", level=Qgis.Warning)
                return None
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Directions API error: {str(e)}", level=Qgis.Critical)
            return None