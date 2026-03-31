"""
Social Media Content Adapter - Multi-platform content adaptation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
import re


class Platform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"


class PlatformLimits(BaseModel):
    """Platform-specific content limits"""
    max_characters: int
    max_hashtags: int
    max_images: int
    max_video_duration_seconds: int
    supports_links: bool = True
    supports_threads: bool = False


PLATFORM_LIMITS = {
    Platform.TWITTER: PlatformLimits(
        max_characters=280,
        max_hashtags=3,
        max_images=4,
        max_video_duration_seconds=140,
        supports_threads=True
    ),
    Platform.LINKEDIN: PlatformLimits(
        max_characters=3000,
        max_hashtags=5,
        max_images=9,
        max_video_duration_seconds=600,
        supports_links=True
    ),
    Platform.YOUTUBE: PlatformLimits(
        max_characters=5000,
        max_hashtags=15,
        max_images=0,
        max_video_duration_seconds=43200,
        supports_links=True
    ),
    Platform.INSTAGRAM: PlatformLimits(
        max_characters=2200,
        max_hashtags=30,
        max_images=10,
        max_video_duration_seconds=900,
        supports_links=False
    ),
    Platform.FACEBOOK: PlatformLimits(
        max_characters=63206,
        max_hashtags=10,
        max_images=10,
        max_video_duration_seconds=240,
        supports_links=True
    ),
    Platform.TIKTOK: PlatformLimits(
        max_characters=2200,
        max_hashtags=5,
        max_images=0,
        max_video_duration_seconds=180,
        supports_links=False
    ),
}


class AdaptedContent(BaseModel):
    """Adapted content for a specific platform"""
    platform: Platform
    content: str
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    content_type: ContentType = ContentType.TEXT
    media_urls: List[str] = Field(default_factory=list)
    thread_parts: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ContentAdapter:
    """Adapt content for multiple social media platforms"""
    
    def __init__(self):
        self._hashtag_pattern = re.compile(r'#\w+')
        self._mention_pattern = re.compile(r'@\w+')
        self._url_pattern = re.compile(r'https?://\S+')
    
    def adapt_content(
        self,
        content: str,
        platform: Platform,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        content_type: ContentType = ContentType.TEXT
    ) -> AdaptedContent:
        """Adapt content for a specific platform"""
        
        limits = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS[Platform.TWITTER])
        
        adapted = AdaptedContent(
            platform=platform,
            content=content,
            hashtags=hashtags or [],
            mentions=mentions or [],
            content_type=content_type,
            media_urls=media_urls or []
        )
        
        adapted.hashtags = self._optimize_hashtags(adapted.hashtags, limits.max_hashtags)
        
        if len(content) > limits.max_characters:
            if platform == Platform.TWITTER and limits.supports_threads:
                adapted.thread_parts = self._split_to_thread(content, limits.max_characters)
                adapted.content = adapted.thread_parts[0]
                adapted.warnings.append(f"Content split into {len(adapted.thread_parts)} tweets")
            else:
                adapted.content = self._truncate_content(content, limits.max_characters)
                adapted.warnings.append(f"Content truncated to {limits.max_characters} characters")
        
        adapted.hashtags = self._extract_existing_hashtags(content, adapted.hashtags)
        adapted.mentions = self._extract_existing_mentions(content)
        
        if not limits.supports_links:
            links = self._url_pattern.findall(content)
            if links:
                adapted.warnings.append(f"Links removed: {links}")
                adapted.content = self._url_pattern.sub("", adapted.content).strip()
        
        adapted.metadata["original_length"] = len(content)
        adapted.metadata["adapted_length"] = len(adapted.content)
        adapted.metadata["character_limit"] = limits.max_characters
        
        return adapted
    
    def adapt_for_all_platforms(
        self,
        content: str,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        platforms: Optional[List[Platform]] = None
    ) -> Dict[Platform, AdaptedContent]:
        """Adapt content for multiple platforms"""
        
        platforms = platforms or list(Platform)
        results = {}
        
        for platform in platforms:
            try:
                results[platform] = self.adapt_content(
                    content=content,
                    platform=platform,
                    hashtags=hashtags,
                    mentions=mentions,
                    media_urls=media_urls
                )
            except Exception as e:
                logger.error(f"Failed to adapt for {platform}: {e}")
        
        return results
    
    def _optimize_hashtags(
        self,
        hashtags: List[str],
        max_count: int
    ) -> List[str]:
        """Optimize hashtag list"""
        
        clean_hashtags = []
        for tag in hashtags:
            if not tag.startswith('#'):
                tag = f'#{tag}'
            clean_hashtags.append(tag)
        
        unique_hashtags = list(dict.fromkeys(clean_hashtags))
        
        return unique_hashtags[:max_count]
    
    def _split_to_thread(
        self,
        content: str,
        max_chars: int
    ) -> List[str]:
        """Split long content into thread parts"""
        
        sentences = content.replace('\n', ' ').split('. ')
        threads = []
        current_thread = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if not sentence.endswith('.'):
                sentence += '.'
            
            if len(current_thread) + len(sentence) + 1 <= max_chars - 10:
                current_thread += sentence + " "
            else:
                if current_thread:
                    threads.append(current_thread.strip())
                current_thread = sentence + " "
        
        if current_thread:
            threads.append(current_thread.strip())
        
        for i, thread in enumerate(threads):
            if len(threads) > 1:
                threads[i] = f"{i+1}/{len(threads)} {thread}"
        
        return threads
    
    def _truncate_content(
        self,
        content: str,
        max_chars: int
    ) -> str:
        """Truncate content to fit limit"""
        
        if len(content) <= max_chars:
            return content
        
        truncated = content[:max_chars - 3]
        last_space = truncated.rfind(' ')
        
        if last_space > max_chars * 0.8:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def _extract_existing_hashtags(
        self,
        content: str,
        existing: List[str]
    ) -> List[str]:
        """Extract hashtags from content"""
        
        found = self._hashtag_pattern.findall(content)
        all_tags = existing + found
        
        seen = set()
        unique = []
        for tag in all_tags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique.append(tag)
        
        return unique
    
    def _extract_existing_mentions(
        self,
        content: str
    ) -> List[str]:
        """Extract mentions from content"""
        
        return self._mention_pattern.findall(content)
    
    def get_platform_limits(self, platform: Platform) -> PlatformLimits:
        """Get limits for a specific platform"""
        return PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS[Platform.TWITTER])
    
    def validate_content(
        self,
        content: str,
        platform: Platform
    ) -> Dict[str, Any]:
        """Validate content for a platform"""
        
        limits = self.get_platform_limits(platform)
        
        return {
            "valid": len(content) <= limits.max_characters,
            "length": len(content),
            "max_length": limits.max_characters,
            "remaining": limits.max_characters - len(content),
            "hashtags_count": len(self._hashtag_pattern.findall(content)),
            "max_hashtags": limits.max_hashtags,
            "has_links": bool(self._url_pattern.search(content)),
            "links_allowed": limits.supports_links
        }


content_adapter = ContentAdapter()
