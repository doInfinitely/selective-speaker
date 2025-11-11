"""
Geocoding service for reverse geocoding GPS coordinates to addresses.

In production, integrate with Google Geocoding API or Mapbox.
"""

from typing import Optional, Tuple
import httpx


async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Convert GPS coordinates to a human-readable address.
    
    In production, this would call Google Geocoding API:
    https://maps.googleapis.com/maps/api/geocode/json?latlng=LAT,LON&key=API_KEY
    
    Or Mapbox Geocoding API:
    https://api.mapbox.com/geocoding/v5/mapbox.places/LON,LAT.json?access_token=TOKEN
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Formatted address string or None if geocoding fails
    """
    # TODO: Implement actual geocoding API call
    # Example with Google:
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(
    #         "https://maps.googleapis.com/maps/api/geocode/json",
    #         params={"latlng": f"{lat},{lon}", "key": GOOGLE_API_KEY}
    #     )
    #     data = response.json()
    #     if data.get("results"):
    #         return data["results"][0]["formatted_address"]
    #     return None
    
    # Dev stub: return coordinates as string
    return f"Lat {lat:.5f}, Lon {lon:.5f}"

