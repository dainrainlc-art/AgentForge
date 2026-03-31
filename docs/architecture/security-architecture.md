# AgentForge 安全架构设计

## 1. 数据安全架构

### 1.1 数据分类分级

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            数据分类体系                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  敏感数据 (Sensitive) - 最高保护级别                                         │
│                                                                              │
│  • 客户个人信息 (姓名、邮箱、电话)                                           │
│  • 支付信息 (银行账户、交易记录)                                             │
│  • API密钥和认证凭证                                                        │
│  • 商业机密 (报价策略、客户名单)                                             │
│  • 源代码和知识产权                                                         │
│                                                                              │
│  保护措施: 加密存储 + 访问控制 + 审计日志                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  内部数据 (Internal) - 中等保护级别                                          │
│                                                                              │
│  • 项目文档和设计资料                                                       │
│  • 客户沟通记录                                                             │
│  • 系统配置信息                                                             │
│  • 工作流定义                                                               │
│  • 运营统计数据                                                             │
│                                                                              │
│  保护措施: 访问控制 + 审计日志                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  公开数据 (Public) - 基础保护级别                                            │
│                                                                              │
│  • 已发布的社交媒体内容                                                     │
│  • 公开的个人Profile                                                        │
│  • 产品介绍和案例展示                                                       │
│                                                                              │
│  保护措施: 完整性校验                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 敏感数据加密方案

**传输加密**:
```
客户端 ──────[TLS 1.3]──────► 服务端
         │              │
         │  加密通道    │
         │  证书验证    │
         │  前向保密    │
         └──────────────┘
```

**存储加密**:
```python
class DataEncryption:
    """数据加密管理"""
    
    ALGORITHM = "AES-256-GCM"
    KEY_DERIVATION = "PBKDF2"
    ITERATIONS = 100000
    
    @staticmethod
    def encrypt(plaintext: str, key: bytes) -> EncryptedData:
        """加密数据"""
        salt = os.urandom(16)
        nonce = os.urandom(12)
        
        derived_key = pbkdf2_hmac(
            'sha256',
            key,
            salt,
            DataEncryption.ITERATIONS
        )
        
        cipher = AES.new(derived_key, AES.MODE_GCM, nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        
        return EncryptedData(
            ciphertext=ciphertext,
            salt=salt,
            nonce=nonce,
            tag=tag
        )
    
    @staticmethod
    def decrypt(encrypted_data: EncryptedData, key: bytes) -> str:
        """解密数据"""
        derived_key = pbkdf2_hmac(
            'sha256',
            key,
            encrypted_data.salt,
            DataEncryption.ITERATIONS
        )
        
        cipher = AES.new(
            derived_key, 
            AES.MODE_GCM, 
            encrypted_data.nonce
        )
        plaintext = cipher.decrypt_and_verify(
            encrypted_data.ciphertext,
            encrypted_data.tag
        )
        
        return plaintext.decode()
```

**字段级加密**:
```python
ENCRYPTED_FIELDS = {
    "customers": ["email", "phone", "company"],
    "orders": ["customer_email", "delivery_notes"],
    "api_keys": ["key", "secret"]
}
```

### 1.3 密钥管理方案

**密钥层次结构**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  主密钥 (Master Key)                                                         │
│  • 存储位置: 环境变量 / 硬件安全模块                                         │
│  • 用途: 加密数据加密密钥                                                   │
│  • 轮换周期: 90天                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  数据加密密钥 (DEK)                                                          │
│  • 存储位置: 数据库 (加密后)                                                 │
│  • 用途: 加密实际数据                                                       │
│  • 轮换周期: 30天                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**密钥轮换流程**:
```python
async def rotate_keys():
    """密钥轮换"""
    # 1. 生成新密钥
    new_dek = generate_key()
    
    # 2. 用主密钥加密新密钥
    encrypted_new_dek = encrypt_with_master_key(new_dek)
    
    # 3. 重新加密所有数据
    for record in get_all_encrypted_records():
        plaintext = decrypt(record, old_dek)
        new_ciphertext = encrypt(plaintext, new_dek)
        update_record(record.id, new_ciphertext)
    
    # 4. 更新密钥存储
    store_encrypted_dek(encrypted_new_dek)
    
    # 5. 安全删除旧密钥
    secure_delete(old_dek)
```

### 1.4 数据脱敏方案

**脱敏规则**:
```python
MASKING_RULES = {
    "email": {
        "pattern": r"(.{2})(.*)(@.*)",
        "replacement": r"\1***\3"
    },
    "phone": {
        "pattern": r"(\d{3})(\d{4})(\d{4})",
        "replacement": r"\1****\3"
    },
    "credit_card": {
        "pattern": r"(\d{4})(\d{8})(\d{4})",
        "replacement": r"\1********\3"
    },
    "name": {
        "pattern": r"(.)[a-zA-Z]*(.)",
        "replacement": r"\1*\2"
    }
}

def mask_field(value: str, field_type: str) -> str:
    """脱敏字段"""
    rule = MASKING_RULES.get(field_type)
    if rule:
        return re.sub(rule["pattern"], rule["replacement"], value)
    return "***"
```

### 1.5 安全审计日志

**审计事件类型**:
| 事件类型 | 描述 | 日志级别 |
|----------|------|----------|
| AUTH_LOGIN | 用户登录 | INFO |
| AUTH_LOGOUT | 用户登出 | INFO |
| AUTH_FAILED | 认证失败 | WARNING |
| DATA_ACCESS | 数据访问 | INFO |
| DATA_MODIFY | 数据修改 | INFO |
| DATA_DELETE | 数据删除 | WARNING |
| DATA_EXPORT | 数据导出 | WARNING |
| API_CALL | API调用 | DEBUG |
| CONFIG_CHANGE | 配置变更 | WARNING |
| ERROR | 错误事件 | ERROR |

