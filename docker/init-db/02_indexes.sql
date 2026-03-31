-- ==========================================
-- AgentForge 数据库性能优化索引脚本
-- 创建日期：2026-03-29
-- 目标：提升查询性能，减少查询时间
-- ==========================================

-- ==========================================
-- 1. 任务表索引优化
-- ==========================================

-- 状态索引 - 用于按状态筛选任务
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- 创建时间索引 - 用于按时间排序和筛选
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- 用户 ID 索引 - 用于按用户筛选任务
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- 复合索引：状态 + 创建时间 - 优化常见查询组合
CREATE INDEX IF NOT EXISTS idx_tasks_status_created_at ON tasks(status, created_at DESC);

-- 复合索引：用户 ID + 状态 - 优化用户任务查询
CREATE INDEX IF NOT EXISTS idx_tasks_user_id_status ON tasks(user_id, status);

-- ==========================================
-- 2. 记忆表索引优化
-- ==========================================

-- 类型索引 - 用于按类型筛选记忆
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);

-- 创建时间索引 - 用于按时间排序
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);

-- 复合索引：类型 + 创建时间 - 优化类型查询
CREATE INDEX IF NOT EXISTS idx_memories_type_created_at ON memories(type, created_at DESC);

-- ==========================================
-- 3. 错误日志表索引优化
-- ==========================================

-- 创建时间索引 - 用于按时间筛选错误日志
CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at DESC);

-- 严重级别索引 - 用于按级别筛选
CREATE INDEX IF NOT EXISTS idx_errors_severity ON errors(severity);

-- 复合索引：创建时间 + 严重级别 - 优化时间范围内的严重错误查询
CREATE INDEX IF NOT EXISTS idx_errors_created_at_severity ON errors(created_at DESC, severity);

-- ==========================================
-- 4. 技能表索引优化
-- ==========================================

-- 技能类型索引 - 用于按类型筛选技能
CREATE INDEX IF NOT EXISTS idx_skills_type ON skills(type);

-- 更新时间索引 - 用于获取最新技能
CREATE INDEX IF NOT EXISTS idx_skills_updated_at ON skills(updated_at DESC);

-- ==========================================
-- 5. 订单项表索引优化
-- ==========================================

-- 订单 ID 索引 - 用于关联查询
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_order_items_created_at ON order_items(created_at DESC);

-- ==========================================
-- 6. 社交媒体帖子表索引优化
-- ==========================================

-- 平台索引 - 用于按平台筛选
CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_posts(platform);

-- 状态索引 - 用于按状态筛选
CREATE INDEX IF NOT EXISTS idx_social_posts_status ON social_posts(status);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_social_posts_created_at ON social_posts(created_at DESC);

-- 复合索引：平台 + 状态
CREATE INDEX IF NOT EXISTS idx_social_posts_platform_status ON social_posts(platform, status);

-- ==========================================
-- 7. 知识文档表索引优化
-- ==========================================

-- 类型索引
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_type ON knowledge_docs(type);

-- 状态索引
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_status ON knowledge_docs(status);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_created_at ON knowledge_docs(created_at DESC);

-- ==========================================
-- 8. 用户表索引优化
-- ==========================================

-- 邮箱索引 - 用于登录查询（如果存在该表）
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 用户名索引
-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ==========================================
-- 9. 会话表索引优化
-- ==========================================

-- 用户 ID 索引
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- 过期时间索引
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ==========================================
-- 10. 向量索引优化 (Qdrant)
-- ==========================================
-- 注意：Qdrant 的向量索引需要通过 Qdrant API 创建
-- 示例：
-- PUT /collections/{collection_name}/index
-- {
--   "field_name": "vector",
--   "field_schema": "vector"
-- }

-- ==========================================
-- 11. 物化视图 (可选)
-- ==========================================

-- 任务统计物化视图
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_task_statistics AS
-- SELECT 
--     user_id,
--     status,
--     COUNT(*) as task_count,
--     MAX(created_at) as last_task_at
-- FROM tasks
-- GROUP BY user_id, status;

-- 刷新物化视图的函数
-- CREATE OR REPLACE FUNCTION refresh_task_statistics()
-- RETURNS void AS $$
-- BEGIN
--     REFRESH MATERIALIZED VIEW mv_task_statistics;
-- END;
-- $$ LANGUAGE plpgsql;

-- ==========================================
-- 12. 查询性能分析
-- ==========================================
-- 使用 EXPLAIN ANALYZE 分析慢查询
-- 示例：
-- EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at DESC;

-- 查看索引使用情况
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;

-- 查看表大小和索引大小
-- SELECT 
--     relname AS table_name,
--     pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
--     pg_size_pretty(pg_relation_size(relid)) AS table_size,
--     pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
-- FROM pg_catalog.pg_statio_user_tables
-- ORDER BY pg_total_relation_size(relid) DESC;

-- ==========================================
-- 13. 数据库配置优化建议
-- ==========================================
-- 在 postgresql.conf 中调整以下参数：

-- shared_buffers = 256MB  # 推荐为系统内存的 25%
-- effective_cache_size = 768MB  # 推荐为系统内存的 75%
-- work_mem = 16MB  # 每个操作的内存
-- maintenance_work_mem = 128MB  # 维护操作的内存
-- max_connections = 100  # 最大连接数
-- random_page_cost = 1.1  # SSD 推荐值

-- ==========================================
-- 14. 连接池配置 (PgBouncer)
-- ==========================================
-- 使用 PgBouncer 进行连接池管理
-- 配置示例：
-- [databases]
-- agentforge = host=localhost port=5432 dbname=agentforge
-- 
-- [pgbouncer]
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 20

-- ==========================================
-- 执行统计
-- ==========================================
-- 创建索引后，统计信息会自动更新
-- 手动更新统计信息：
ANALYZE;

-- 查看索引创建结果
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
