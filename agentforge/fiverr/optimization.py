"""
Fiverr 主页优化建议模块

分析 Fiverr 主页数据，使用 AI 生成优化建议
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from loguru import logger

from agentforge.llm.model_router import ModelRouter


class OptimizationCategory(str, Enum):
    """优化建议类别"""
    PROFILE = "profile"
    GIG = "gig"
    PRICING = "pricing"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"


class Priority(str, Enum):
    """优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OptimizationSuggestion(BaseModel):
    """优化建议模型"""
    id: str
    category: OptimizationCategory
    title: str
    description: str
    priority: Priority
    expected_impact: str = Field(..., description="预期影响")
    implementation_steps: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, rejected


class FiverrProfileData(BaseModel):
    """Fiverr 主页数据模型"""
    username: str
    level: str = "New Seller"
    rating: float = 0.0
    total_reviews: int = 0
    total_orders: int = 0
    completion_rate: float = 0.0
    on_time_delivery: float = 0.0
    response_time: float = 0.0  # 小时
    gigs_count: int = 0
    total_earnings: float = 0.0
    profile_views: int = 0
    gig_impressions: int = 0
    gig_clicks: int = 0
    orders_in_queue: int = 0


class FiverrOptimizationEngine:
    """Fiverr 主页优化引擎"""
    
    def __init__(self):
        self.llm = ModelRouter()
        self._suggestions: Dict[str, OptimizationSuggestion] = {}
    
    async def analyze_profile(self, profile_data: FiverrProfileData) -> List[OptimizationSuggestion]:
        """分析 Fiverr 主页并生成优化建议"""
        logger.info(f"分析 Fiverr 主页：{profile_data.username}")
        
        # 准备分析数据
        analysis_prompt = self._build_analysis_prompt(profile_data)
        
        # 使用 AI 生成优化建议
        suggestions_text = await self.llm.chat_with_failover(
            message=analysis_prompt,
            task_type="analysis"
        )
        
        # 解析建议
        suggestions = self._parse_suggestions(suggestions_text, profile_data)
        
        # 保存建议
        for suggestion in suggestions:
            self._suggestions[suggestion.id] = suggestion
        
        logger.info(f"生成 {len(suggestions)} 条优化建议")
        return suggestions
    
    def _build_analysis_prompt(self, profile_data: FiverrProfileData) -> str:
        """构建分析提示"""
        return f"""分析以下 Fiverr 卖家数据并提供优化建议：

卖家信息:
- 用户名：{profile_data.username}
- 等级：{profile_data.level}
- 评分：{profile_data.rating}/5.0 ({profile_data.total_reviews} 条评价)
- 总订单：{profile_data.total_orders}
- 完成率：{profile_data.completion_rate}%
- 准时交付：{profile_data.on_time_delivery}%
- 响应时间：{profile_data.response_time} 小时
- 在线服务数：{profile_data.gigs_count}
- 主页浏览量：{profile_data.profile_views}
- 服务展示次数：{profile_data.gig_impressions}
- 服务点击次数：{profile_data.gig_clicks}
- 进行中订单：{profile_data.orders_in_queue}

请从以下方面提供具体的优化建议：
1. 个人资料优化（头像、描述、技能等）
2. Gig 优化（标题、描述、图片、视频等）
3. 定价策略（套餐设置、附加服务等）
4. 营销推广（社交媒体、SEO 等）
5. 客户服务（响应速度、沟通技巧等）

对于每条建议，请说明：
- 建议内容
- 优先级（高/中/低）
- 预期影响
- 具体实施步骤

请以 JSON 格式返回建议列表。"""
    
    def _parse_suggestions(self, suggestions_text: str, profile_data: FiverrProfileData) -> List[OptimizationSuggestion]:
        """解析 AI 生成的建议"""
        import json
        import hashlib
        
        suggestions = []
        
        try:
            # 尝试解析 JSON
            data = json.loads(suggestions_text)
            if isinstance(data, list):
                for i, item in enumerate(data):
                    suggestion = OptimizationSuggestion(
                        id=hashlib.md5(f"{profile_data.username}_{i}".encode(), usedforsecurity=False).hexdigest()[:8],
                        category=OptimizationCategory(item.get("category", "gig")),
                        title=item.get("title", "优化建议"),
                        description=item.get("description", ""),
                        priority=Priority(item.get("priority", "medium")),
                        expected_impact=item.get("expected_impact", "提升表现"),
                        implementation_steps=item.get("implementation_steps", [])
                    )
                    suggestions.append(suggestion)
        except json.JSONDecodeError:
            # 如果解析失败，创建默认建议
            suggestions = self._generate_default_suggestions(profile_data)
        
        return suggestions
    
    def _generate_default_suggestions(self, profile_data: FiverrProfileData) -> List[OptimizationSuggestion]:
        """生成默认优化建议（基于规则）"""
        suggestions = []
        
        # 检查评分
        if profile_data.rating < 4.5 and profile_data.total_reviews > 0:
            suggestions.append(OptimizationSuggestion(
                id="sugg_rating",
                category=OptimizationCategory.CUSTOMER_SERVICE,
                title="提升客户满意度",
                description="当前评分较低，需要改进服务质量",
                priority=Priority.HIGH,
                expected_impact="提升评分至 4.8+，增加订单转化率",
                implementation_steps=[
                    "主动联系过往客户收集反馈",
                    "识别并解决常见问题",
                    "提供超出预期的服务",
                    "礼貌地请满意客户留下好评"
                ]
            ))
        
        # 检查响应时间
        if profile_data.response_time > 2:
            suggestions.append(OptimizationSuggestion(
                id="sugg_response",
                category=OptimizationCategory.CUSTOMER_SERVICE,
                title="缩短响应时间",
                description=f"当前响应时间为{profile_data.response_time}小时，建议缩短至 1 小时内",
                priority=Priority.MEDIUM,
                expected_impact="提升客户满意度和搜索排名",
                implementation_steps=[
                    "启用手机通知",
                    "设置快速回复模板",
                    "定期检查消息",
                    "使用 Fiverr 移动应用"
                ]
            ))
        
        # 检查点击率
        if profile_data.gig_impressions > 0:
            ctr = (profile_data.gig_clicks / profile_data.gig_impressions) * 100
            if ctr < 2:
                suggestions.append(OptimizationSuggestion(
                    id="sugg_ctr",
                    category=OptimizationCategory.GIG,
                    title="优化 Gig 主图",
                    description=f"当前点击率{ctr:.1f}%，低于平均水平",
                    priority=Priority.HIGH,
                    expected_impact="提升点击率至 3%+",
                    implementation_steps=[
                        "使用高质量、专业的封面图片",
                        "添加清晰的标题文字",
                        "展示最佳作品案例",
                        "A/B 测试不同的封面图"
                    ]
                ))
        
        # 检查订单完成率
        if profile_data.completion_rate < 95:
            suggestions.append(OptimizationSuggestion(
                id="sugg_completion",
                category=OptimizationCategory.CUSTOMER_SERVICE,
                title="提升订单完成率",
                description=f"当前完成率{profile_data.completion_rate}%，建议提升至 95%+",
                priority=Priority.CRITICAL,
                expected_impact="提升搜索排名和客户信任度",
                implementation_steps=[
                    "谨慎接受订单，不超负荷工作",
                    "如无法完成及时与客户沟通取消",
                    "设置合理的交付时间",
                    "建立订单管理流程"
                ]
            ))
        
        # 检查准时交付率
        if profile_data.on_time_delivery < 90:
            suggestions.append(OptimizationSuggestion(
                id="sugg_delivery",
                category=OptimizationCategory.CUSTOMER_SERVICE,
                title="提升准时交付率",
                description=f"当前准时交付率{profile_data.on_time_delivery}%",
                priority=Priority.HIGH,
                expected_impact="提升客户满意度和复购率",
                implementation_steps=[
                    "设置更宽松的交付时间",
                    "提前开始工作",
                    "使用提醒工具",
                    "如遇延误提前沟通"
                ]
            ))
        
        return suggestions
    
    def get_suggestions(
        self,
        category: Optional[OptimizationCategory] = None,
        priority: Optional[Priority] = None,
        status: Optional[str] = None
    ) -> List[OptimizationSuggestion]:
        """获取优化建议（支持过滤）"""
        suggestions = list(self._suggestions.values())
        
        if category:
            suggestions = [s for s in suggestions if s.category == category]
        if priority:
            suggestions = [s for s in suggestions if s.priority == priority]
        if status:
            suggestions = [s for s in suggestions if s.status == status]
        
        # 按优先级排序
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 4))
        
        return suggestions
    
    def update_suggestion_status(self, suggestion_id: str, status: str) -> bool:
        """更新建议状态"""
        if suggestion_id in self._suggestions:
            self._suggestions[suggestion_id].status = status
            logger.info(f"更新建议 {suggestion_id} 状态为 {status}")
            return True
        return False
    
    def get_progress_report(self) -> Dict[str, Any]:
        """生成进度报告"""
        suggestions = list(self._suggestions.values())
        
        report = {
            "total_suggestions": len(suggestions),
            "by_status": {
                "pending": len([s for s in suggestions if s.status == "pending"]),
                "in_progress": len([s for s in suggestions if s.status == "in_progress"]),
                "completed": len([s for s in suggestions if s.status == "completed"]),
                "rejected": len([s for s in suggestions if s.status == "rejected"])
            },
            "by_category": {},
            "by_priority": {
                "critical": len([s for s in suggestions if s.priority == Priority.CRITICAL]),
                "high": len([s for s in suggestions if s.priority == Priority.HIGH]),
                "medium": len([s for s in suggestions if s.priority == Priority.MEDIUM]),
                "low": len([s for s in suggestions if s.priority == Priority.LOW])
            }
        }
        
        # 按类别统计
        for category in OptimizationCategory:
            report["by_category"][category.value] = len([
                s for s in suggestions if s.category == category
            ])
        
        return report


# 便捷函数
async def generate_optimization_suggestions(
    profile_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """生成优化建议的便捷函数"""
    engine = FiverrOptimizationEngine()
    
    # 转换为 Pydantic 模型
    profile = FiverrProfileData(**profile_data)
    
    # 生成建议
    suggestions = await engine.analyze_profile(profile)
    
    # 转换为字典
    return [s.model_dump() for s in suggestions]
