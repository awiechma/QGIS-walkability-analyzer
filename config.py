# config.py - Erweiterte Konfigurationsdatei

# OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf6248c3f28f7b4dcb48a8817a2dd37711fb8a"  

# Münster Stadtteile (Name: [lat, lon])
MUENSTER_DISTRICTS = {
    "Centrum": [51.9606649, 7.6261347],
    "Hiltrup": [51.8833333, 7.6333333],
    "Kinderhaus": [51.9833333, 7.6166667],
    "Gievenbeck": [51.9500000, 7.5833333],
    "Mauritz": [51.9666667, 7.6500000],
    "Roxel": [51.9333333, 7.5166667],
    "Albachten": [51.9000000, 7.5333333],
    "Gremmendorf": [51.9333333, 7.7000000],
    "Angelmodde": [51.9000000, 7.7000000],
    "Wolbeck": [51.9000000, 7.7500000],
    "Berg Fidel": [51.9333333, 7.6500000],
    "Coerde": [52.0000000, 7.6000000],
    "Handorf": [51.9666667, 7.7833333],
    "Amelsbüren": [51.8833333, 7.5000000],
    "Sprakel": [52.0166667, 7.5833333]
}

# Service-Kategorien für die Analyse
SERVICE_CATEGORIES = {
    "Supermarkt": {"weight": 0.25, "min_count": 1, "icon": "🛒"},
    "Apotheke": {"weight": 0.20, "min_count": 1, "icon": "💊"},
    "Arzt": {"weight": 0.20, "min_count": 1, "icon": "🏥"},
    "Schule": {"weight": 0.15, "min_count": 1, "icon": "🎓"},
    "Restaurant": {"weight": 0.10, "min_count": 2, "icon": "🍽️"},
    "Bank": {"weight": 0.10, "min_count": 1, "icon": "🏦"}
}

# Erweiterte Service-Kategorien (optional verfügbar)
EXTENDED_SERVICE_CATEGORIES = {
    "ÖPNV": {"weight": 0.15, "min_count": 2, "icon": "🚌"},
    "Spielplatz": {"weight": 0.05, "min_count": 1, "icon": "🛝"},
    "Park": {"weight": 0.05, "min_count": 1, "icon": "🌳"},
    "Bäckerei": {"weight": 0.05, "min_count": 1, "icon": "🥖"},
    "Post": {"weight": 0.05, "min_count": 1, "icon": "📮"},
    "Tankstelle": {"weight": 0.05, "min_count": 1, "icon": "⛽"}
}

# Zeitlimits für Isochronen (in Minuten)
TIME_LIMITS = [5, 10, 15, 20]
DEFAULT_TIME_LIMIT = 15

# OpenRouteService URLs
ORS_BASE_URL = "https://api.openrouteservice.org/v2"
ORS_ISOCHRONE_URL = f"{ORS_BASE_URL}/isochrones/foot-walking"
ORS_DIRECTIONS_URL = f"{ORS_BASE_URL}/directions/foot-walking"
ORS_GEOCODE_URL = f"{ORS_BASE_URL}/geocode/search"

# Nominatim für Geocoding (Backup)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Münster Bounding Box für Validierung [south, west, north, east]
MUENSTER_BBOX = [51.8, 7.4, 52.1, 7.8]

# Analysis Settings
MAX_ANALYSIS_TIME = 60  # Sekunden
DEFAULT_CRS = "EPSG:4326"
TEMP_LAYER_PREFIX = "Walkability_"

# PDF Export Settings
PDF_PAGE_SIZE = "A4"
PDF_MARGIN = 2  # cm
PDF_TITLE = "Walkability-Analyse Münster"

# Styling Configurations
LAYER_STYLES = {
    'isochrone': {
        'color': '70,130,180,100',
        'outline_color': '30,80,120,255',
        'outline_width': '2'
    },
    'center': {
        'symbol': 'star',
        'color': 'red',
        'size': '8',
        'outline_color': 'black'
    },
    'pois': {
        'Supermarkt': '#228B22',    # Forest Green
        'Apotheke': '#DC143C',      # Crimson Red
        'Arzt': '#4169E1',          # Royal Blue
        'Schule': '#FF8C00',        # Dark Orange
        'Restaurant': '#8A2BE2',     # Blue Violet
        'Bank': '#B8860B'           # Dark Goldenrod
    }
}

# Validation Settings
MIN_COORDINATE_PRECISION = 4  # Decimal places
COORDINATE_BOUNDS = {
    'lat_min': -90,
    'lat_max': 90,
    'lon_min': -180,
    'lon_max': 180
}

# Required Python packages
REQUIRED_PACKAGES = [
    'requests',
    'shapely',
    'reportlab',  # für PDF export
    'pyproj'      # für Koordinatentransformationen
]

# Hilfsfunktionen
def is_valid_coordinate(lat, lon):
    """Validiere Koordinaten"""
    try:
        lat = float(lat)
        lon = float(lon)
        
        if not (COORDINATE_BOUNDS['lat_min'] <= lat <= COORDINATE_BOUNDS['lat_max']):
            return False
        if not (COORDINATE_BOUNDS['lon_min'] <= lon <= COORDINATE_BOUNDS['lon_max']):
            return False
            
        return True
    except (ValueError, TypeError):
        return False

def is_in_muenster_area(lat, lon):
    """Prüfe ob Koordinaten im Münster-Bereich liegen"""
    try:
        lat = float(lat)
        lon = float(lon)
        
        return (MUENSTER_BBOX[0] <= lat <= MUENSTER_BBOX[2] and 
                MUENSTER_BBOX[1] <= lon <= MUENSTER_BBOX[3])
    except (ValueError, TypeError):
        return False

def get_service_icon(service_type):
    """Hole Icon für Service-Typ"""
    if service_type in SERVICE_CATEGORIES:
        return SERVICE_CATEGORIES[service_type].get('icon', '📍')
    elif service_type in EXTENDED_SERVICE_CATEGORIES:
        return EXTENDED_SERVICE_CATEGORIES[service_type].get('icon', '📍')
    else:
        return '📍'