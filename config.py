# config.py - Konfigurationsdatei

# OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf6248c3f28f7b4dcb48a8817a2dd37711fb8a"  # Kostenlos von openrouteservice.org

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
    "Wolbeck": [51.9000000, 7.7500000]
}

# Service-Kategorien für die Analyse
SERVICE_CATEGORIES = {
    "Supermarkt": {"weight": 0.25, "min_count": 1},
    "Apotheke": {"weight": 0.20, "min_count": 1},
    "Arzt": {"weight": 0.20, "min_count": 1},
    "Schule": {"weight": 0.15, "min_count": 1},
    "Restaurant": {"weight": 0.10, "min_count": 2},
    "Bank": {"weight": 0.10, "min_count": 1}
}

# Zeitlimits für Isochronen (in Minuten)
TIME_LIMITS = [5, 10, 15, 20]

# OpenRouteService URLs
ORS_BASE_URL = "https://api.openrouteservice.org/v2"
ORS_ISOCHRONE_URL = f"{ORS_BASE_URL}/isochrones/foot-walking"
ORS_DIRECTIONS_URL = f"{ORS_BASE_URL}/directions/foot-walking"