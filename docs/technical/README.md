# AgentForge 技术规范文档索引

## 百度千帆 Coding Plan API

### 基本信息
- **套餐**: Coding Plan Pro (¥200/月)
- **API端点**:
  - OpenAI兼容: `https://qianfan.baidubce.com/v2/coding`
  - Anthropic兼容: `https://qianfan.baidubce.com/anthropic/coding`
- **官方文档**: https://cloud.baidu.com/doc/qianfan/s/imlg0beiu

### 可用模型
| 模型 | 特长 | 推荐场景 |
|------|------|----------|
| Kimi-K2.5 | 128K上下文，长文档理解 | 架构设计、技术文档 |
| DeepSeek-V3.2 | 代码能力强 | 代码生成、调试 |
| GLM-5 | 多语言优化 | 内容创作、翻译 |
| MiniMax-M2.5 | 低延迟响应 | 快速交互 |

### 请求限制
- 每5小时: 约6,000次请求
- 每周: 约45,000次请求
- 每月: 约90,000次请求
- 联网搜索: 每月约2,000次

### 使用注意事项
1. 仅限编程工具使用，禁止自动化脚本和批量调用
2. Pro版本建议使用终端数不超过2个
3. 高峰期可能出现限流，建议间隔重试

## Fiverr API

### API状态
- **官方API**: 受限访问，需申请
- **替代方案**: Webhook监控、页面爬虫（需遵守服务条款）

### 关键端点
- 订单管理
- 消息系统
- Gig管理
- 财务数据

## 社交媒体API

### YouTube Data API v3
- **文档**: https://developers.google.com/youtube/v3
- **配额**: 每日10,000单位
- **用途**: 视频上传、频道管理

### Twitter/X API v2
- **文档**: https://developer.twitter.com
- **层级**: Basic/Pro/Enterprise
- **用途**: 推文发布、互动管理

### Facebook Graph API
- **文档**: https://developers.facebook.com/docs/graph-api
- **用途**: 页面管理、内容发布

### Instagram Graph API
- **文档**: https://developers.facebook.com/docs/instagram-api
- **用途**: 内容发布、互动管理

### LinkedIn API
- **文档**: https://learn.microsoft.com/en-us/linkedin/
- **用途**: 个人档案、内容分享

## GitHub API

### REST API
- **文档**: https://docs.github.com/en/rest
- **速率限制**: 5,000次/小时（认证）

### GraphQL API
- **文档**: https://docs.github.com/en/graphql
- **用途**: 复杂查询、批量操作

## 医疗器械法规参考

### IEC 60601
- **范围**: 医疗电气设备安全要求
- **获取**: IEC官网 (https://www.iec.ch)

### FDA 510(k)
- **范围**: 美国医疗器械上市前通知
- **获取**: FDA开放数据 (https://www.fda.gov)

### ISO 14971
- **范围**: 医疗器械风险管理
- **获取**: ISO官网 (https://www.iso.org)

### ISO 13485
- **范围**: 医疗器械质量管理体系
- **获取**: ISO官网
