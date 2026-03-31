"""
Fiverr 优化建议测试
"""
import pytest
from datetime import datetime
from agentforge.fiverr.optimization import (
    FiverrOptimizationEngine,
    FiverrProfileData,
    OptimizationCategory,
    Priority,
    OptimizationSuggestion
)


@pytest.fixture
def engine():
    """创建优化引擎"""
    return FiverrOptimizationEngine()


@pytest.fixture
def sample_profile_data():
    """示例主页数据"""
    return FiverrProfileData(
        username="test_seller",
        level="Level 2 Seller",
        rating=4.7,
        total_reviews=150,
        total_orders=200,
        completion_rate=98,
        on_time_delivery=95,
        response_time=1.5,
        gigs_count=5,
        total_earnings=10000.0,
        profile_views=5000,
        gig_impressions=10000,
        gig_clicks=300,
        orders_in_queue=3
    )


class TestFiverrOptimizationEngine:
    """测试 Fiverr 优化引擎"""
    
    def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert engine.llm is not None
        assert len(engine._suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_profile(self, engine, sample_profile_data):
        """测试分析主页"""
        suggestions = await engine.analyze_profile(sample_profile_data)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # 验证建议结构
        for suggestion in suggestions:
            assert isinstance(suggestion, OptimizationSuggestion)
            assert suggestion.id is not None
            assert suggestion.category in OptimizationCategory
            assert suggestion.priority in Priority
            assert len(suggestion.title) > 0
            assert len(suggestion.description) > 0
    
    def test_generate_default_suggestions_low_rating(self, engine):
        """测试生成默认建议 - 低评分"""
        profile = FiverrProfileData(
            username="low_rating_seller",
            rating=3.5,
            total_reviews=50,
            completion_rate=90,
            response_time=5.0
        )
        
        suggestions = engine._generate_default_suggestions(profile)
        
        assert len(suggestions) > 0
        
        # 应该包含评分相关建议
        rating_suggestions = [
            s for s in suggestions 
            if "评分" in s.title or "满意度" in s.title
        ]
        assert len(rating_suggestions) > 0
    
    def test_generate_default_suggestions_slow_response(self, engine):
        """测试生成默认建议 - 响应慢"""
        profile = FiverrProfileData(
            username="slow_responder",
            rating=4.8,
            response_time=10.0,  # 10 小时
            completion_rate=99
        )
        
        suggestions = engine._generate_default_suggestions(profile)
        
        # 应该包含响应时间建议
        response_suggestions = [
            s for s in suggestions 
            if "响应" in s.title or "响应" in s.description
        ]
        assert len(response_suggestions) > 0
    
    def test_generate_default_suggestions_low_ctr(self, engine):
        """测试生成默认建议 - 低点击率"""
        profile = FiverrProfileData(
            username="low_ctr_seller",
            gig_impressions=10000,
            gig_clicks=50,  # 0.5% CTR
            rating=4.9
        )
        
        suggestions = engine._generate_default_suggestions(profile)
        
        # 应该包含点击率建议
        ctr_suggestions = [
            s for s in suggestions 
            if "点击" in s.title or "CTR" in s.title or "主图" in s.title
        ]
        assert len(ctr_suggestions) > 0
    
    def test_get_suggestions_all(self, engine, sample_profile_data):
        """测试获取所有建议"""
        # 先生成建议
        engine._suggestions = {
            "s1": OptimizationSuggestion(
                id="s1",
                category=OptimizationCategory.GIG,
                title="优化 Gig 图片",
                description="使用更专业的图片",
                priority=Priority.HIGH,
                expected_impact="提升点击率"
            ),
            "s2": OptimizationSuggestion(
                id="s2",
                category=OptimizationCategory.PRICING,
                title="调整价格",
                description="提高套餐价格",
                priority=Priority.MEDIUM,
                expected_impact="增加收入"
            ),
            "s3": OptimizationSuggestion(
                id="s3",
                category=OptimizationCategory.GIG,
                title="优化描述",
                description="添加更多关键词",
                priority=Priority.LOW,
                expected_impact="提升搜索排名"
            )
        }
        
        suggestions = engine.get_suggestions()
        
        assert len(suggestions) == 3
        # 应该按优先级排序
        assert suggestions[0].priority == Priority.HIGH
        assert suggestions[1].priority == Priority.MEDIUM
        assert suggestions[2].priority == Priority.LOW
    
    def test_get_suggestions_filter_by_category(self, engine):
        """测试按类别过滤建议"""
        engine._suggestions = {
            "s1": OptimizationSuggestion(
                id="s1",
                category=OptimizationCategory.GIG,
                title="优化 Gig 图片",
                description="使用更专业的图片",
                priority=Priority.HIGH,
                expected_impact="提升点击率"
            ),
            "s2": OptimizationSuggestion(
                id="s2",
                category=OptimizationCategory.PRICING,
                title="调整价格",
                description="提高套餐价格",
                priority=Priority.MEDIUM,
                expected_impact="增加收入"
            )
        }
        
        suggestions = engine.get_suggestions(category=OptimizationCategory.GIG)
        
        assert len(suggestions) == 1
        assert suggestions[0].category == OptimizationCategory.GIG
    
    def test_get_suggestions_filter_by_priority(self, engine):
        """测试按优先级过滤建议"""
        engine._suggestions = {
            "s1": OptimizationSuggestion(
                id="s1",
                category=OptimizationCategory.GIG,
                title="优化 Gig 图片",
                description="使用更专业的图片",
                priority=Priority.HIGH,
                expected_impact="提升点击率"
            ),
            "s2": OptimizationSuggestion(
                id="s2",
                category=OptimizationCategory.PRICING,
                title="调整价格",
                description="提高套餐价格",
                priority=Priority.HIGH,
                expected_impact="增加收入"
            ),
            "s3": OptimizationSuggestion(
                id="s3",
                category=OptimizationCategory.GIG,
                title="优化描述",
                description="添加更多关键词",
                priority=Priority.LOW,
                expected_impact="提升搜索排名"
            )
        }
        
        suggestions = engine.get_suggestions(priority=Priority.HIGH)
        
        assert len(suggestions) == 2
        assert all(s.priority == Priority.HIGH for s in suggestions)
    
    def test_get_suggestions_filter_by_status(self, engine):
        """测试按状态过滤建议"""
        engine._suggestions = {
            "s1": OptimizationSuggestion(
                id="s1",
                category=OptimizationCategory.GIG,
                title="优化 Gig 图片",
                description="使用更专业的图片",
                priority=Priority.HIGH,
                expected_impact="提升点击率",
                status="pending"
            ),
            "s2": OptimizationSuggestion(
                id="s2",
                category=OptimizationCategory.PRICING,
                title="调整价格",
                description="提高套餐价格",
                priority=Priority.MEDIUM,
                expected_impact="增加收入",
                status="completed"
            )
        }
        
        suggestions = engine.get_suggestions(status="pending")
        
        assert len(suggestions) == 1
        assert suggestions[0].status == "pending"
    
    def test_update_suggestion_status(self, engine):
        """测试更新建议状态"""
        suggestion = OptimizationSuggestion(
            id="s1",
            category=OptimizationCategory.GIG,
            title="优化 Gig 图片",
            description="使用更专业的图片",
            priority=Priority.HIGH,
            expected_impact="提升点击率",
            status="pending"
        )
        engine._suggestions["s1"] = suggestion
        
        # 更新状态
        success = engine.update_suggestion_status("s1", "in_progress")
        
        assert success is True
        assert engine._suggestions["s1"].status == "in_progress"
        
        # 更新不存在的建议
        success = engine.update_suggestion_status("nonexistent", "completed")
        assert success is False
    
    def test_get_progress_report(self, engine):
        """测试获取进度报告"""
        engine._suggestions = {
            "s1": OptimizationSuggestion(
                id="s1",
                category=OptimizationCategory.GIG,
                title="优化 Gig 图片",
                description="使用更专业的图片",
                priority=Priority.HIGH,
                expected_impact="提升点击率",
                status="pending"
            ),
            "s2": OptimizationSuggestion(
                id="s2",
                category=OptimizationCategory.PRICING,
                title="调整价格",
                description="提高套餐价格",
                priority=Priority.MEDIUM,
                expected_impact="增加收入",
                status="completed"
            ),
            "s3": OptimizationSuggestion(
                id="s3",
                category=OptimizationCategory.GIG,
                title="优化描述",
                description="添加更多关键词",
                priority=Priority.LOW,
                expected_impact="提升搜索排名",
                status="pending"
            )
        }
        
        report = engine.get_progress_report()
        
        assert report["total_suggestions"] == 3
        assert report["by_status"]["pending"] == 2
        assert report["by_status"]["completed"] == 1
        assert report["by_priority"]["high"] == 1
        assert report["by_priority"]["medium"] == 1
        assert report["by_priority"]["low"] == 1
        assert "gig" in report["by_category"]
        assert "pricing" in report["by_category"]


class TestOptimizationSuggestion:
    """测试优化建议模型"""
    
    def test_create_suggestion(self):
        """测试创建建议"""
        suggestion = OptimizationSuggestion(
            id="test_1",
            category=OptimizationCategory.GIG,
            title="优化 Gig 图片",
            description="使用更专业的图片",
            priority=Priority.HIGH,
            expected_impact="提升点击率"
        )
        
        assert suggestion.id == "test_1"
        assert suggestion.category == OptimizationCategory.GIG
        assert suggestion.priority == Priority.HIGH
        assert suggestion.status == "pending"
        assert isinstance(suggestion.created_at, datetime)
    
    def test_create_suggestion_with_steps(self):
        """测试创建带实施步骤的建议"""
        suggestion = OptimizationSuggestion(
            id="test_2",
            category=OptimizationCategory.PRICING,
            title="调整价格策略",
            description="增加高级套餐",
            priority=Priority.MEDIUM,
            expected_impact="提高客单价",
            implementation_steps=[
                "分析竞争对手价格",
                "设计新的套餐结构",
                "更新 Gig 描述",
                "通知老客户"
            ]
        )
        
        assert len(suggestion.implementation_steps) == 4
        assert "分析竞争对手价格" in suggestion.implementation_steps


class TestFiverrProfileData:
    """测试主页数据模型"""
    
    def test_create_profile_data(self):
        """测试创建主页数据"""
        profile = FiverrProfileData(
            username="test_seller",
            level="Level 2 Seller",
            rating=4.8,
            total_reviews=100
        )
        
        assert profile.username == "test_seller"
        assert profile.level == "Level 2 Seller"
        assert profile.rating == 4.8
        assert profile.total_reviews == 100
        assert profile.gigs_count == 0  # 默认值
    
    def test_profile_data_defaults(self):
        """测试默认值"""
        profile = FiverrProfileData(username="new_seller")
        
        assert profile.level == "New Seller"
        assert profile.rating == 0.0
        assert profile.total_reviews == 0
        assert profile.completion_rate == 0.0
        assert profile.on_time_delivery == 0.0
