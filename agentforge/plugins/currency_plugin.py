"""
Currency Plugin - 货币转换插件
Provides currency conversion and exchange rate information
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from loguru import logger

from .plugin_system import Plugin, PluginMetadata


class CurrencyPlugin(Plugin):
    """Currency conversion plugin with real-time exchange rates"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.get_config("api_key")
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Common currencies
        self.supported_currencies = [
            "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF",
            "HKD", "NZD", "SGD", "KRW", "INR", "RUB", "BRL", "ZAR"
        ]
        
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="currency",
            version="1.0.0",
            description="货币转换和汇率查询插件",
            author="AgentForge",
            tags=["currency", "finance", "conversion"],
            permissions=["http_request"]
        )
    
    @property
    def config_schema(self) -> Dict[str, Any]:
        return {
            "api_key": {
                "type": "string",
                "description": "Exchange Rate API Key (optional)",
                "required": False
            },
            "default_from": {
                "type": "string",
                "description": "默认源货币",
                "default": "USD"
            },
            "default_to": {
                "type": "string",
                "description": "默认目标货币",
                "default": "CNY"
            }
        }
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies"""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Check cache
        cache_key = f"rate_{from_currency}"
        if cache_key in self._cache:
            cached_time, rates = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl):
                if to_currency in rates:
                    return rates[to_currency]
        
        try:
            # Use free API (no key required for basic usage)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{from_currency}",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                rates = data.get("rates", {})
                
                # Cache rates
                self._cache[cache_key] = (datetime.now(), rates)
                
                if to_currency in rates:
                    return rates[to_currency]
                else:
                    raise ValueError(f"Currency {to_currency} not supported")
                    
        except Exception as e:
            logger.error(f"Failed to get exchange rate: {e}")
            raise
    
    async def convert(self, amount: float, from_currency: str = None, to_currency: str = None) -> Dict[str, Any]:
        """Convert amount from one currency to another"""
        from_currency = (from_currency or self.get_config("default_from", "USD")).upper()
        to_currency = (to_currency or self.get_config("default_to", "CNY")).upper()
        
        try:
            rate = await self.get_exchange_rate(from_currency, to_currency)
            converted_amount = amount * rate
            
            return {
                "from": {
                    "currency": from_currency,
                    "amount": amount
                },
                "to": {
                    "currency": to_currency,
                    "amount": round(converted_amount, 2)
                },
                "rate": rate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            return {"error": str(e)}
    
    async def get_all_rates(self, base_currency: str = "USD") -> Dict[str, Any]:
        """Get all exchange rates for a base currency"""
        base_currency = base_currency.upper()
        
        # Check cache
        cache_key = f"all_rates_{base_currency}"
        if cache_key in self._cache:
            cached_time, data = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl):
                return data
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{base_currency}",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                result = {
                    "base": base_currency,
                    "date": data.get("date"),
                    "rates": {k: v for k, v in data.get("rates", {}).items() if k in self.supported_currencies},
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache result
                self._cache[cache_key] = (datetime.now(), result)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get all rates: {e}")
            return {"error": str(e)}
    
    async def batch_convert(self, amounts: List[float], from_currency: str, to_currencies: List[str]) -> List[Dict[str, Any]]:
        """Convert multiple amounts to multiple currencies"""
        results = []
        
        for amount in amounts:
            for to_currency in to_currencies:
                result = await self.convert(amount, from_currency, to_currency)
                if "error" not in result:
                    results.append(result)
        
        return results
    
    def format_currency(self, amount: float, currency: str) -> str:
        """Format amount with currency symbol"""
        symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "CNY": "¥", "AUD": "A$", "CAD": "C$", "CHF": "Fr",
            "HKD": "HK$", "NZD": "NZ$", "SGD": "S$", "KRW": "₩",
            "INR": "₹", "RUB": "₽", "BRL": "R$", "ZAR": "R"
        }
        
        symbol = symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute plugin actions"""
        if action == "convert":
            return await self.convert(
                params.get("amount", 0),
                params.get("from"),
                params.get("to")
            )
        elif action == "rate":
            rate = await self.get_exchange_rate(
                params.get("from", "USD"),
                params.get("to", "CNY")
            )
            return {"rate": rate}
        elif action == "all_rates":
            return await self.get_all_rates(params.get("base", "USD"))
        elif action == "batch_convert":
            return await self.batch_convert(
                params.get("amounts", []),
                params.get("from", "USD"),
                params.get("to", ["CNY"])
            )
        else:
            raise ValueError(f"Unknown action: {action}")
