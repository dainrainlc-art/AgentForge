# AgentForge

**Version**: 1.0.0

AgentForge - AI 驱动的 Fiverr 运营自动化智能助理系统

## Auth

### `POST` /api/auth/register

**Register**

*Operation ID*: `register_api_auth_register_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/auth/login

**Login**

*Operation ID*: `login_api_auth_login_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/auth/refresh

**Refresh Token**

*Operation ID*: `refresh_token_api_auth_refresh_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/auth/logout

**Logout**

*Operation ID*: `logout_api_auth_logout_post`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/auth/verify

**Verify Auth**

*Operation ID*: `verify_auth_api_auth_verify_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/auth/me

**Get Current User**

*Operation ID*: `get_current_user_api_auth_me_get`

**Responses**:

- `200` - Successful Response

---

### `POST` /api/auth/change-password

**Change Password**

*Operation ID*: `change_password_api_auth_change_password_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## Backup

### `GET` /api/backup/status

**Get Backup Status**

*Operation ID*: `get_backup_status_api_backup_status_get`

**Responses**:

- `200` - Successful Response

---

### `POST` /api/backup/create

**Create Backup**

*Operation ID*: `create_backup_api_backup_create_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/backup/restore

**Restore Backup**

*Operation ID*: `restore_backup_api_backup_restore_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/backup/list

**List Backups**

*Operation ID*: `list_backups_api_backup_list_get`

**Parameters**:

- `limit` (query, integer)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/backup/{backup_id}

**Get Backup**

*Operation ID*: `get_backup_api_backup__backup_id__get`

**Parameters**:

- `backup_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `DELETE` /api/backup/{backup_id}

**Delete Backup**

*Operation ID*: `delete_backup_api_backup__backup_id__delete`

**Parameters**:

- `backup_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/backup/{backup_id}/verify

**Verify Backup**

*Operation ID*: `verify_backup_api_backup__backup_id__verify_get`

**Parameters**:

- `backup_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/backup/retention/apply

**Apply Retention Policy**

*Operation ID*: `apply_retention_policy_api_backup_retention_apply_post`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/backup/stats/summary

**Get Backup Stats**

*Operation ID*: `get_backup_stats_api_backup_stats_summary_get`

**Responses**:

- `200` - Successful Response

---

### `PUT` /api/backup/schedule

**Update Schedule**

*Operation ID*: `update_schedule_api_backup_schedule_put`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## Chat

### `POST` /api/chat

**Chat**

*Operation ID*: `chat_api_chat_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/chat/message

**Send Message**

*Operation ID*: `send_message_api_chat_message_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/chat/history

**Get History**

*Operation ID*: `get_history_api_chat_history_get`

**Parameters**:

- `conversation_id` (query, string)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `DELETE` /api/chat/history

**Clear History**

*Operation ID*: `clear_history_api_chat_history_delete`

**Parameters**:

- `conversation_id` (query, string)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/chat/status

**Get Agent Status**

*Operation ID*: `get_agent_status_api_chat_status_get`

**Responses**:

- `200` - Successful Response

---

## Config

### `GET` /api/config

**Get Config**

*Operation ID*: `get_config_api_config_get`

**Responses**:

- `200` - Successful Response

---

### `POST` /api/config/test

**Test Config**

*Operation ID*: `test_config_api_config_test_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/config/save

**Save Config**

*Operation ID*: `save_config_api_config_save_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/config/status

**Get Config Status**

*Operation ID*: `get_config_status_api_config_status_get`

**Responses**:

- `200` - Successful Response

---

## Default

### `GET` /

**Root**

*Operation ID*: `root__get`

**Responses**:

- `200` - Successful Response

---

### `POST` /api/docs/generate

**Generate Docs**

*Operation ID*: `generate_docs_api_docs_generate_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## Fiverr

### `GET` /api/fiverr/dashboard

**Get Dashboard Summary**

*Operation ID*: `get_dashboard_summary_api_fiverr_dashboard_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/fiverr/revenue

**Get Revenue Stats**

