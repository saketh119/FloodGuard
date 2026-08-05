"""
pipeline/enricher.py — Data Enrichment.

Normalizes district names and provides basic reverse-geocoding 
if coordinates are available but district/state are missing.
"""
import re
from typing import Optional

# Simple hardcoded lookup for demonstration.
# In a real system, this would use a spatial database or external geocoding API.
DISTRICT_ALIASES = {
    "kamrup metro": "Kamrup Metropolitan",
    "kamrup (m)": "Kamrup Metropolitan",
    "w godavari": "West Godavari",
}

# Very rough bounding boxes for demonstration
REGIONS = [
    {"state": "Assam", "district": "Kamrup Metropolitan", "bounds": (25.5, 91.0, 26.5, 92.5)},
    {"state": "Andhra Pradesh", "district": "NTR", "bounds": (16.0, 80.0, 17.0, 81.0)},
    {"state": "Andhra Pradesh", "district": "West Godavari", "bounds": (16.5, 81.0, 17.5, 82.0)},
    {"state": "Telangana", "district": "Hyderabad", "bounds": (17.0, 78.0, 17.8, 79.0)},
    {"state": "Kerala", "district": "Ernakulam", "bounds": (9.5, 76.0, 10.5, 77.0)},
    {"state": "Bihar", "district": "Patna", "bounds": (25.0, 84.5, 26.0, 86.0)},
]

class Enricher:
    @staticmethod
    def normalize_district(district: Optional[str]) -> Optional[str]:
        if not district:
            return None
        d = district.lower().strip()
        # Remove common suffixes
        d = re.sub(r'\s+district$', '', d)
        d = re.sub(r'\s+dist$', '', d)
        
        # Check aliases
        if d in DISTRICT_ALIASES:
            return DISTRICT_ALIASES[d]
            
        # Title case
        return district.title()
        
    @staticmethod
    def reverse_geocode(lat: Optional[float], lng: Optional[float]) -> tuple[Optional[str], Optional[str]]:
        """Returns (district, state) based on rough bounding boxes."""
        if lat is None or lng is None:
            return None, None
            
        for region in REGIONS:
            min_lat, min_lng, max_lat, max_lng = region["bounds"]
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                return region["district"], region["state"]
                
        return None, None
