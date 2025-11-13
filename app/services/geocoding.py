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
                
                # Try to get a concise address
                address = data.get("display_name")
                if address:
                    # Nominatim returns very long addresses, let's shorten them
                    # Example: "123 Main St, City, County, State, Country"
                    parts = address.split(", ")
                    
                    # Take the first 3-4 most relevant parts
                    if len(parts) > 4:
                        address = ", ".join(parts[:4])
                    
                    logger.debug(f"Geocoded ({lat}, {lon}) -> {address}")
                    return address
                else:
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

