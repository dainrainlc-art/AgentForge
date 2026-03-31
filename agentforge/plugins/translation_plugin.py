"""插件系统 - 翻译插件."""

import aiohttp
from loguru import logger

from agentforge.core.plugin_base import ActionPlugin


class TranslationPlugin(ActionPlugin):
    """翻译插件."""

    name = "translation"
    version = "1.0.0"
    description = "多语言翻译"
    author = "System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.api_key = self.get_config("api_key", "")
        self.secret_key = self.get_config("secret_key", "")
        self.base_url = "https://fanyi-api.baidu.com/api/translate/v2"

    async def initialize(self):
        """初始化插件."""
        if not self.api_key or not self.secret_key:
            logger.warning("翻译插件未配置 API key 或 secret key")
        self.enable()
        logger.info("翻译插件已初始化")

    async def shutdown(self):
        """关闭插件."""
        self.disable()
        logger.info("翻译插件已关闭")

    def get_capabilities(self) -> list[str]:
        """返回插件能力."""
        return ["action", "translation"]

    async def execute(self, params: dict, context=None) -> dict:
        """执行翻译."""
        text = params.get("text", "")
        from_lang = params.get("from", "auto")
        to_lang = params.get("to", "en")

        if not text:
            raise ValueError("必须指定要翻译的文本")

        return await self.translate(text, from_lang, to_lang)

    async def translate(
        self, text: str, from_lang: str = "auto", to_lang: str = "en"
    ) -> dict:
        """翻译文本."""
        if not self.api_key or not self.secret_key:
            return {
                "error": "未配置翻译 API",
                "message": "请在配置中添加 api_key 和 secret_key",
                "text": text,
            }

        try:
            import hashlib
            import random
            import time

            # 生成签名
            salt = str(random.randint(32768, 65536))
            sign_str = f"{self.api_key}{text}{salt}{self.secret_key}"
            sign = hashlib.md5(sign_str.encode(), usedforsecurity=False).hexdigest()

            params = {
                "q": text,
                "from": from_lang,
                "to": to_lang,
                "appid": self.api_key,
                "salt": salt,
                "sign": sign,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "trans_result" in data:
                            result = data["trans_result"]
                            return {
                                "from": from_lang,
                                "to": to_lang,
                                "original": text,
                                "translation": "\n".join([item["dst"] for item in result]),
                                "timestamp": time.time(),
                            }
                        else:
                            return {
                                "error": data.get("error_msg", "翻译失败"),
                            }
                    else:
                        return {"error": f"请求失败：{response.status}"}

        except Exception as e:
            logger.error(f"翻译失败：{str(e)}")
            return {"error": str(e)}

    async def detect_language(self, text: str) -> str:
        """检测语言（简化版）."""
        # 简单的语言检测
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            return "zh"
        elif any(c.isalpha() and ord(c) > 127 for c in text):
            return "ja"  # 日文
        else:
            return "en"  # 默认英文

    def validate_config(self) -> bool:
        """验证配置."""
        # api_key 和 secret_key 是可选的
        return True