*Operation ID*: `get_revenue_stats_api_fiverr_revenue_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/fiverr/orders/analytics

**Get Order Analytics**

*Operation ID*: `get_order_analytics_api_fiverr_orders_analytics_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/fiverr/buyers

**Get Buyer Analytics**

*Operation ID*: `get_buyer_analytics_api_fiverr_buyers_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/fiverr/performance

**Get Performance Metrics**

*Operation ID*: `get_performance_metrics_api_fiverr_performance_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/fiverr/charts/revenue

**Get Revenue Chart Data**

*Operation ID*: `get_revenue_chart_data_api_fiverr_charts_revenue_get`

**Parameters**:

- `days` (query, integer)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/fiverr/charts/orders

**Get Order Chart Data**

*Operation ID*: `get_order_chart_data_api_fiverr_charts_orders_get`

**Parameters**:

- `days` (query, integer)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/fiverr/quotation/generate

**Generate Quotation**

*Operation ID*: `generate_quotation_api_fiverr_quotation_generate_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/fiverr/pricing/suggest

**Suggest Pricing**

*Operation ID*: `suggest_pricing_api_fiverr_pricing_suggest_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/fiverr/pricing/market/{category}

**Get Market Data**

*Operation ID*: `get_market_data_api_fiverr_pricing_market__category__get`

**Parameters**:

- `category` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## Health

### `GET` /api/health

**Health Check**

*Operation ID*: `health_check_api_health_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/health/live

**Liveness**

*Operation ID*: `liveness_api_health_live_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/health/ready

**Readiness**

*Operation ID*: `readiness_api_health_ready_get`

**Responses**:

- `200` - Successful Response

---

## Knowledge

### `GET` /api/knowledge

**List Knowledge**

*Operation ID*: `list_knowledge_api_knowledge_get`

**Parameters**:

- `tag` (query, string)
  - Filter by tag
- `source` (query, string)
  - Filter by source

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/knowledge

**Create Knowledge**

*Operation ID*: `create_knowledge_api_knowledge_post`

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/knowledge/search

**Search Knowledge**

*Operation ID*: `search_knowledge_api_knowledge_search_get`

**Parameters**:

- `query` (query, string) **(required)**
  - Search query
- `limit` (query, integer)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/knowledge/{item_id}

**Get Knowledge**

*Operation ID*: `get_knowledge_api_knowledge__item_id__get`

**Parameters**:

- `item_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `PUT` /api/knowledge/{item_id}

**Update Knowledge**

*Operation ID*: `update_knowledge_api_knowledge__item_id__put`

**Parameters**:

- `item_id` (path, string) **(required)**

**Request Body**:

Content-Type: `application/json`


**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `DELETE` /api/knowledge/{item_id}

**Delete Knowledge**

*Operation ID*: `delete_knowledge_api_knowledge__item_id__delete`

**Parameters**:

- `item_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/knowledge/tags/list

**List Tags**

*Operation ID*: `list_tags_api_knowledge_tags_list_get`

**Responses**:

- `200` - Successful Response

---

### `POST` /api/knowledge/sync/{source}

**Sync Knowledge**

*Operation ID*: `sync_knowledge_api_knowledge_sync__source__post`

**Parameters**:

- `source` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## Orders

### `GET` /api/orders

**List Orders**

*Operation ID*: `list_orders_api_orders_get`

**Parameters**:

- `status` (query, string)
  - Filter by status
- `limit` (query, integer)

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `GET` /api/orders/stats

**Get Order Stats**

*Operation ID*: `get_order_stats_api_orders_stats_get`

**Responses**:

- `200` - Successful Response

---

### `GET` /api/orders/{order_id}

**Get Order**

*Operation ID*: `get_order_api_orders__order_id__get`

**Parameters**:

- `order_id` (path, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

### `POST` /api/orders/{order_id}/message

**Send Order Message**

*Operation ID*: `send_order_message_api_orders__order_id__message_post`

**Parameters**:

- `order_id` (path, string) **(required)**
- `message` (query, string) **(required)**

**Responses**:

- `200` - Successful Response
- `422` - Validation Error

---

## 认证方式

### HTTPBearer

- **Type**: http
