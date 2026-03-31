"""
Social Media Account Manager - Manage multiple social accounts
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
from uuid import uuid4

from agentforge.social.content_adapter import Platform


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AccountType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    CREATOR = "creator"


class SocialAccount(BaseModel):
    """Social media account model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    platform: Platform
    username: str
    display_name: Optional[str] = None
    account_type: AccountType = AccountType.PERSONAL
    status: AccountStatus = AccountStatus.ACTIVE
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_verified: bool = False
    is_primary: bool = False
    credentials: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_sync: Optional[datetime] = None


class AccountStats(BaseModel):
    """Account statistics"""
    account_id: str
    platform: Platform
    followers: int = 0
    following: int = 0
    posts: int = 0
    engagement_rate: float = 0.0
    growth_rate: float = 0.0
    collected_at: datetime = Field(default_factory=datetime.now)


class AccountManager:
    """Manage social media accounts"""
    
    def __init__(self):
        self._accounts: Dict[str, SocialAccount] = {}
        self._stats_history: Dict[str, List[AccountStats]] = {}
    
    def add_account(
        self,
        platform: Platform,
        username: str,
        display_name: Optional[str] = None,
        account_type: AccountType = AccountType.PERSONAL,
        credentials: Optional[Dict[str, str]] = None,
        is_primary: bool = False
    ) -> SocialAccount:
        """Add a new social media account"""
        
        existing = self.get_account_by_username(platform, username)
        if existing:
            logger.warning(f"Account already exists: {username} on {platform.value}")
            return existing
        
        account = SocialAccount(
            platform=platform,
            username=username,
            display_name=display_name or username,
            account_type=account_type,
            credentials=credentials or {},
            is_primary=is_primary
        )
        
        self._accounts[account.id] = account
        self._stats_history[account.id] = []
        
        logger.info(f"Added account: {username} on {platform.value}")
        
        return account
    
    def update_account(
        self,
        account_id: str,
        **kwargs
    ) -> Optional[SocialAccount]:
        """Update account information"""
        
        if account_id not in self._accounts:
            return None
        
        account = self._accounts[account_id]
        
        for key, value in kwargs.items():
            if hasattr(account, key) and key not in ["id", "created_at"]:
                setattr(account, key, value)
        
        account.updated_at = datetime.now()
        
        logger.info(f"Updated account: {account.username}")
        
        return account
    
    def remove_account(self, account_id: str) -> bool:
        """Remove an account"""
        
        if account_id not in self._accounts:
            return False
        
        account = self._accounts[account_id]
        
        del self._accounts[account_id]
        
        if account_id in self._stats_history:
            del self._stats_history[account_id]
        
        logger.info(f"Removed account: {account.username}")
        
        return True
    
    def get_account(self, account_id: str) -> Optional[SocialAccount]:
        """Get account by ID"""
        return self._accounts.get(account_id)
    
    def get_account_by_username(
        self,
        platform: Platform,
        username: str
    ) -> Optional[SocialAccount]:
        """Get account by platform and username"""
        
        for account in self._accounts.values():
            if account.platform == platform and account.username == username:
                return account
        
        return None
    
    def get_accounts_by_platform(
        self,
        platform: Platform,
        active_only: bool = True
    ) -> List[SocialAccount]:
        """Get all accounts for a platform"""
        
        accounts = [
            a for a in self._accounts.values()
            if a.platform == platform
        ]
        
        if active_only:
            accounts = [a for a in accounts if a.status == AccountStatus.ACTIVE]
        
        return accounts
    
    def get_primary_account(
        self,
        platform: Platform
    ) -> Optional[SocialAccount]:
        """Get primary account for a platform"""
        
        for account in self._accounts.values():
            if account.platform == platform and account.is_primary:
                return account
        
        accounts = self.get_accounts_by_platform(platform)
        return accounts[0] if accounts else None
    
    def set_primary_account(
        self,
        account_id: str
    ) -> bool:
        """Set an account as primary"""
        
        if account_id not in self._accounts:
            return False
        
        account = self._accounts[account_id]
        
        for other in self._accounts.values():
            if other.platform == account.platform and other.id != account_id:
                other.is_primary = False
        
        account.is_primary = True
        
        logger.info(f"Set primary account: {account.username} for {account.platform.value}")
        
        return True
    
    def update_stats(
        self,
        account_id: str,
        followers: int,
        following: int,
        posts: int,
        engagement_rate: float = 0.0,
        growth_rate: float = 0.0
    ) -> Optional[AccountStats]:
        """Update account statistics"""
        
        if account_id not in self._accounts:
            return None
        
        account = self._accounts[account_id]
        
        account.followers_count = followers
        account.following_count = following
        account.posts_count = posts
        account.last_sync = datetime.now()
        
        stats = AccountStats(
            account_id=account_id,
            platform=account.platform,
            followers=followers,
            following=following,
            posts=posts,
            engagement_rate=engagement_rate,
            growth_rate=growth_rate
        )
        
        if account_id not in self._stats_history:
            self._stats_history[account_id] = []
        
        self._stats_history[account_id].append(stats)
        
        logger.info(f"Updated stats for {account.username}")
        
        return stats
    
    def get_stats_history(
        self,
        account_id: str,
        limit: int = 30
    ) -> List[AccountStats]:
        """Get stats history for an account"""
        
        history = self._stats_history.get(account_id, [])
        return history[-limit:]
    
    def list_all_accounts(
        self,
        active_only: bool = True
    ) -> List[SocialAccount]:
        """List all accounts"""
        
        accounts = list(self._accounts.values())
        
        if active_only:
            accounts = [a for a in accounts if a.status == AccountStatus.ACTIVE]
        
        return accounts
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get summary of all accounts"""
        
        platform_counts = {}
        for platform in Platform:
            platform_counts[platform.value] = len(
                self.get_accounts_by_platform(platform)
            )
        
        total_followers = sum(a.followers_count for a in self._accounts.values())
        total_posts = sum(a.posts_count for a in self._accounts.values())
        
        return {
            "total_accounts": len(self._accounts),
            "platform_distribution": platform_counts,
            "total_followers": total_followers,
            "total_posts": total_posts,
            "primary_accounts": {
                platform.value: (self.get_primary_account(platform).username if self.get_primary_account(platform) else None)
                for platform in Platform
            }
        }
    
    def check_account_health(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """Check account health status"""
        
        if account_id not in self._accounts:
            return {"error": "Account not found"}
        
        account = self._accounts[account_id]
        
        health = {
            "account_id": account_id,
            "username": account.username,
            "platform": account.platform.value,
            "status": account.status.value,
            "issues": [],
            "recommendations": []
        }
        
        if account.status == AccountStatus.SUSPENDED:
            health["issues"].append("Account is suspended")
        
        if not account.credentials:
            health["issues"].append("No credentials configured")
        
        if account.last_sync:
            days_since_sync = (datetime.now() - account.last_sync).days
            if days_since_sync > 7:
                health["issues"].append(f"Last sync was {days_since_sync} days ago")
        
        history = self._stats_history.get(account_id, [])
        if len(history) >= 2:
            recent = history[-1]
            previous = history[-2]
            
            if recent.followers < previous.followers:
                health["issues"].append("Follower count decreased")
            
            if recent.engagement_rate < previous.engagement_rate * 0.8:
                health["issues"].append("Engagement rate dropped significantly")
        
        if not health["issues"]:
            health["status"] = "healthy"
        else:
            health["recommendations"].append("Review and address identified issues")
        
        return health


account_manager = AccountManager()
