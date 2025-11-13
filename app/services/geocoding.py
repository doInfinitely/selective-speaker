"""
Geocoding service for reverse geocoding GPS coordinates to addresses.

Uses OpenStreetMap Nominatim for free geocoding (no API key required).
"""

from typing import Optional, Tuple
import httpx
from loguru import logger


async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Convert GPS coordinates to a human-readable address using OpenStreetMap Nominatim.
    
    Free service with no API key required. Please respect their usage policy:
    https://operations.osmfoundation.org/policies/nominatim/
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Formatted address string or None if geocoding fails
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "zoom": 18,  # Street-level detail
                },
                headers={
                    "User-Agent": "SelectiveSpeaker/1.0"  # Required by Nominatim usage policy
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Try to get structured address for better formatting
                address_data = data.get("address", {})
                
                # Build a clean address from structured data
                parts = []
                
                # Add house number and road together (no comma between them)
                house_number = address_data.get("house_number", "")
                road = address_data.get("road", "")
                if house_number and road:
                    parts.append(f"{house_number} {road}")
                elif road:
                    parts.append(road)
                
                # Add neighborhood or suburb if available
                neighborhood = address_data.get("neighbourhood") or address_data.get("suburb")
                if neighborhood:
                    parts.append(neighborhood)
                
                # Add city
                city = address_data.get("city") or address_data.get("town") or address_data.get("village")
                if city:
                    parts.append(city)
                
                # Add state/province
                state = address_data.get("state")
                if state:
                    parts.append(state)
                
                if parts:
                    address = ", ".join(parts[:3])  # Limit to 3 parts for brevity
                    logger.debug(f"Geocoded ({lat}, {lon}) -> {address}")
                    return address
                else:
                    # Fallback to display_name if structured data not available
                    display_name = data.get("display_name")
                    if display_name:
                        address_parts = display_name.split(", ")
                        address = ", ".join(address_parts[:3])
                        logger.debug(f"Geocoded ({lat}, {lon}) -> {address}")
                        return address
                    
                    logger.warning(f"No address found for ({lat}, {lon})")
                    return None
            else:
                logger.warning(f"Geocoding failed with status {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.warning(f"Geocoding timeout for ({lat}, {lon})")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for ({lat}, {lon}): {e}")
        return None

