# NeuralSite 安全审查报告

**审查日期**: 2026-03-05  
**审查范围**: 认证授权、API安全、敏感信息、数据安全、基础设施  
**严重程度**: 🔴高危 | 🟠中危 | 🟡低危 | ✅安全

---

## 一、认证与授权

### 1.1 JWT实现 ✅ 基本安全

| 项目 | 状态 | 说明 |
|------|------|------|
| 算法 | ✅ | 使用HS256（非对称更佳，但HS256在密钥安全情况下可用） |
| 密钥管理 | 🟠 | SECRET_KEY从环境变量获取，但有默认值 |
| 过期时间 | ✅ | 默认24小时（生产环境建议缩短至30-60分钟） |
| 令牌内容 | ✅ | 包含user_id、username、role，无敏感信息 |

**问题**：
```python
# deps.py 第23行
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
```
- 默认密钥太弱，且提示明确

**修复建议**：
```bash
# 生产环境必须使用强密钥
export SECRET_KEY=$(openssl rand -hex 32)
```

### 1.2 密码存储 ✅ 安全

| 项目 | 状态 | 说明 |
|------|------|------|
| 哈希算法 | ✅ | 使用bcrypt（业界标准） |
| salt | ✅ | bcrypt自动处理salt |
| 验证逻辑 | ✅ | 正确使用passlib库 |

```python
# deps.py 第90-95行
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### 1.3 角色权限 🟠 需验证

| 项目 | 状态 | 说明 |
|------|------|------|
| 角色定义 | ✅ | 有UserRole枚举（admin/manager/engineer/worker） |
| 权限装饰器 | ✅ | 实现了`require_role()`装饰器 |
| 实际使用 | 🟡 | 需验证各路由是否正确使用权限检查 |

**潜在问题**：检查代码发现`require_role`装饰器存在，但部分路由可能未使用。

---

## 二、API安全

### 2.1 SQL注入 ✅ 安全

| 项目 | 状态 | 说明 |
|------|------|------|
| ORM使用 | ✅ | 使用SQLAlchemy ORM |
| 参数化查询 | ✅ | 所有查询使用绑定参数 |

```python
# auth.py 示例
user = db.query(User).filter(User.username == request.username).first()
```

### 2.2 XSS风险 ✅ 低风险

| 项目 | 状态 | 说明 |
|------|------|------|
| 响应类型 | ✅ | FastAPI默认返回JSON，非HTML |
| Pydantic验证 | ✅ | 有基础输入验证 |

### 2.3 CSRF保护 ⚠️ 不适用

| 项目 | 状态 | 说明 |
|------|------|------|
| 无状态API | ✅ | JWT无状态，CSRF不适用 |
| 建议 | ✅ | 使用`HttpOnly` Cookie存储token更佳 |

### 2.4 输入验证 🟡 基本验证

| 项目 | 状态 | 说明 |
|------|------|------|
| Pydantic | ✅ | 有基础验证（min_length、max_length） |
| 格式验证 | 🟠 | username有alphanumeric检查，但可以加强 |
| 边界检查 | 🟡 | 缺少对特殊字符的更严格过滤 |

```python
# auth.py 第40-42行
@validator('username')
def username_alphanumeric(cls, v):
    assert v.replace('_', '').replace('-', '').isalnum()
    return v
```

---

## 三、敏感信息

### 3.1 硬编码密钥 🔴 高危

| 文件 | 问题 | 风险 |
|------|------|------|
| `deps.py` | SECRET_KEY默认值为`"your-secret-key-change-in-production"` | Token伪造 |
| `config.py` | SECRET_KEY默认值为`"changeme_generate_with_openssl_rand_hex_32"` | Token伪造 |
| `.env.example` | 包含示例密钥和数据库密码 | 信息泄露 |

```python
# deps.py 第23行
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# config.py 第54行
SECRET_KEY: str = Field(
    default="changeme_generate_with_openssl_rand_hex_32",
    description="应用密钥"
)
```

### 3.2 环境配置 ✅ 已提供模板

| 项目 | 状态 | 说明 |
|------|------|------|
| .env.example | ✅ | 提供完整配置模板 |
| .gitignore | ✅ | 包含.env |
| 生产密钥 | 🔴 | 需确保生产环境使用强随机密钥 |

### 3.3 日志泄露 🟡 需审查

| 项目 | 状态 | 说明 |
|------|------|------|
| SQL日志 | 🟠 | `DATABASE_ECHO=false` 默认为false（安全） |
| 错误处理 | 🟡 | 需确保生产环境不返回详细错误 |

---

## 四、数据安全

### 4.1 文件上传 🟠 中危

| 项目 | 状态 | 说明 |
|------|------|------|
| 文件大小限制 | ✅ | `MAX_FILE_SIZE=52428800` (50MB) |
| 路径存储 | ✅ | 使用相对路径存储 |
| 文件类型检查 | 🔴 | **未验证文件类型** |

```python
# import_routes.py 第25-38行
@router.post("/excel/road")
async def import_excel_road(
    file: UploadFile = File(...)
):
    content = await file.read()
    result = parse_excel_file(content)  # 直接解析，未验证MIME类型
