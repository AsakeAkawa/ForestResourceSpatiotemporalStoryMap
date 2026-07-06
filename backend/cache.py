"""
In-memory cache for raw computation results.
Keys: (indicator, year, year2) → (data_array, bounds_dict)
"""
_cache = {}

def get(key):
    return _cache.get(key)

def set(key, data, bounds):
    _cache[key] = (data.copy(), bounds.copy())
    # Keep only last 10 entries
    if len(_cache) > 10:
        oldest = next(iter(_cache))
        del _cache[oldest]
