"""
AgentForge Visual Generation Module
AI-powered image suggestions and visual content creation
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import httpx
import asyncio
from loguru import logger

from agentforge.config import settings
from agentforge.llm.model_router import ModelRouter


class ImageStyle(str, Enum):
    PROFESSIONAL = "professional"
    MINIMALIST = "minimalist"
    VIBRANT = "vibrant"
    DARK = "dark"
    LIGHT = "light"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    VINTAGE = "vintage"
    MODERN = "modern"
    PLAYFUL = "playful"


class ImageCategory(str, Enum):
    SOCIAL_POST = "social_post"
    BANNER = "banner"
    THUMBNAIL = "thumbnail"
    LOGO = "logo"
    ILLUSTRATION = "illustration"
    BACKGROUND = "background"
    INFOGRAPHIC = "infographic"
    PRODUCT = "product"
    PORTRAIT = "portrait"
    ABSTRACT = "abstract"


class PlatformSpec(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    WEBSITE = "website"
    BLOG = "blog"


PLATFORM_DIMENSIONS: Dict[PlatformSpec, Tuple[int, int]] = {
    PlatformSpec.TWITTER: (1200, 675),
    PlatformSpec.INSTAGRAM: (1080, 1080),
    PlatformSpec.FACEBOOK: (1200, 630),
    PlatformSpec.LINKEDIN: (1200, 627),
    PlatformSpec.YOUTUBE: (1280, 720),
    PlatformSpec.WEBSITE: (1920, 1080),
    PlatformSpec.BLOG: (800, 600),
}


class StylePreset(BaseModel):
    id: str
    name: str
    description: str
    style_keywords: List[str]
    negative_keywords: List[str] = Field(default_factory=list)
    color_palette: Optional[List[str]] = None
    example_prompt: Optional[str] = None


DEFAULT_STYLE_PRESETS: Dict[str, StylePreset] = {
    "professional_clean": StylePreset(
        id="professional_clean",
        name="Professional Clean",
        description="Clean, modern professional look",
        style_keywords=[
            "clean", "minimalist", "professional", "modern",
            "corporate", "elegant", "sleek"
        ],
        negative_keywords=["cluttered", "messy", "amateur"],
        color_palette=["#FFFFFF", "#000000", "#1E3A5F", "#4A90D9"],
        example_prompt="clean professional business background with subtle gradient"
    ),
    "vibrant_creative": StylePreset(
        id="vibrant_creative",
        name="Vibrant Creative",
        description="Bold, colorful, and eye-catching",
        style_keywords=[
            "vibrant", "colorful", "bold", "dynamic",
            "energetic", "creative", "artistic"
        ],
        negative_keywords=["dull", "boring", "monochrome"],
        color_palette=["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"],
        example_prompt="vibrant colorful abstract background with dynamic shapes"
    ),
    "tech_modern": StylePreset(
        id="tech_modern",
        name="Tech Modern",
        description="Futuristic technology aesthetic",
        style_keywords=[
            "futuristic", "technology", "digital", "cyber",
            "modern", "sleek", "high-tech"
        ],
        negative_keywords=["old", "retro", "vintage"],
        color_palette=["#0D1117", "#58A6FF", "#238636", "#F78166"],
        example_prompt="futuristic technology background with glowing circuits"
    ),
    "nature_organic": StylePreset(
        id="nature_organic",
        name="Nature Organic",
        description="Natural, organic, eco-friendly aesthetic",
        style_keywords=[
            "natural", "organic", "eco", "green",
            "sustainable", "fresh", "earthy"
        ],
        negative_keywords=["artificial", "synthetic", "industrial"],
        color_palette=["#2D5A27", "#8BC34A", "#CDDC39", "#FFEB3B"],
        example_prompt="natural organic background with leaves and soft lighting"
    ),
    "luxury_elegant": StylePreset(
        id="luxury_elegant",
        name="Luxury Elegant",
        description="Premium, sophisticated look",
        style_keywords=[
            "luxury", "elegant", "premium", "sophisticated",
            "gold", "refined", "exclusive"
        ],
        negative_keywords=["cheap", "tacky", "basic"],
        color_palette=["#1A1A2E", "#D4AF37", "#C0C0C0", "#FFFFFF"],
        example_prompt="luxury elegant background with gold accents and marble texture"
    ),
}


class ImageSuggestion(BaseModel):
    id: str
    prompt: str
    style: ImageStyle
    category: ImageCategory
    platform: Optional[PlatformSpec] = None
    dimensions: Tuple[int, int]
    style_preset: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    negative_prompt: Optional[str] = None
    variations: int = 1
    quality: str = "standard"
    created_at: datetime = Field(default_factory=datetime.now)


class GeneratedImage(BaseModel):
    id: str
    url: str
    prompt: str
    revised_prompt: Optional[str] = None
    style: ImageStyle
    category: ImageCategory
    platform: Optional[PlatformSpec] = None
    dimensions: Tuple[int, int]
    file_size: Optional[int] = None
    format: str = "png"
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ImagePromptBuilder:
    def __init__(self):
        self.llm = ModelRouter()
    
    async def build_prompt(
        self,
        description: str,
        style: ImageStyle = ImageStyle.PROFESSIONAL,
        category: ImageCategory = ImageCategory.SOCIAL_POST,
        platform: Optional[PlatformSpec] = None,
        style_preset: Optional[str] = None,
        additional_keywords: Optional[List[str]] = None
    ) -> ImageSuggestion:
        prompt_parts = [description]
        
        preset = DEFAULT_STYLE_PRESETS.get(style_preset) if style_preset else None
        if preset:
            prompt_parts.extend(preset.style_keywords)
        else:
            style_keywords = self._get_style_keywords(style)
            prompt_parts.extend(style_keywords)
        
        category_keywords = self._get_category_keywords(category)
        prompt_parts.extend(category_keywords)
        
        if platform:
            platform_keywords = self._get_platform_keywords(platform)
            prompt_parts.extend(platform_keywords)
        
        if additional_keywords:
            prompt_parts.extend(additional_keywords)
        
        final_prompt = ", ".join(prompt_parts)
        
        negative_prompt = self._build_negative_prompt(style, preset)
        
        dimensions = PLATFORM_DIMENSIONS.get(platform, (1024, 1024)) if platform else (1024, 1024)
        
        return ImageSuggestion(
            id=f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            prompt=final_prompt,
            style=style,
            category=category,
            platform=platform,
            dimensions=dimensions,
            style_preset=style_preset,
            keywords=prompt_parts,
            negative_prompt=negative_prompt
        )
    
    def _get_style_keywords(self, style: ImageStyle) -> List[str]:
        style_map: Dict[ImageStyle, List[str]] = {
            ImageStyle.PROFESSIONAL: ["professional", "clean", "corporate"],
            ImageStyle.MINIMALIST: ["minimalist", "simple", "clean"],
            ImageStyle.VIBRANT: ["vibrant", "colorful", "bold"],
            ImageStyle.DARK: ["dark", "moody", "dramatic"],
            ImageStyle.LIGHT: ["light", "bright", "airy"],
            ImageStyle.CORPORATE: ["corporate", "business", "professional"],
            ImageStyle.CREATIVE: ["creative", "artistic", "unique"],
            ImageStyle.VINTAGE: ["vintage", "retro", "nostalgic"],
            ImageStyle.MODERN: ["modern", "contemporary", "sleek"],
            ImageStyle.PLAYFUL: ["playful", "fun", "whimsical"],
        }
        return style_map.get(style, ["professional"])
    
    def _get_category_keywords(self, category: ImageCategory) -> List[str]:
        category_map: Dict[ImageCategory, List[str]] = {
            ImageCategory.SOCIAL_POST: ["social media", "engaging", "eye-catching"],
            ImageCategory.BANNER: ["banner", "header", "wide format"],
            ImageCategory.THUMBNAIL: ["thumbnail", "click-worthy", "preview"],
            ImageCategory.LOGO: ["logo", "brand", "icon"],
            ImageCategory.ILLUSTRATION: ["illustration", "artwork", "graphic"],
            ImageCategory.BACKGROUND: ["background", "wallpaper", "texture"],
            ImageCategory.INFOGRAPHIC: ["infographic", "data visualization", "informative"],
            ImageCategory.PRODUCT: ["product", "commercial", "showcase"],
            ImageCategory.PORTRAIT: ["portrait", "headshot", "professional photo"],
            ImageCategory.ABSTRACT: ["abstract", "artistic", "conceptual"],
        }
        return category_map.get(category, [])
    
    def _get_platform_keywords(self, platform: PlatformSpec) -> List[str]:
        platform_map: Dict[PlatformSpec, List[str]] = {
            PlatformSpec.TWITTER: ["twitter optimized", "landscape format"],
            PlatformSpec.INSTAGRAM: ["instagram optimized", "square format"],
            PlatformSpec.FACEBOOK: ["facebook optimized", "shareable"],
            PlatformSpec.LINKEDIN: ["linkedin optimized", "professional network"],
            PlatformSpec.YOUTUBE: ["youtube thumbnail", "video preview"],
            PlatformSpec.WEBSITE: ["website hero", "high resolution"],
            PlatformSpec.BLOG: ["blog featured", "article header"],
        }
        return platform_map.get(platform, [])
    
    def _build_negative_prompt(
        self,
        style: ImageStyle,
        preset: Optional[StylePreset] = None
    ) -> str:
        negative_parts = [
            "blurry", "low quality", "pixelated", "distorted",
            "watermark", "signature", "text", "logo"
        ]
        
        if preset and preset.negative_keywords:
            negative_parts.extend(preset.negative_keywords)
        
        return ", ".join(negative_parts)
    
    async def enhance_prompt(self, base_prompt: str) -> str:
        enhance_request = f"""Enhance this image generation prompt to be more detailed and effective for AI image generation.