```

**风险**：攻击者可能上传恶意文件（.exe、.sh、.php等）

**修复建议**：
```python
from fastapi import UploadFile, File
from typing import List

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel'
}

async def validate_upload_file(file: UploadFile) -> bool:
    # 验证文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "不允许的文件类型")
    
    # 验证MIME类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "不允许的MIME类型")
    
    return True
```

### 4.2 路径遍历风险 🟡 需检查

| 项目 | 状态 | 说明 |
|------|------|------|
| 文件路径 | 🟡 | 需验证file_path不包含`../`等路径遍历 |

### 4.3 Excel解析安全 🟠 中危

| 项目 | 状态 | 说明 |
|------|------|------|
| 解析库 | 🟡 | 使用openpyxl，需确保版本最新 |
| 宏病毒 | 🟠 | 未禁用Excel宏 |

---

## 五、基础设施

### 5.1 Docker配置 🟠 基本安全

| 项目 | 状态 | 说明 |
|------|------|------|
| 非root用户 | ✅ | 使用`neuralsite`用户 |
| 多阶段构建 | ✅ | 使用builder/production stages |
| 健康检查 | ✅ | 有HEALTHCHECK配置 |

```dockerfile
# Dockerfile 第35-38行
RUN groupadd --gid 1000 neuralsite && \
    useradd --uid 1000 --gid neuralsite --shell /bin/bash --create-home neuralsite

USER neuralsite
```

### 5.2 端口暴露 🔴 高危

| 服务 | 当前配置 | 建议 |
|------|----------|------|
| API | 8000:8000 | 需通过nginx反向代理 |
| PostgreSQL | 5432:5432 | **不应暴露到公网** |
| Redis | 6379:6379 | **不应暴露到公网** |
| Neo4j | 7474,7687 | **不应暴露到公网** |

```yaml
# docker-compose.prod.yml
ports:
  - "5432:5432"  # 🔴 高危 - 数据库不应暴露
  - "6379:6379"  # 🔴 高危 - 缓存不应暴露
```

**修复建议**：
```yaml
# 只暴露必要的端口
ports:
  - "8000:8000"  # API通过nginx代理

# 数据库和Redis使用内部网络
networks:
  - neuralsite-network  # 仅内部访问
```

### 5.3 CORS配置 🔴 高危

```python
# api/main.py 第39-43行
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔴 允许所有来源
    allow_credentials=True,  # 🔴 允许凭据
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**：允许任意来源的跨域请求

**修复建议**：
```python
# 生产环境应配置具体域名
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # ["https://neuralsite.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 风险汇总

| 严重程度 | 数量 | 问题 |
|----------|------|------|
| 🔴 高危 | 4 | 默认密钥弱、CORS开放、端口过度暴露、文件类型未验证 |
| 🟠 中危 | 3 | JWT过期时间、Excel解析安全、路径遍历风险 |
| 🟡 低危 | 2 | 日志泄露检查、权限装饰器使用 |

---

## 修复优先级

### P0 - 立即修复

1. **修改默认SECRET_KEY**
   ```bash
   # 生产环境必须
   export SECRET_KEY=$(openssl rand -hex 32)
   export JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **修复CORS配置**
   ```python
   # api/main.py
   allow_origins=["https://your-domain.com"],  # 非"*"
   ```

3. **关闭数据库/Redis端口暴露**
   ```yaml
   # docker-compose.prod.yml
   db:
     ports:
       - "127.0.0.1:5432:5432"  # 仅本地访问
   ```

### P1 - 高优先级

4. **添加文件上传类型验证**
5. **缩短JWT过期时间**（30分钟）
6. **配置生产环境日志级别**

### P2 - 建议改进

7. 添加请求速率限制
8. 添加API审计日志
9. 考虑使用JWT Refresh Token机制

---

## 审查结论

NeuralSite在认证和密码存储方面做得较好（使用bcrypt和JWT），但存在**4个高危问题**需要立即修复：

1. **CORS完全开放** - 允许任意来源访问
2. **默认密钥未修改** - 容易被利用
3. **数据库端口暴露** - 严重安全风险
4. **文件上传无类型验证** - 可能被上传恶意文件

建议立即修复P0级别问题后再上线生产环境。
