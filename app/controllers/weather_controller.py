from flask import Blueprint, request, jsonify
from app.services.weather_service import WeatherService
from app.services.location_service import LocationService

weather_bp = Blueprint("weather", __name__)
weather_service = WeatherService()
location_service = LocationService()

@weather_bp.route("/api/weather", methods=["GET"])
def get_weather():
    """
    Fetch weather based on GPS coordinates or manual district name.
    """
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    district = request.args.get("district", type=str)
    
    try:
        if lat is not None and lon is not None:
            # Resolve district name for visual reporting
            resolved_district = location_service.resolve_district(lat, lon)
            weather_model = weather_service.get_weather_by_coords(lat, lon)
            
            # Augment weather data with resolved district name
            weather_dict = weather_model.to_dict()
            weather_dict["resolved_district"] = resolved_district
            return jsonify(weather_dict), 200
            
        elif district:
            coords = location_service.get_coords_for_district(district)
            weather_model = weather_service.get_weather_by_district(district)
            
            weather_dict = weather_model.to_dict()
            weather_dict["resolved_district"] = district.capitalize()
            return jsonify(weather_dict), 200
            
        else:
            # Default to Dhaka if no parameters
            weather_model = weather_service.get_weather_by_district("Dhaka")
            weather_dict = weather_model.to_dict()
            weather_dict["resolved_district"] = "Dhaka"
            return jsonify(weather_dict), 200
            
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve weather context: {str(e)}"}), 500
