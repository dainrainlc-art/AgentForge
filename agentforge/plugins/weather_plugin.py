"""插件系统 - 天气查询插件."""

import aiohttp
from loguru import logger

from agentforge.core.plugin_base import ActionPlugin


class WeatherPlugin(ActionPlugin):
    """天气查询插件."""

    name = "weather"
    version = "1.0.0"
    description = "查询天气预报"
    author = "System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.api_key = self.get_config("api_key", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def initialize(self):
        """初始化插件."""
        if not self.api_key:
            logger.warning("天气插件未配置 API key")
        self.enable()
        logger.info("天气查询插件已初始化")

    async def shutdown(self):
        """关闭插件."""
        self.disable()
        logger.info("天气查询插件已关闭")

    def get_capabilities(self) -> list[str]:
        """返回插件能力."""
        return ["action", "weather_query"]

    async def execute(self, params: dict, context=None) -> dict:
        """执行天气查询."""
        city = params.get("city")
        days = params.get("days", 1)

        if not city:
            raise ValueError("必须指定城市名称")

        return await self.query_weather(city, days)

    async def query_weather(self, city: str, days: int = 1) -> dict:
        """查询天气."""
        if not self.api_key:
            return {
                "error": "未配置天气 API key",
                "city": city,
                "message": "请在配置中添加 api_key",
            }

        try:
            async with aiohttp.ClientSession() as session:
                # 当前天气
                url = f"{self.base_url}/weather"
                params = {
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_weather_data(data)
                    else:
                        return {"error": f"查询失败：{response.status}"}

        except Exception as e:
            logger.error(f"天气查询失败：{str(e)}")
            return {"error": str(e)}

    def _format_weather_data(self, data: dict) -> dict:
        """格式化天气数据."""
        return {
            "city": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "wind_speed": data.get("wind", {}).get("speed"),
        }

    def validate_config(self) -> bool:
        """验证配置."""
        # api_key 是可选的，但建议使用
        return True
