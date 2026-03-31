"""
AgentForge Internationalization (i18n) Module
多语言支持框架
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json
import os
from loguru import logger

from agentforge.config import settings


class Language(str, Enum):
    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    EN_US = "en-US"
    EN_GB = "en-GB"
    JA_JP = "ja-JP"
    KO_KR = "ko-KR"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    PT_BR = "pt-BR"


DEFAULT_LANGUAGE = Language.ZH_CN


class TranslationEntry(BaseModel):
    key: str
    value: str
    context: Optional[str] = None
    plural: Optional[Dict[str, str]] = None


class LocaleConfig(BaseModel):
    language: Language
    name: str
    native_name: str
    rtl: bool = False
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    currency: str = "USD"
    currency_symbol: str = "$"
    decimal_separator: str = "."
    thousands_separator: str = ","


LOCALE_CONFIGS: Dict[Language, LocaleConfig] = {
    Language.ZH_CN: LocaleConfig(
        language=Language.ZH_CN,
        name="Chinese Simplified",
        native_name="简体中文",
        date_format="%Y年%m月%d日",
        time_format="%H:%M",
        currency="CNY",
        currency_symbol="¥"
    ),
    Language.ZH_TW: LocaleConfig(
        language=Language.ZH_TW,
        name="Chinese Traditional",
        native_name="繁體中文",
        date_format="%Y年%m月%d日",
        time_format="%H:%M",
        currency="TWD",
        currency_symbol="NT$"
    ),
    Language.EN_US: LocaleConfig(
        language=Language.EN_US,
        name="English (US)",
        native_name="English (US)",
        date_format="%m/%d/%Y",
        time_format="%I:%M %p",
        currency="USD",
        currency_symbol="$"
    ),
    Language.EN_GB: LocaleConfig(
        language=Language.EN_GB,
        name="English (UK)",
        native_name="English (UK)",
        date_format="%d/%m/%Y",
        time_format="%H:%M",
        currency="GBP",
        currency_symbol="£"
    ),
    Language.JA_JP: LocaleConfig(
        language=Language.JA_JP,
        name="Japanese",
        native_name="日本語",
        date_format="%Y年%m月%d日",
        time_format="%H:%M",
        currency="JPY",
        currency_symbol="¥"
    ),
    Language.KO_KR: LocaleConfig(
        language=Language.KO_KR,
        name="Korean",
        native_name="한국어",
        date_format="%Y.%m.%d",
        time_format="%H:%M",
        currency="KRW",
        currency_symbol="₩"
    ),
    Language.ES_ES: LocaleConfig(
        language=Language.ES_ES,
        name="Spanish",
        native_name="Español",
        date_format="%d/%m/%Y",
        time_format="%H:%M",
        currency="EUR",
        currency_symbol="€"
    ),
    Language.FR_FR: LocaleConfig(
        language=Language.FR_FR,
        name="French",
        native_name="Français",
        date_format="%d/%m/%Y",
        time_format="%H:%M",
        currency="EUR",
        currency_symbol="€"
    ),
    Language.DE_DE: LocaleConfig(
        language=Language.DE_DE,
        name="German",
        native_name="Deutsch",
        date_format="%d.%m.%Y",
        time_format="%H:%M",
        currency="EUR",
        currency_symbol="€"
    ),
    Language.PT_BR: LocaleConfig(
        language=Language.PT_BR,
        name="Portuguese (Brazil)",
        native_name="Português (Brasil)",
        date_format="%d/%m/%Y",
        time_format="%H:%M",
        currency="BRL",
        currency_symbol="R$"
    ),
}


DEFAULT_TRANSLATIONS: Dict[Language, Dict[str, str]] = {
    Language.ZH_CN: {
        "app.name": "AgentForge",
        "app.tagline": "AI驱动的个人助理系统",
        "common.save": "保存",
        "common.cancel": "取消",
        "common.delete": "删除",
        "common.edit": "编辑",
        "common.create": "创建",
        "common.search": "搜索",
        "common.loading": "加载中...",
        "common.success": "操作成功",
        "common.error": "操作失败",
        "common.confirm": "确认",
        "common.back": "返回",
        "common.next": "下一步",
        "common.previous": "上一步",
        "nav.dashboard": "仪表盘",
        "nav.fiverr": "Fiverr运营",
        "nav.social": "社交媒体",
        "nav.knowledge": "知识管理",
        "nav.settings": "设置",
        "fiverr.orders": "订单管理",
        "fiverr.messages": "消息中心",
        "fiverr.quotation": "报价建议",
        "fiverr.analytics": "数据分析",
        "social.posts": "内容发布",
        "social.scheduler": "定时发布",
        "social.analytics": "社媒分析",
        "social.platforms": "平台管理",
        "knowledge.notes": "笔记",
        "knowledge.sync": "同步",
        "knowledge.search": "搜索知识库",
        "settings.profile": "个人资料",
        "settings.notifications": "通知设置",
        "settings.integrations": "集成配置",
        "settings.api_keys": "API密钥",
        "audit.title": "AI内容审核",
        "audit.pending": "待审核",
        "audit.approved": "已通过",
        "audit.rejected": "已驳回",
        "audit.approve": "通过",
        "audit.reject": "驳回",
        "audit.regenerate": "重新生成",
        "errors.not_found": "未找到请求的资源",
        "errors.unauthorized": "未授权访问",
        "errors.server_error": "服务器内部错误",
        "errors.network_error": "网络连接失败",
        "messages.welcome": "欢迎使用AgentForge",
        "messages.goodbye": "感谢使用，再见！",
    },
    Language.EN_US: {
        "app.name": "AgentForge",
        "app.tagline": "AI-Powered Personal Assistant System",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.delete": "Delete",
        "common.edit": "Edit",
        "common.create": "Create",
        "common.search": "Search",
        "common.loading": "Loading...",
        "common.success": "Success",
        "common.error": "Error",
        "common.confirm": "Confirm",
        "common.back": "Back",
        "common.next": "Next",
        "common.previous": "Previous",
        "nav.dashboard": "Dashboard",
        "nav.fiverr": "Fiverr Operations",
        "nav.social": "Social Media",
        "nav.knowledge": "Knowledge",
        "nav.settings": "Settings",
        "fiverr.orders": "Orders",
        "fiverr.messages": "Messages",
        "fiverr.quotation": "Quotations",
        "fiverr.analytics": "Analytics",
        "social.posts": "Posts",
        "social.scheduler": "Scheduler",
        "social.analytics": "Analytics",
        "social.platforms": "Platforms",
        "knowledge.notes": "Notes",
        "knowledge.sync": "Sync",
        "knowledge.search": "Search Knowledge",
        "settings.profile": "Profile",
        "settings.notifications": "Notifications",
        "settings.integrations": "Integrations",
        "settings.api_keys": "API Keys",
        "audit.title": "AI Content Audit",
        "audit.pending": "Pending",
        "audit.approved": "Approved",
        "audit.rejected": "Rejected",
        "audit.approve": "Approve",
        "audit.reject": "Reject",
        "audit.regenerate": "Regenerate",
        "errors.not_found": "Resource not found",
        "errors.unauthorized": "Unauthorized access",
        "errors.server_error": "Internal server error",
        "errors.network_error": "Network connection failed",
        "messages.welcome": "Welcome to AgentForge",
        "messages.goodbye": "Thank you for using AgentForge!",
    },
}


class Translator:
    def __init__(
        self,
        default_language: Language = DEFAULT_LANGUAGE,
        translations_path: Optional[str] = None
    ):
        self.default_language = default_language
        self.current_language = default_language
        self.translations_path = Path(translations_path or getattr(settings, 'translations_path', 'data/translations'))
        
        self._translations: Dict[Language, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self):
        for lang in Language:
            self._translations[lang] = DEFAULT_TRANSLATIONS.get(lang, {}).copy()
        
        if self.translations_path.exists():
            for lang_file in self.translations_path.glob("*.json"):
                try:
                    lang_code = lang_file.stem
                    lang = Language(lang_code)
                    
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        custom_translations = json.load(f)
                    
                    self._translations[lang].update(custom_translations)
                    logger.info(f"Loaded custom translations for {lang_code}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load translations from {lang_file}: {e}")
    
    def set_language(self, language: Language):
        self.current_language = language
        logger.info(f"Language set to {language.value}")
    
    def get_language(self) -> Language:
        return self.current_language
    
    def t(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        lang = language or self.current_language
        
        translations = self._translations.get(lang, {})
        text = translations.get(key)
        
        if text is None:
            default_translations = self._translations.get(self.default_language, {})
            text = default_translations.get(key, key)
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        
        return text
    
    def plural(
        self,
        key: str,
        count: int,
        language: Optional[Language] = None
    ) -> str:
        lang = language or self.current_language
        
        translations = self._translations.get(lang, {})
        base_key = key
        
        if count == 0:
            plural_key = f"{key}.zero"
        elif count == 1:
            plural_key = f"{key}.one"
        else:
            plural_key = f"{key}.other"
        
        text = translations.get(plural_key)
        if text is None:
            text = translations.get(base_key, key)
        
        return text.format(count=count)
    
    def get_available_languages(self) -> List[LocaleConfig]:
        return list(LOCALE_CONFIGS.values())
    
    def get_locale_config(self, language: Optional[Language] = None) -> LocaleConfig:
        lang = language or self.current_language
        return LOCALE_CONFIGS.get(lang, LOCALE_CONFIGS[DEFAULT_LANGUAGE])
    
    def format_date(
        self,
        date: datetime,
        language: Optional[Language] = None,
        include_time: bool = False
    ) -> str:
        config = self.get_locale_config(language)
        
        fmt = config.date_format
        if include_time:
            fmt = f"{config.date_format} {config.time_format}"
        
        return date.strftime(fmt)
    
    def format_number(
        self,
        number: float,
        language: Optional[Language] = None,
        decimals: int = 2
    ) -> str:
        config = self.get_locale_config(language)
        
        formatted = f"{number:,.{decimals}f}"
        
        formatted = formatted.replace(',', 'TEMP')
        formatted = formatted.replace('.', config.decimal_separator)
        formatted = formatted.replace('TEMP', config.thousands_separator)
        
        return formatted
    
    def format_currency(
        self,
        amount: float,
        language: Optional[Language] = None,
        include_symbol: bool = True
    ) -> str:
        config = self.get_locale_config(language)
        
        formatted = self.format_number(amount, language)
        
        if include_symbol:
            formatted = f"{config.currency_symbol}{formatted}"
        
        return formatted
    
    def add_translation(
        self,
        key: str,
        value: str,
        language: Optional[Language] = None
    ):
        lang = language or self.current_language
        
        if lang not in self._translations:
            self._translations[lang] = {}
        
        self._translations[lang][key] = value
    
    def export_translations(
        self,
        language: Language,
        output_path: Optional[str] = None
    ) -> bool:
        translations = self._translations.get(language, {})
        
        if not output_path:
            self.translations_path.mkdir(parents=True, exist_ok=True)
            output_path = self.translations_path / f"{language.value}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported translations to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export translations: {e}")
            return False


translator = Translator()


def t(key: str, **kwargs) -> str:
    return translator.t(key, **kwargs)


def set_language(language: Language):
    translator.set_language(language)


def get_language() -> Language:
    return translator.get_language()


def get_locale_config(language: Optional[Language] = None) -> LocaleConfig:
    return translator.get_locale_config(language)


class ContentLocalizer:
    def __init__(self):
        self.translator = Translator()
    
    async def localize_content(
        self,
        content: str,
        target_language: Language,
        source_language: Optional[Language] = None
    ) -> str:
        if source_language and source_language == target_language:
            return content
        
        from agentforge.llm.model_router import ModelRouter
        llm = ModelRouter()
        
        source_lang_name = LOCALE_CONFIGS.get(source_language or Language.EN_US, LocaleConfig).native_name
        target_lang_name = LOCALE_CONFIGS.get(target_language, LocaleConfig).native_name
        
        prompt = f"""Translate the following content from {source_lang_name} to {target_lang_name}.

