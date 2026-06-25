class Weather:
    def __init__(self, temp=0.0, humidity=0, rainfall=0.0, wind_speed=0.0, description="Clear", forecast=None, raw_data=None):
        self.temp = float(temp)
        self.humidity = int(humidity)
        self.rainfall = float(rainfall)
        self.wind_speed = float(wind_speed)
        self.description = description or "Clear"
        self.forecast = forecast or []
        self.raw_data = raw_data or {}

    def to_dict(self):
        return {
            "temp": self.temp,
            "humidity": self.humidity,
            "rainfall": self.rainfall,
            "wind_speed": self.wind_speed,
            "description": self.description,
            "forecast": self.forecast,
            "raw_data": self.raw_data
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            temp=data.get("temp", 0.0),
            humidity=data.get("humidity", 0),
            rainfall=data.get("rainfall", 0.0),
            wind_speed=data.get("wind_speed", 0.0),
            description=data.get("description", "Clear"),
            forecast=data.get("forecast", []),
            raw_data=data.get("raw_data", {})
        )

    def validate(self):
        errors = {}
        if not (-50 <= self.temp <= 60):
            errors["temp"] = "Temperature is out of standard realistic range."
        if not (0 <= self.humidity <= 100):
            errors["humidity"] = "Humidity must be between 0 and 100."
        if self.rainfall < 0:
            errors["rainfall"] = "Rainfall cannot be negative."
        if self.wind_speed < 0:
            errors["wind_speed"] = "Wind speed cannot be negative."
        return len(errors) == 0, errors