**审计日志格式**:
```json
{
  "event_id": "uuid",
  "timestamp": "2026-03-26T10:00:00Z",
  "event_type": "DATA_ACCESS",
  "severity": "INFO",
  "actor": {
    "type": "user|agent|system",
    "id": "identifier",
    "ip_address": "192.168.1.1"
  },
  "resource": {
    "type": "order|customer|content",
    "id": "resource_id",
    "sensitivity": "sensitive|internal|public"
  },
  "action": {
    "operation": "read|create|update|delete",
    "details": {}
  },
  "context": {
    "request_id": "uuid",
    "session_id": "uuid",
    "user_agent": "..."
  },
  "result": {
    "status": "success|failure",
    "error": null
  }
}
```

## 2. 访问控制架构

### 2.1 API认证机制

**认证方式**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            认证方式选择                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  API Key认证 (服务间调用)                                                    │
│                                                                              │
│  Header: X-API-Key: <api_key>                                               │
│  适用场景: N8N → AgentForge Core                                            │
│           外部系统集成                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  JWT认证 (用户会话)                                                          │
│                                                                              │
│  Header: Authorization: Bearer <jwt_token>                                  │
│  适用场景: Web界面、桌面客户端                                               │
│  有效期: 24小时 (可刷新)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  OAuth 2.0 (第三方授权)                                                      │
│                                                                              │
│  适用场景: 社交媒体API、GitHub、Notion                                       │
│  流程: 授权码模式                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**JWT Token结构**:
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "iat": 1709337600,
    "exp": 1709424000,
    "roles": ["admin", "user"],
    "permissions": ["read:orders", "write:orders"]
  },
  "signature": "..."
}
```

### 2.2 权限管理模型

**RBAC模型**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RBAC权限模型                                      │
└─────────────────────────────────────────────────────────────────────────────┘

用户 (User)
    │
    │ 属于
    ▼
角色 (Role)
    │
    │ 拥有
    ▼
权限 (Permission)
    │
    │ 作用于
    ▼
资源 (Resource)
```

**角色定义**:
| 角色 | 描述 | 权限 |
|------|------|------|
| admin | 系统管理员 | 所有权限 |
| operator | 运营人员 | 订单管理、客户管理、内容管理 |
| viewer | 只读用户 | 查看权限 |

**权限定义**:
```python
PERMISSIONS = {
    # 订单权限
    "orders:read": "查看订单",
    "orders:create": "创建订单",
    "orders:update": "更新订单",
    "orders:delete": "删除订单",
    "orders:deliver": "交付订单",
    
    # 客户权限
    "customers:read": "查看客户",
    "customers:create": "创建客户",
    "customers:update": "更新客户",
    "customers:delete": "删除客户",
    
    # 内容权限
    "content:read": "查看内容",
    "content:create": "创建内容",
    "content:publish": "发布内容",
    "content:delete": "删除内容",
    
    # 系统权限
    "system:config": "系统配置",
    "system:logs": "查看日志",
    "system:backup": "数据备份"
}
```

### 2.3 操作审计机制

**审计流程**:
```
请求 ──► 认证 ──► 授权 ──► 执行 ──► 记录日志
           │         │         │
           ▼         ▼         ▼
        认证日志   授权日志   操作日志
```

**审计检查点**:
```python
class AuditMiddleware:
    """审计中间件"""
    
    async def process_request(self, request: Request):
        # 1. 记录请求信息
        await self.log_request(request)
        
        # 2. 验证认证
        user = await self.authenticate(request)
        if not user:
            await self.log_auth_failure(request)
            raise AuthenticationError()
        
        # 3. 检查授权
        if not await self.authorize(user, request):
            await self.log_authz_failure(request, user)
            raise AuthorizationError()
        
        # 4. 执行请求
        response = await self.execute(request)
        
        # 5. 记录操作日志
        await self.log_operation(request, response, user)
        
        return response
```

### 2.4 安全告警机制

**告警规则**:
```python
ALERT_RULES = {
    "auth_failures": {
        "condition": "count > 5 in 5 minutes",
        "severity": "high",
        "action": "lock_account + notify"
    },
    "suspicious_access": {
        "condition": "access from new location",
        "severity": "medium",
        "action": "notify"
    },
    "data_export": {
        "condition": "export > 100 records",
        "severity": "medium",
        "action": "notify + log"
    },
    "api_abuse": {
        "condition": "rate_limit_exceeded",
        "severity": "low",
        "action": "throttle + log"
    }
}
```

**告警通知渠道**:
- 桌面通知
- Telegram消息
- 邮件通知 (高优先级)

## 3. 安全配置清单

### 3.1 环境变量安全

```bash
# 敏感配置 - 必须通过环境变量设置
QIANFAN_API_KEY=***        # 百度千帆API密钥
POSTGRES_PASSWORD=***      # 数据库密码
N8N_PASSWORD=***           # N8N管理密码
SECRET_KEY=***             # 应用密钥
ENCRYPTION_KEY=***         # 数据加密密钥

# OAuth配置
GITHUB_TOKEN=***
NOTION_API_KEY=***
TWITTER_API_KEY=***
```

### 3.2 安全配置检查

```yaml
security_checklist:
  transport:
    - TLS 1.3 enabled
    - Certificate valid
    - HSTS header set
  
  authentication:
    - Strong password policy
    - Session timeout configured
    - Brute force protection
  
  authorization:
    - RBAC implemented
    - Least privilege principle
    - Resource access control
  
  data_protection:
    - Sensitive data encrypted
    - Backup encrypted
    - Data masking for logs
  
  monitoring:
    - Audit logging enabled
    - Alert rules configured
    - Incident response plan
```