Content:
{content}

Requirements:
- Maintain the original tone and style
- Preserve any formatting (markdown, HTML, etc.)
- Keep technical terms and brand names unchanged
- Adapt cultural references appropriately

Translated content:"""

        response = await llm.chat_with_failover(
            message=prompt,
            task_type="creative"
        )
        
        return response.strip()
    
    async def localize_for_platforms(
        self,
        content: str,
        platforms: List[str],
        target_language: Language
    ) -> Dict[str, str]:
        results = {}
        
        base_translation = await self.localize_content(content, target_language)
        
        platform_adjustments = {
            "twitter": {"max_length": 280, "style": "casual"},
            "linkedin": {"max_length": 3000, "style": "professional"},
            "instagram": {"max_length": 2200, "style": "casual"},
            "facebook": {"max_length": 63206, "style": "casual"},
        }
        
        for platform in platforms:
            adjustment = platform_adjustments.get(platform, {})
            
            if adjustment.get("max_length") and len(base_translation) > adjustment["max_length"]:
                results[platform] = base_translation[:adjustment["max_length"] - 3] + "..."
            else:
                results[platform] = base_translation
        
        return results
    
    async def detect_language(self, content: str) -> Optional[Language]:
        from agentforge.llm.model_router import ModelRouter
        llm = ModelRouter()
        
        prompt = f"""Detect the language of this content and return only the ISO language code.

Content: {content[:500]}

Return format: just the language code like "zh-CN", "en-US", "ja-JP", etc."""

        try:
            response = await llm.chat_with_failover(
                message=prompt,
                task_type="analysis"
            )
            
            lang_code = response.strip().strip('"\'')
            return Language(lang_code)
        except Exception:
            return None