Original prompt: "{base_prompt}"

Guidelines:
- Add specific visual details
- Include lighting and mood descriptors
- Add composition hints
- Keep it concise but descriptive
- Focus on visual elements only

Enhanced prompt:"""

        response = await self.llm.chat_with_failover(
            message=enhance_request,
            task_type="creative"
        )
        return response.strip()
    
    async def suggest_for_content(
        self,
        content: str,
        platform: PlatformSpec,
        style: ImageStyle = ImageStyle.PROFESSIONAL
    ) -> List[ImageSuggestion]:
        analysis_prompt = f"""Analyze this content and suggest 3 image concepts that would complement it well.

Content: "{content[:500]}"
Platform: {platform.value}

For each suggestion, provide:
1. A brief concept description
2. Key visual elements
3. Mood/atmosphere

Format as JSON array with keys: concept, elements, mood"""

        response = await self.llm.chat_with_failover(
            message=analysis_prompt,
            task_type="creative"
        )
        
        suggestions = []
        try:
            import json
            concepts = json.loads(response)
            
            for i, concept in enumerate(concepts[:3]):
                suggestion = await self.build_prompt(
                    description=concept.get("concept", ""),
                    style=style,
                    category=ImageCategory.SOCIAL_POST,
                    platform=platform,
                    additional_keywords=concept.get("elements", [])
                )
                suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Failed to parse content suggestions: {e}")
            suggestion = await self.build_prompt(
                description=f"visual for {platform.value} post",
                style=style,
                category=ImageCategory.SOCIAL_POST,
                platform=platform
            )
            suggestions.append(suggestion)
        
        return suggestions


class VisualGenerator:
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai"
    ):
        self.api_key = api_key or getattr(settings, 'openai_api_key', None)
        self.provider = provider
        self.prompt_builder = ImagePromptBuilder()
        
        self._providers = {
            "openai": self._generate_openai,
            "stability": self._generate_stability,
            "midjourney": self._generate_midjourney,
        }
    
    async def generate(
        self,
        suggestion: ImageSuggestion,
        provider: Optional[str] = None
    ) -> GeneratedImage:
        selected_provider = provider or self.provider
        generator = self._providers.get(selected_provider)
        
        if not generator:
            raise ValueError(f"Unknown provider: {selected_provider}")
        
        return await generator(suggestion)
    
    async def generate_from_description(
        self,
        description: str,
        style: ImageStyle = ImageStyle.PROFESSIONAL,
        category: ImageCategory = ImageCategory.SOCIAL_POST,
        platform: Optional[PlatformSpec] = None,
        style_preset: Optional[str] = None
    ) -> GeneratedImage:
        suggestion = await self.prompt_builder.build_prompt(
            description=description,
            style=style,
            category=category,
            platform=platform,
            style_preset=style_preset
        )
        
        return await self.generate(suggestion)
    
    async def generate_variations(
        self,
        suggestion: ImageSuggestion,
        count: int = 4
    ) -> List[GeneratedImage]:
        tasks = []
        for i in range(count):
            varied_suggestion = ImageSuggestion(
                id=f"{suggestion.id}_var{i}",
                prompt=suggestion.prompt,
                style=suggestion.style,
                category=suggestion.category,
                platform=suggestion.platform,
                dimensions=suggestion.dimensions,
                style_preset=suggestion.style_preset,
                keywords=suggestion.keywords,
                negative_prompt=suggestion.negative_prompt,
                variations=1
            )
            tasks.append(self.generate(varied_suggestion))
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _generate_openai(self, suggestion: ImageSuggestion) -> GeneratedImage:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        url = "https://api.openai.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": suggestion.prompt,
            "n": suggestion.variations,
            "size": f"{suggestion.dimensions[0]}x{suggestion.dimensions[1]}",
            "quality": suggestion.quality,
            "response_format": "url"
        }
        
        if suggestion.negative_prompt:
            payload["negative_prompt"] = suggestion.negative_prompt
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            
            if "error" in data:
                raise Exception(f"OpenAI API error: {data['error']}")
            
            image_data = data.get("data", [])[0]
            
            return GeneratedImage(
                id=f"gen_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                url=image_data.get("url", ""),
                prompt=suggestion.prompt,
                revised_prompt=image_data.get("revised_prompt"),
                style=suggestion.style,
                category=suggestion.category,
                platform=suggestion.platform,
                dimensions=suggestion.dimensions,
                format="png",
                metadata={"provider": "openai", "model": "dall-e-3"}
            )
    
    async def _generate_stability(self, suggestion: ImageSuggestion) -> GeneratedImage:
        stability_key = getattr(settings, 'stability_api_key', None)
        if not stability_key:
            raise ValueError("Stability API key not configured")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {"text": suggestion.prompt, "weight": 1.0}
            ],
            "cfg_scale": 7,
            "height": suggestion.dimensions[1],
            "width": suggestion.dimensions[0],
            "samples": suggestion.variations,
            "steps": 30
        }
        
        if suggestion.negative_prompt:
            payload["text_prompts"].append({
                "text": suggestion.negative_prompt,
                "weight": -1.0
            })
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            
            if "artifacts" not in data:
                raise Exception(f"Stability API error: {data}")
            
            artifact = data["artifacts"][0]
            
            return GeneratedImage(
                id=f"gen_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                url=f"data:image/png;base64,{artifact.get('base64', '')}",
                prompt=suggestion.prompt,
                style=suggestion.style,
                category=suggestion.category,
                platform=suggestion.platform,
                dimensions=suggestion.dimensions,
                format="png",
                metadata={"provider": "stability", "seed": artifact.get("seed")}
            )
    
    async def _generate_midjourney(self, suggestion: ImageSuggestion) -> GeneratedImage:
        logger.warning("Midjourney direct API not available, using placeholder")
        
        return GeneratedImage(
            id=f"gen_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            url="",
            prompt=suggestion.prompt,
            style=suggestion.style,
            category=suggestion.category,
            platform=suggestion.platform,
            dimensions=suggestion.dimensions,
            format="png",
            metadata={"provider": "midjourney", "status": "requires_manual_generation"}
        )
    
    def get_style_presets(self) -> Dict[str, StylePreset]:
        return DEFAULT_STYLE_PRESETS.copy()
    
    def get_platform_specs(self) -> Dict[PlatformSpec, Tuple[int, int]]:
        return PLATFORM_DIMENSIONS.copy()
    
    async def suggest_and_generate(
        self,
        content: str,
        platform: PlatformSpec,
        style: ImageStyle = ImageStyle.PROFESSIONAL,
        auto_select: bool = True
    ) -> Tuple[ImageSuggestion, GeneratedImage]:
        suggestions = await self.prompt_builder.suggest_for_content(
            content=content,
            platform=platform,
            style=style
        )
        
        if not suggestions:
            raise Exception("Failed to generate image suggestions")
        
        selected = suggestions[0] if auto_select else suggestions[0]
        generated = await self.generate(selected)
        
        return selected, generated
