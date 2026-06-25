import re

class Farmer:
    def __init__(self, name=None, location=None, primary_crops=None, language_pref="bn"):
        self.name = name or "Bangladeshi Farmer"
        # location format: {"district": "Mymensingh", "lat": 24.7471, "lon": 90.4203}
        self.location = location or {"district": "Dhaka", "lat": 23.8103, "lon": 90.4125}
        self.primary_crops = primary_crops or []
        self.language_pref = language_pref or "bn"

    def to_dict(self):
        return {
            "name": self.name,
            "location": self.location,
            "primary_crops": self.primary_crops,
            "language_pref": self.language_pref
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            name=data.get("name"),
            location=data.get("location"),
            primary_crops=data.get("primary_crops"),
            language_pref=data.get("language_pref")
        )

    def validate(self):
        errors = {}
        if not self.name or len(self.name.strip()) < 2:
            errors["name"] = "Name must be at least 2 characters long."
            
        loc = self.location
        if not isinstance(loc, dict) or "district" not in loc:
            errors["location"] = "Location must include a district name."
        else:
            lat = loc.get("lat")
            lon = loc.get("lon")
            if lat is not None and not (-90 <= float(lat) <= 90):
                errors["location_lat"] = "Latitude must be between -90 and 90."
            if lon is not None and not (-180 <= float(lon) <= 180):
                errors["location_lon"] = "Longitude must be between -180 and 180."
                
        if self.language_pref not in ["bn", "en", "dialect"]:
            errors["language_pref"] = "Language preference must be 'bn', 'en', or 'dialect'."
            
        return len(errors) == 0, errors
