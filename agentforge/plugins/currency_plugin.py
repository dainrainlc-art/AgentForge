"""插件系统 - 汇率转换插件."""

import aiohttp
from datetime import datetime

from loguru import logger

from agentforge.core.plugin_base import ActionPlugin


class CurrencyPlugin(ActionPlugin):
    """汇率转换插件."""

    name = "currency"
    version = "1.0.0"
    description = "货币汇率转换"
    author = "System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.api_key = self.get_config("api_key", "")
        self.base_url = "https://api.exchangerate-api.com/v4"
        self._cache = {}
        self._cache_time = None

    async def initialize(self):
        """初始化插件."""
        self.enable()
        logger.info("汇率转换插件已初始化")

    async def shutdown(self):
        """关闭插件."""
        self.disable()
        self._cache.clear()
        logger.info("汇率转换插件已关闭")

    def get_capabilities(self) -> list[str]:
        """返回插件能力."""
        return ["action", "currency_conversion"]

    async def execute(self, params: dict, context=None) -> dict:
        """执行汇率转换."""
        amount = params.get("amount", 1)
        from_currency = params.get("from", "USD")
        to_currency = params.get("to", "CNY")

        return await self.convert_currency(amount, from_currency, to_currency)

    async def convert_currency(
        self, amount: float, from_currency: str, to_currency: str
    ) -> dict:
        """转换货币."""
        try:
            # 获取汇率
            rate = await self._get_exchange_rate(from_currency, to_currency)

            if "error" in rate:
                return rate

            converted_amount = amount * rate["rate"]

            return {
                "from": from_currency,
                "to": to_currency,
                "amount": amount,
                "converted_amount": round(converted_amount, 2),
                "rate": rate["rate"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"汇率转换失败：{str(e)}")
            return {"error": str(e)}

    async def _get_exchange_rate(self, from_currency: str, to_currency: str) -> dict:
        """获取汇率."""
        # 检查缓存（1 小时内有效）
        cache_key = f"{from_currency}_{to_currency}"
        if (
            cache_key in self._cache
            and self._cache_time
            and (datetime.now() - self._cache_time).total_seconds() < 3600
        ):
            return {"rate": self._cache[cache_key]}

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/latest/{from_currency}"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})

                        if to_currency in rates:
                            rate = rates[to_currency]

                            # 更新缓存
                            self._cache[cache_key] = rate
                            self._cache_time = datetime.now()

                            return {"rate": rate}
                        else:
                            return {"error": f"不支持的货币：{to_currency}"}
                    else:
                        return {"error": f"查询失败：{response.status}"}

        except Exception as e:
            logger.error(f"获取汇率失败：{str(e)}")
            return {"error": str(e)}

    async def get_supported_currencies(self) -> list[str]:
        """获取支持的货币列表."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/latest/USD"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return list(data.get("rates", {}).keys())
        except Exception as e:
            logger.error(f"获取货币列表失败：{str(e)}")
            return []

    def validate_config(self) -> bool:
        """验证配置."""
        # 该插件不需要 API key
        return True
