"""
Pure-Python Geographic Utilities for BloodBridge AI.
Includes Geohash encoding, neighbor computation, and Haversine distance calculations.
NO EXTERNAL DEPENDENCIES (e.g. geohash2).
"""
import math

# Standard base32 encoding character set for Geohash
__base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
__decodemap = {c: i for i, c in enumerate(__base32)}

# Neighbor mapping tables
__neighbors = {
    'right': { 'even': 'bc01fg45238967deuvhjyznpkmstqrwx', 'odd': 'p0r21436x8zb9dcf5h7kjnmqesgutwvy' },
    'left':  { 'even': '238967debc01fg45kmstqrwxuvhjyznp', 'odd': '14365h7k9dcfesgujnmqp0r2x8zbvytw' },
    'top':   { 'even': 'p0r21436x8zb9dcf5h7kjnmqesgutwvy', 'odd': 'bc01fg45238967deuvhjyznpkmstqrwx' },
    'bottom':{ 'even': '14365h7k9dcfesgujnmqp0r2x8zbvytw', 'odd': '238967debc01fg45kmstqrwxuvhjyznp' }
}

__borders = {
    'right': { 'even': 'bcfguvyz', 'odd': 'prxz' },
    'left':  { 'even': '0145hjnp', 'odd': '028b' },
    'top':   { 'even': 'prxz',     'odd': 'bcfguvyz' },
    'bottom':{ 'even': '028b',     'odd': '0145hjnp' }
}

def encode_geohash(lat: float, lng: float, precision: int = 6) -> str:
    """
    Encode a coordinate to a geohash.
    """
    lat_interval = [-90.0, 90.0]
    lng_interval = [-180.0, 180.0]
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True

    while len(geohash) < precision:
        if even:
            mid = (lng_interval[0] + lng_interval[1]) / 2
            if lng > mid:
                ch |= bits[bit]
                lng_interval[0] = mid
            else:
                lng_interval[1] = mid
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if lat > mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid

        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(__base32[ch])
            bit = 0
            ch = 0

    return "".join(geohash)

def _calculate_adjacent(geohash_str: str, direction: str) -> str:
    """
    Calculate the adjacent geohash in a given direction.
    """
    if not geohash_str:
        return ""
    
    geohash_str = geohash_str.lower()
    last_char = geohash_str[-1]
    parent = geohash_str[:-1]
    is_even = len(geohash_str) % 2 == 0
    type_str = 'even' if is_even else 'odd'

    if last_char in __borders[direction][type_str] and parent:
        parent = _calculate_adjacent(parent, direction)

    return parent + __base32[__neighbors[direction][type_str].index(last_char)]

def neighbors(geohash_str: str) -> list[str]:
    """
    Return the 8 adjacent neighbors of a geohash.
    Order: top, top-right, right, bottom-right, bottom, bottom-left, left, top-left
    """
    top = _calculate_adjacent(geohash_str, 'top')
    bottom = _calculate_adjacent(geohash_str, 'bottom')
    right = _calculate_adjacent(geohash_str, 'right')
    left = _calculate_adjacent(geohash_str, 'left')
    
    top_right = _calculate_adjacent(top, 'right')
    bottom_right = _calculate_adjacent(bottom, 'right')
    bottom_left = _calculate_adjacent(bottom, 'left')
    top_left = _calculate_adjacent(top, 'left')
    
    return [top, top_right, right, bottom_right, bottom, bottom_left, left, top_left]

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth surface in kilometers.
    """
    # Earth radius in kilometers
    R = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def radius_buckets() -> dict:
    """
    Returns the three radius tiers for matching.
    R1: Primary search area (highly likely to accept).
    R2: Secondary search area.
    R3: Tertiary / wide-net search area.
    """
    return {
        "R1": 5.0,  # km
        "R2": 15.0, # km
        "R3": 30.0  # km
    }
