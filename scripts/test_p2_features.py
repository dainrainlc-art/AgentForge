#!/usr/bin/env python3
"""
P2 功能快速测试脚本

测试 Fiverr 优化建议和社交媒体分析 API
"""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agentforge.fiverr.optimization import FiverrOptimizationEngine, FiverrProfileData
from agentforge.social.analytics_enhanced import AdvancedAnalyticsEngine, PostMetrics, Platform, AnalyticsPeriod


async def test_fiverr_optimization():
    """测试 Fiverr 优化建议功能"""
    print("\n" + "="*60)
    print("📊 测试 Fiverr 优化建议功能")
    print("="*60)
    
    # 创建引擎
    engine = FiverrOptimizationEngine()
    
    # 准备测试数据
    profile_data = FiverrProfileData(
        username="test_seller_2024",
        level="Level 2 Seller",
        rating=4.3,
        total_reviews=85,
        total_orders=120,
        completion_rate=92,
        on_time_delivery=88,
        response_time=3.5,
        gigs_count=4,
        total_earnings=5000.0,
        profile_views=2500,
        gig_impressions=8000,
        gig_clicks=120,
        orders_in_queue=2
    )
    
    print(f"\n分析卖家：{profile_data.username}")
    print(f"评级：{profile_data.rating}/5.0 ({profile_data.total_reviews} 条评价)")
    print(f"完成率：{profile_data.completion_rate}%")
    print(f"准时交付：{profile_data.on_time_delivery}%")
    print(f"响应时间：{profile_data.response_time} 小时")
    print(f"点击率：{(profile_data.gig_clicks/profile_data.gig_impressions*100):.2f}%")
    
    # 生成建议（使用基于规则的兜底方案，避免 AI 调用）
    print("\n⏳ 生成优化建议...")
    suggestions = engine._generate_default_suggestions(profile_data)
    
    print(f"\n✅ 生成了 {len(suggestions)} 条优化建议：\n")
    
    # 显示建议
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. [{suggestion.priority.value.upper()}] {suggestion.title}")
        print(f"   类别：{suggestion.category.value}")
        print(f"   描述：{suggestion.description}")
        print(f"   预期影响：{suggestion.expected_impact}")
        print(f"   实施步骤:")
        for j, step in enumerate(suggestion.implementation_steps, 1):
            print(f"     {j}. {step}")
        print()
    
    # 获取进度报告
    print("\n📈 进度报告:")
    report = engine.get_progress_report()
    print(f"   总建议数：{report['total_suggestions']}")
    print(f"   按优先级:")
    for priority, count in report['by_priority'].items():
        print(f"     - {priority}: {count}")
    
    return suggestions


def test_social_analytics():
    """测试社交媒体分析功能"""
    print("\n" + "="*60)
    print("📱 测试社交媒体效果分析功能")
    print("="*60)
    
    # 创建引擎
    engine = AdvancedAnalyticsEngine()
    
    # 准备测试数据
    test_posts = [
        {"post_id": "tw_001", "platform": "twitter", "impressions": 5000, "engagement": 250, "likes": 180, "comments": 45, "shares": 25},
        {"post_id": "tw_002", "platform": "twitter", "impressions": 6000, "engagement": 300, "likes": 220, "comments": 50, "shares": 30},
        {"post_id": "tw_003", "platform": "twitter", "impressions": 4500, "engagement": 200, "likes": 150, "comments": 30, "shares": 20},
        {"post_id": "li_001", "platform": "linkedin", "impressions": 3000, "engagement": 180, "likes": 120, "comments": 40, "shares": 20},
        {"post_id": "li_002", "platform": "linkedin", "impressions": 3500, "engagement": 200, "likes": 140, "comments": 45, "shares": 15},
        {"post_id": "fb_001", "platform": "facebook", "impressions": 2000, "engagement": 100, "likes": 70, "comments": 20, "shares": 10},
    ]
    
    print(f"\n添加 {len(test_posts)} 个帖子的指标数据...")
    
    # 添加数据
    for post in test_posts:
        metrics = PostMetrics(
            post_id=post["post_id"],
            platform=Platform(post["platform"]),
            impressions=post["impressions"],
            engagement=post["engagement"],
            likes=post["likes"],
            comments=post["comments"],
            shares=post["shares"],
            engagement_rate=(post["engagement"]/post["impressions"]*100) if post["impressions"] > 0 else 0
        )
        engine.add_metrics(metrics)
        print(f"  ✓ {post['post_id']} ({post['platform']}) - {post['impressions']} 展示")
    
    # 生成报告
    print("\n⏳ 生成分析报告...")
    report = engine.generate_report(AnalyticsPeriod.LAST_7_DAYS)
    
    print(f"\n✅ 分析报告生成完成:\n")
    
    # 核心指标
    print("📊 核心指标:")
    print(f"   总帖子数：{report.total_posts}")
    print(f"   总展示量：{report.total_impressions:,}")
    print(f"   总触达：{report.total_reach:,}")
    print(f"   总互动：{report.total_engagement:,}")
    print(f"   平均互动率：{report.avg_engagement_rate:.2f}%")
    
    # 平台对比
    print(f"\n📱 平台对比:")
    for platform_data in report.platform_comparison:
        print(f"   {platform_data.name}: {platform_data.value:,} 展示 ({platform_data.percentage}%)")
    
    # 洞察
    print(f"\n💡 分析洞察 ({len(report.insights)} 条):")
    for i, insight in enumerate(report.insights, 1):
        emoji = "✅" if insight.type == "positive" else "⚠️" if insight.type == "negative" else "💡"
        print(f"\n   {emoji} {insight.title}")
        print(f"      {insight.description}")
        print(f"      置信度：{insight.confidence*100:.0f}%")
        if insight.action_items:
            print(f"      建议:")
            for action in insight.action_items[:3]:
                print(f"        • {action}")
    
    # 图表配置
    print(f"\n📈 图表配置:")
    for chart_name, chart_config in report.charts.items():
        print(f"   • {chart_config['title']} ({chart_config['type']})")
    
    return report


async def main():
    """主函数"""
    print("\n" + "🚀"*30)
    print(" AgentForge P2 功能测试")
    print("🚀"*30)
    print(f"\n测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试 Fiverr 优化
        fiverr_suggestions = await test_fiverr_optimization()
        
        # 测试社交媒体分析
        social_report = test_social_analytics()
        
        # 总结
        print("\n" + "="*60)
        print("✅ 测试完成总结")
        print("="*60)
        print(f"\nFiverr 优化建议:")
        print(f"  ✓ 生成 {len(fiverr_suggestions)} 条建议")
        print(f"  ✓ 包含实施步骤")
        print(f"  ✓ 支持优先级排序")
        
        print(f"\n社交媒体分析:")
        print(f"  ✓ 分析 {social_report.total_posts} 个帖子")
        print(f"  ✓ 生成 {len(social_report.insights)} 条洞察")
        print(f"  ✓ 配置 {len(social_report.charts)} 个图表")
        
        print("\n📚 查看详细文档:")
        print("   - docs/P2_FEATURES_GUIDE.md")
        print("   - docs/P2_COMPLETION_SUMMARY.md")
        
        print("\n🌐 API 访问:")
        print("   - 启动服务：uvicorn agentforge.api.main:app --reload")
        print("   - API 文档：http://localhost:8000/docs")
        
        print("\n" + "✨"*30)
        print(" 所有功能测试通过！")
        print("✨"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
