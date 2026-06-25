import logging

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        # District coordinate catalog (centered locations)
        self.districts = [
            {"name": "Dhaka", "lat": 23.8103, "lon": 90.4125},
            {"name": "Mymensingh", "lat": 24.7471, "lon": 90.4203},
            {"name": "Sylhet", "lat": 24.8949, "lon": 91.8687},
            {"name": "Rajshahi", "lat": 24.3745, "lon": 88.6042},
            {"name": "Rangpur", "lat": 25.7508, "lon": 89.2467},
            {"name": "Jessore", "lat": 23.1664, "lon": 89.2081},
            {"name": "Barisal", "lat": 22.7010, "lon": 90.3535},
            {"name": "Chittagong", "lat": 22.3569, "lon": 91.7832},
            {"name": "Dinajpur", "lat": 25.6217, "lon": 88.6354},
            {"name": "Bogra", "lat": 24.8481, "lon": 89.3730}
        ]

    def resolve_district(self, lat: float, lon: float) -> str:
        """
        Find the nearest district based on euclidean distance.
        """
        if lat is None or lon is None:
            return "Dhaka"
            
        try:
            nearest_district = "Dhaka"
            min_dist = float("inf")
            
            for dist in self.districts:
                dist_lat = dist["lat"]
                dist_lon = dist["lon"]
                
                # Simple distance calculation
                d = ((lat - dist_lat) ** 2 + (lon - dist_lon) ** 2) ** 0.5
                if d < min_dist:
                    min_dist = d
                    nearest_district = dist["name"]
                    
            logger.info(f"Resolved coordinates ({lat}, {lon}) to district: {nearest_district}")
            return nearest_district
        except Exception as e:
            logger.error(f"Error resolving coordinates: {e}")
            return "Dhaka"

    def get_coords_for_district(self, district_name: str) -> dict:
        """
        Get the center latitude and longitude for a district.
        """
        normalized = district_name.strip().lower()
        for dist in self.districts:
            if dist["name"].lower() == normalized:
                return {"lat": dist["lat"], "lon": dist["lon"]}
                
        # Default to Dhaka
        return {"lat": 23.8103, "lon": 90.4125}
