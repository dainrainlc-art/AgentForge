# AgentForge P2 功能使用指南

本指南介绍 P2 阶段新增的两个完整功能：Fiverr 主页优化建议和社交媒体效果分析增强。

---

## 📋 目录

1. [Fiverr 主页优化建议](#1-fiverr-主页优化建议)
2. [社交媒体效果分析增强](#2-社交媒体效果分析增强)
3. [API 集成示例](#3-api-集成示例)
4. [最佳实践](#4-最佳实践)

---

## 1. Fiverr 主页优化建议

### 功能概述

使用 AI 分析 Fiverr 卖家主页数据，自动生成优化建议，帮助提升业绩表现。

**核心特性**:
- ✅ AI 智能分析（基于 GLM-5）
- ✅ 5 个维度的优化建议
- ✅ 优先级排序
- ✅ 具体实施步骤
- ✅ 进度跟踪

### 数据模型

#### OptimizationCategory（优化类别）
- `PROFILE` - 个人资料优化
- `GIG` - Gig 优化
- `PRICING` - 定价策略
- `MARKETING` - 营销推广
- `CUSTOMER_SERVICE` - 客户服务

#### Priority（优先级）
- `CRITICAL` - 紧急
- `HIGH` - 高
- `MEDIUM` - 中
- `LOW` - 低

### API 使用

#### 1.1 分析主页并生成建议

```http
POST /api/fiverr/optimization/analyze
Content-Type: application/json
```

**请求示例**:
```json
{
  "username": "my_seller_account",
  "level": "Level 2 Seller",
  "rating": 4.3,
  "total_reviews": 85,
  "total_orders": 120,
  "completion_rate": 92,
  "on_time_delivery": 88,
  "response_time": 3.5,
  "gigs_count": 4,
  "total_earnings": 5000.0,
  "profile_views": 2500,
  "gig_impressions": 8000,
  "gig_clicks": 120,
  "orders_in_queue": 2
}
```

**响应示例**:
```json
{
  "success": true,
  "username": "my_seller_account",
  "suggestions_count": 5,
  "suggestions": [
    {
      "id": "a1b2c3d4",
      "category": "customer_service",
      "title": "提升准时交付率",
      "description": "当前准时交付率 88%，建议提升至 95% 以上",
      "priority": "high",
      "expected_impact": "提升客户满意度和复购率",
      "implementation_steps": [
        "设置更宽松的交付时间",
        "提前开始工作",
        "使用提醒工具",
        "如遇延误提前沟通"
      ],
      "status": "pending"
    }
  ]
}
```

#### 1.2 获取优化建议

```http
GET /api/fiverr/optimization/suggestions/{username}?category=gig&priority=high&status=pending
```

**查询参数**:
- `category` (可选): 过滤类别
- `priority` (可选): 过滤优先级
- `status` (可选): 过滤状态

**响应示例**:
```json
{
  "success": true,
  "count": 2,
  "suggestions": [
    {
      "id": "s1",
      "category": "gig",
      "title": "优化 Gig 主图",
      "priority": "high",
      "status": "pending"
    }
  ]
}
```

#### 1.3 更新建议状态

```http
PATCH /api/fiverr/optimization/suggestions/{username}/{suggestion_id}
Content-Type: application/json
```

**请求示例**:
```json
{
  "status": "in_progress"
}
```

**可用状态**:
- `pending` - 待处理
- `in_progress` - 进行中
- `completed` - 已完成
- `rejected` - 已拒绝

#### 1.4 获取进度报告

```http
GET /api/fiverr/optimization/progress/{username}
```

**响应示例**:
```json
{
  "success": true,
  "username": "my_seller_account",
  "report": {
    "total_suggestions": 10,
    "by_status": {
      "pending": 5,
      "in_progress": 3,
      "completed": 2,
      "rejected": 0
    },
    "by_category": {
      "profile": 2,
      "gig": 4,
      "pricing": 1,
      "marketing": 2,
      "customer_service": 1
    },
    "by_priority": {
      "critical": 1,
      "high": 3,
      "medium": 4,
      "low": 2
    }
  }
}
```

### Python SDK 使用

```python
from agentforge.fiverr.optimization import FiverrOptimizationEngine, FiverrProfileData

# 创建引擎
engine = FiverrOptimizationEngine()

# 准备数据
profile = FiverrProfileData(
    username="my_account",
    rating=4.5,
    total_reviews=100,
    completion_rate=95,
    response_time=2.0,
    gig_impressions=10000,
    gig_clicks=200
)

# 生成建议
suggestions = await engine.analyze_profile(profile)

# 获取建议
all_suggestions = engine.get_suggestions()
high_priority = engine.get_suggestions(priority=Priority.HIGH)

# 更新状态
engine.update_suggestion_status("suggestion_id", "completed")

# 获取报告
report = engine.get_progress_report()
```

---

## 2. 社交媒体效果分析增强

### 功能概述

提供 8 个维度的数据分析、AI 智能洞察和可视化图表配置。

**核心特性**:
- ✅ 8 个分析维度
- ✅ 时间趋势分析
- ✅ 平台对比分析
- ✅ AI 智能洞察
- ✅ 可视化图表配置
- ✅ 可导出报告

### 分析维度

1. **时间趋势** - 展示量、互动量、粉丝数随时间变化
2. **平台对比** - 各社交平台表现对比
3. **内容类型** - 图文、视频、链接的表现
4. **受众分析** - 受众特征和行为
5. **互动分析** - 点赞、评论、分享等互动指标
6. **转化分析** - 点击、转化等指标
7. **标签分析** - Hashtag 效果分析
8. **发布时间** - 最佳发布时间分析

### API 使用

#### 2.1 添加帖子指标

```http
POST /api/social/analytics/metrics?user_id=user123
Content-Type: application/json
```

**请求示例**:
```json
{
  "post_id": "post_001",
  "platform": "twitter",
  "impressions": 5000,
  "reach": 3500,
  "engagement": 250,
  "likes": 180,
  "comments": 45,
  "shares": 25,
  "clicks": 120,
  "engagement_rate": 5.0,
  "click_through_rate": 2.4
}
```

#### 2.2 生成分析报告

```http
GET /api/social/analytics/report/{user_id}?period=7d&platforms=twitter,linkedin
```

**查询参数**:
- `period`: 分析周期 (24h, 7d, 30d, 90d)
- `platforms`: 平台列表（逗号分隔）

**响应示例**:
```json
{
  "success": true,
  "user_id": "user123",
  "period": "7d",
  "report": {
    "report_id": "report_20240101_120000",
    "total_posts": 15,
    "total_impressions": 50000,
    "total_reach": 35000,
    "total_engagement": 2500,
    "avg_engagement_rate": 5.0,
    "impression_trend": [
      {"date": "2024-01-01", "value": 5000, "label": "5000 展示"},
      {"date": "2024-01-02", "value": 6000, "label": "6000 展示"}
    ],
    "engagement_trend": [...],
    "platform_comparison": [
      {"name": "twitter", "value": 30000, "percentage": 60.0, "color": "#1DA1F2"},
      {"name": "linkedin", "value": 20000, "percentage": 40.0, "color": "#0077B5"}
    ],
    "insights": [
      {
        "title": "出色的互动率",
        "description": "平均互动率 5.0%，远高于行业平均水平（2-3%）",
        "type": "positive",
        "confidence": 0.9,
        "action_items": [
          "保持当前的内容策略",
          "分析高互动帖子的共同特征"
        ]
      }
    ],
    "charts": {...}
  }
}
```

#### 2.3 获取分析洞察

```http
GET /api/social/analytics/insights/{user_id}?period=30d
```

**响应示例**:
```json
{
  "success": true,
  "insights_count": 3,
  "insights": [
    {
      "title": "互动率偏低",
      "description": "平均互动率 0.8%，低于行业平均水平",
      "type": "negative",
      "confidence": 0.85,
      "action_items": [
        "优化帖子标题和配图",
        "增加互动性问题",
        "调整发布时间"
      ]
    },
    {
      "title": "展示量呈上升趋势",
      "description": "近期展示量较前期有明显增长",
      "type": "positive",
      "confidence": 0.8
    },
    {
      "title": "优化发布时间建议",
      "description": "数据分析显示特定时间段发布效果更好",
      "type": "recommendation",
      "confidence": 0.7,
      "action_items": [
        "在工作日早上 8-9 点发布重要内容",
        "周末下午安排轻松话题"
      ]
    }
  ]
}
```

#### 2.4 获取趋势数据

```http
GET /api/social/analytics/trends/{user_id}?metric_type=impressions
```

**查询参数**:
- `metric_type`: impressions, engagement, followers

**响应示例**:
```json
{
  "success": true,
  "metric_type": "impressions",
  "trends": [
    {"date": "2024-01-01", "value": 5000, "label": "5000 展示"},
    {"date": "2024-01-02", "value": 6000, "label": "6000 展示"},
    {"date": "2024-01-03", "value": 5500, "label": "5500 展示"}
  ]
}
```

#### 2.5 获取对比数据

```http
GET /api/social/analytics/comparison/{user_id}
```

**响应示例**:
```json
{
  "success": true,
  "platform_comparison": [
    {"name": "twitter", "value": 30000, "percentage": 60.0, "color": "#1DA1F2"},
    {"name": "linkedin", "value": 20000, "percentage": 40.0, "color": "#0077B5"}
  ],
  "content_type_performance": [
    {"name": "图文", "value": 60, "percentage": 60.0, "color": "#4CAF50"},
    {"name": "视频", "value": 30, "percentage": 30.0, "color": "#2196F3"},
    {"name": "链接", "value": 10, "percentage": 10.0, "color": "#FF9800"}
  ]
}
```

#### 2.6 获取图表配置

```http
GET /api/social/analytics/charts/{user_id}
```

**响应示例**:
```json
{
  "success": true,
  "charts": {
    "impression_trend_chart": {
      "type": "line",
      "title": "展示量趋势",
      "data": [...],
      "color": "#4CAF50"
    },
    "platform_comparison_chart": {
      "type": "pie",
      "title": "平台表现对比",
      "data": [...]
    }
  }
}
```

#### 2.7 导出报告

```http
POST /api/social/analytics/export/{user_id}?period=30d&format=json
```

---

## 3. API 集成示例

### 3.1 完整工作流示例

```python
import httpx
import asyncio

async def complete_workflow():
    base_url = "http://localhost:8000"
    
    # 1. Fiverr 主页分析
    async with httpx.AsyncClient() as client:
        # 分析主页
        response = await client.post(
            f"{base_url}/api/fiverr/optimization/analyze",
            json={
                "username": "my_shop",
                "rating": 4.5,
                "total_reviews": 100,
                "completion_rate": 95,
                "response_time": 2.0,
                "gig_impressions": 10000,
                "gig_clicks": 200
            }
        )
        suggestions = response.json()["suggestions"]
        
        # 获取高优先级建议
        response = await client.get(
            f"{base_url}/api/fiverr/optimization/suggestions/my_shop",
            params={"priority": "high"}
        )
        high_priority = response.json()["suggestions"]
        
        # 实施建议后更新状态
        for suggestion in high_priority:
            await client.patch(
                f"{base_url}/api/fiverr/optimization/suggestions/my_shop/{suggestion['id']}",
                json={"status": "completed"}
            )
    
    # 2. 社交媒体数据分析
    async with httpx.AsyncClient() as client:
        # 添加多个帖子数据
        posts_data = [
            {"post_id": "p1", "platform": "twitter", "impressions": 5000, "engagement": 250},
            {"post_id": "p2", "platform": "twitter", "impressions": 6000, "engagement": 300},
            {"post_id": "p3", "platform": "linkedin", "impressions": 4000, "engagement": 200}
        ]
        
        for post in posts_data:
            await client.post(
                f"{base_url}/api/social/analytics/metrics",
                params={"user_id": "user123"},
                json=post
            )
        
        # 生成报告
        response = await client.get(
            f"{base_url}/api/social/analytics/report/user123?period=7d"
        )
        report = response.json()["report"]
        
        # 获取洞察
        response = await client.get(
            f"{base_url}/api/social/analytics/insights/user123?period=7d"
        )
        insights = response.json()["insights"]
        
        # 获取图表配置
        response = await client.get(
            f"{base_url}/api/social/analytics/charts/user123"
        )
        charts = response.json()["charts"]
        
        print(f"生成{len(insights)}条洞察")
        print(f"有{len(charts)}个图表配置")

asyncio.run(complete_workflow())
```

### 3.2 前端集成示例（React）

```tsx
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

function Dashboard() {
  const [insights, setInsights] = useState([]);
  const [charts, setCharts] = useState({});
  
  useEffect(() => {
    loadAnalytics();
  }, []);
  
  const loadAnalytics = async () => {
    // 加载洞察
    const insightsRes = await axios.get(
      `${API_BASE}/api/social/analytics/insights/user123?period=7d`
    );
    setInsights(insightsRes.data.insights);
    
    // 加载图表
    const chartsRes = await axios.get(
      `${API_BASE}/api/social/analytics/charts/user123`
    );
    setCharts(chartsRes.data.charts);
  };
  
  return (
    <div>
      <h1>分析洞察</h1>
      {insights.map(insight => (
        <div key={insight.title} className={`insight ${insight.type}`}>
          <h3>{insight.title}</h3>
          <p>{insight.description}</p>
          <ul>
            {insight.action_items.map(item => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
      
      <h1>数据图表</h1>
      {Object.entries(charts).map(([key, chart]) => (
        <div key={key}>
          <h3>{chart.title}</h3>
          {/* 使用 Recharts 或其他图表库渲染 */}
        </div>
      ))}
    </div>
  );
}
```

---

## 4. 最佳实践

### 4.1 Fiverr 优化建议

1. **定期分析**: 每周运行一次主页分析
2. **优先级处理**: 先处理紧急和高优先级建议
3. **跟踪进度**: 及时更新建议状态
4. **持续优化**: 根据实施效果调整策略

### 4.2 社交媒体分析

1. **数据收集**: 
   - 每天收集帖子数据
   - 确保数据准确性
   
2. **分析周期**:
   - 短期：24 小时（监控突发情况）
   - 中期：7 天（常规分析）
   - 长期：30-90 天（趋势分析）

3. **洞察应用**:
   - 重视高置信度的洞察
   - 优先执行具体的行动建议
   - A/B 测试优化策略

4. **可视化**:
   - 使用提供的图表配置
   - 关注趋势而非单点数据
   - 定期对比不同平台表现

### 4.3 性能优化

1. **缓存策略**: 报告数据缓存 1 小时
2. **批量处理**: 批量添加指标数据
3. **增量更新**: 只更新变化的数据
4. **异步处理**: 使用异步 API 调用

---

## 5. 故障排除

### 常见问题

**Q: AI 建议生成失败？**
- 检查 API Key 配置
- 确保网络连接正常
- 查看日志获取详细错误

**Q: 分析报告为空？**
- 确认已添加足够的数据
- 检查时间范围是否正确
- 验证平台名称是否匹配

**Q: 图表不显示？**
- 检查图表配置格式
- 确保前端图表库已安装
- 验证数据格式是否正确

---

## 6. 更新日志

### v1.0.0 (2024-01-01)
- ✅ Fiverr 主页优化建议功能上线
- ✅ 社交媒体分析增强功能上线
- ✅ 8 个分析维度
- ✅ AI 智能洞察
- ✅ 可视化图表配置

---

## 7. 联系支持

如有问题或建议，请联系开发团队。
