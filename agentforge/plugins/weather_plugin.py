"""
Weather Plugin - 天气查询插件
Provides weather information and forecasts
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger

from .plugin_system import Plugin, PluginMetadata, PluginConfig


class WeatherPlugin(Plugin):
    """Weather query plugin with forecast capabilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.get_config("api_key")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._cache = {}
        self._cache_ttl = 600  # 10 minutes
        
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="weather",
            version="1.0.0",
            description="天气查询和预报插件",
            author="AgentForge",
            tags=["weather", "forecast", "utility"],
            permissions=["http_request"]
        )
    
    @property
    def config_schema(self) -> Dict[str, Any]:
        return {
            "api_key": {
                "type": "string",
                "description": "OpenWeatherMap API Key",
                "required": True
            },
            "default_city": {
                "type": "string",
                "description": "默认城市",
                "default": "Beijing"
            },
            "units": {
                "type": "string",
                "description": "温度单位 (metric/imperial)",
                "default": "metric",
                "enum": ["metric", "imperial"]
            }
        }
    
    async def get_current_weather(self, city: str = None) -> Dict[str, Any]:
        """Get current weather for a city"""
        city = city or self.get_config("default_city", "Beijing")
        
        # Check cache
        cache_key = f"current_{city}"
        if cache_key in self._cache:
            cached_time, data = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl):
                return data
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": self.get_config("units", "metric"),
                        "lang": "zh_cn"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                result = {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "weather": data["weather"][0]["description"],
                    "weather_main": data["weather"][0]["main"],
                    "icon": data["weather"][0]["icon"],
                    "wind_speed": data["wind"]["speed"],
                    "visibility": data.get("visibility", 0),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache result
                self._cache[cache_key] = (datetime.now(), result)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get weather for {city}: {e}")
            return {"error": str(e)}
    
    async def get_forecast(self, city: str = None, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for a city"""
        city = city or self.get_config("default_city", "Beijing")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": self.get_config("units", "metric"),
                        "lang": "zh_cn",
                        "cnt": days * 8  # 3-hour intervals
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Group by day
                daily_forecast = {}
                for item in data["list"]:
                    date = item["dt_txt"].split()[0]
                    if date not in daily_forecast:
                        daily_forecast[date] = {
                            "temps": [],
                            "weather": [],
                            "icons": []
                        }
                    daily_forecast[date]["temps"].append(item["main"]["temp"])
                    daily_forecast[date]["weather"].append(item["weather"][0]["description"])
                    daily_forecast[date]["icons"].append(item["weather"][0]["icon"])
                
                # Format result
                forecast = []
                for date, info in list(daily_forecast.items())[:days]:
                    forecast.append({
                        "date": date,
                        "temp_min": min(info["temps"]),
                        "temp_max": max(info["temps"]),
                        "temp_avg": sum(info["temps"]) / len(info["temps"]),
                        "weather": max(set(info["weather"]), key=info["weather"].count),
                        "icon": info["icons"][len(info["icons"])//2]
                    })
                
                return {
                    "city": data["city"]["name"],
                    "country": data["city"]["country"],
                    "forecast": forecast
                }
                
        except Exception as e:
            logger.error(f"Failed to get forecast for {city}: {e}")
            return {"error": str(e)}
    
    async def get_travel_suggestion(self, city: str = None) -> str:
        """Get travel suggestion based on weather"""
        weather = await self.get_current_weather(city)
        
        if "error" in weather:
            return f"无法获取天气信息: {weather['error']}"
        
        temp = weather["temperature"]
        condition = weather["weather_main"]
        
        suggestions = []
        
        # Temperature-based suggestions
        if temp < 0:
            suggestions.append("❄️ 天气寒冷，请穿厚外套，注意保暖")
        elif temp < 15:
            suggestions.append("🧥 天气较凉，建议穿长袖或薄外套")
        elif temp < 25:
            suggestions.append("👕 天气舒适，适合户外活动")
        else:
            suggestions.append("☀️ 天气炎热，注意防晒和补水")
        
        # Weather condition suggestions
        if condition in ["Rain", "Drizzle"]:
            suggestions.append("🌧️ 有雨，记得带伞")
        elif condition == "Snow":
            suggestions.append("🌨️ 有雪，注意防滑")
        elif condition == "Thunderstorm":
            suggestions.append("⛈️ 雷雨天气，尽量避免户外活动")
        elif condition == "Clear":
            suggestions.append("☀️ 晴朗天气，适合出行")
        elif condition == "Clouds":
            suggestions.append("☁️ 多云天气，比较舒适")
        
        # Wind suggestion
        if weather.get("wind_speed", 0) > 10:
            suggestions.append("💨 风力较大，注意防风")
        
        return "\n".join(suggestions)
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute plugin actions"""
        if action == "current":
            return await self.get_current_weather(params.get("city"))
        elif action == "forecast":
            return await self.get_forecast(
                params.get("city"),
                params.get("days", 5)
            )
        elif action == "suggestion":
            return await self.get_travel_suggestion(params.get("city"))
        else:
            raise ValueError(f"Unknown action: {action}")
