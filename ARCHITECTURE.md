# 架构设计文档

## 项目重构说明

### 重构目标

1. **清晰的分层架构**：路由层、服务层、模型层分离
2. **数据库支持**：从JSON文件迁移到关系型数据库
3. **文件管理优化**：独立的上传目录，引用计数管理
4. **软删除功能**：支持数据恢复
5. **接口规范化**：按功能分类，RESTful风格

### 架构对比

#### 旧架构（单文件）
```
app.py (800+ 行)
├── 数据读写函数
├── 图片上传函数
├── 所有路由处理
└── 业务逻辑混杂
```

#### 新架构（分层）
```
app_new.py (应用工厂)
├── config.py (配置管理)
├── models.py (数据模型)
├── routes/ (路由层)
│   ├── main_routes.py
│   ├── character_routes.py
│   ├── script_routes.py
│   ├── game_routes.py
│   └── api_routes.py
├── services/ (业务逻辑层)
│   ├── character_service.py
│   ├── script_service.py
│   ├── game_service.py
│   └── file_service.py
└── utils/ (工具函数)
    └── constants.py
```

## 分层职责

### 1. 路由层（Routes）
**职责**：
- 处理HTTP请求
- 参数验证和提取
- 调用服务层
- 返回响应（HTML/JSON）

**示例**：
```python
@character_bp.route("/<cid>/delete", methods=["POST"])
def delete_character(cid):
    if CharacterService.soft_delete(cid):
        flash('角色已删除（可恢复）', 'success')
    return redirect(url_for("character.list_characters"))
```

### 2. 服务层（Services）
**职责**：
- 封装业务逻辑
- 数据库操作
- 业务规则验证
- 事务管理

**示例**：
```python
class CharacterService:
    @staticmethod
    def soft_delete(char_id):
        character = CharacterService.get_by_id(char_id)
        if character:
            character.soft_delete()
            db.session.commit()
            return True
        return False
```

### 3. 模型层（Models）
**职责**：
- 定义数据结构
- ORM映射
- 数据验证
- 通用方法（如软删除）

**示例**：
```python
class Character(db.Model, SoftDeleteMixin):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
```

## 核心功能设计

### 1. 软删除机制

**设计思路**：
- 添加 `deleted_at` 字段标记删除时间
- 查询时默认过滤已删除数据
- 提供 `include_deleted` 参数查看所有数据
- 支持恢复和硬删除

**实现**：
```python
class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        self.deleted_at = None
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

### 2. 文件引用计数

**设计思路**：
- 每个上传文件记录引用次数
- 新增引用时计数+1
- 删除引用时计数-1
- 计数为0时自动删除文件

**实现**：
```python
class FileUpload(db.Model):
    filename = db.Column(db.String(255), unique=True)
    reference_count = db.Column(db.Integer, default=0)
    
    def increment_reference(self):
        self.reference_count += 1
    
    def decrement_reference(self):
        if self.reference_count > 0:
            self.reference_count -= 1
```

### 3. 数据迁移

**设计思路**：
- 首次启动自动检测JSON文件
- 仅迁移不存在的数据（避免重复）
- 保留原JSON文件作为备份
- 提供独立迁移脚本

**流程**：
```
1. 检查数据库是否为空
2. 读取JSON文件
3. 逐条检查是否已存在
4. 插入新数据
5. 提交事务
6. 显示统计信息
```

## 接口设计规范

### RESTful风格

| 操作 | HTTP方法 | 路径 | 说明 |
|------|----------|------|------|
| 列表 | GET | /resource/ | 获取资源列表 |
| 详情 | GET | /resource/<id> | 获取单个资源 |
| 创建页面 | GET | /resource/new | 显示创建表单 |
| 创建 | POST | /resource/new | 提交创建 |
| 编辑页面 | GET | /resource/<id>/edit | 显示编辑表单 |
| 更新 | POST | /resource/<id>/edit | 提交更新 |
| 删除 | POST | /resource/<id>/delete | 软删除 |
| 恢复 | POST | /resource/<id>/restore | 恢复 |

### API接口规范

**导出接口**：
- `GET /api/export/characters` - 导出角色
- `GET /api/export/scripts` - 导出剧本
- `GET /api/export/games` - 导出游戏

**导入接口**：
- `POST /api/import/characters` - 导入角色

**回收站接口**：
- `GET /api/trash/characters` - 已删除角色
- `GET /api/trash/scripts` - 已删除剧本
- `GET /api/trash/games` - 已删除游戏

**AJAX接口**：
- `POST /game/<id>/update` - 游戏状态更新（统一接口）

## 数据库设计

### 表结构

#### characters（角色表）
```sql
CREATE TABLE characters (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    type VARCHAR(20) NOT NULL DEFAULT 'townsfolk',
    ability TEXT,
    image VARCHAR(500),
    first_night INTEGER,
    other_nights INTEGER,
    cause_drunk BOOLEAN DEFAULT FALSE,
    cause_poison BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

#### scripts（剧本表）
```sql
CREATE TABLE scripts (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    character_ids TEXT,  -- JSON数组
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

#### games（游戏表）
```sql
CREATE TABLE games (
    id VARCHAR(50) PRIMARY KEY,
    script_id VARCHAR(50) NOT NULL,
    script_name VARCHAR(200),
    seats TEXT,  -- JSON数组
    days TEXT,   -- JSON数组
    status VARCHAR(20) DEFAULT 'active',
    winner VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

#### file_uploads（文件上传表）
```sql
CREATE TABLE file_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) UNIQUE NOT NULL,
    original_name VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reference_count INTEGER DEFAULT 0
);
```

## 部署架构

### 开发环境
```
本地开发
├── SQLite数据库（data/botc.db）
├── 本地文件存储（uploads/）
└── Flask开发服务器
```

### 生产环境（推荐）
```
云平台（Render/Heroku）
├── PostgreSQL数据库
├── 云存储（S3/OSS）
└── Gunicorn + Nginx
```

## 扩展性设计

### 1. 支持多种数据库
通过环境变量 `DATABASE_URL` 切换：
- SQLite：`sqlite:///path/to/db.db`
- PostgreSQL：`postgresql://user:pass@host/db`
- MySQL：`mysql://user:pass@host/db`

### 2. 支持云存储
修改 `FileService` 适配不同存储：
- 本地存储：默认实现
- AWS S3：使用 boto3
- 阿里云OSS：使用 oss2

### 3. 支持缓存
添加 Flask-Caching：
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

### 4. 支持认证
添加 Flask-Login：
```python
from flask_login import LoginManager, login_required
```

## 性能优化

1. **数据库索引**：为常用查询字段添加索引
2. **查询优化**：使用 `select_related` 减少查询次数
3. **缓存策略**：缓存角色列表、剧本列表等静态数据
4. **CDN加速**：静态资源和图片使用CDN
5. **异步任务**：文件上传、数据导出使用后台任务

## 安全考虑

1. **SQL注入防护**：使用ORM参数化查询
2. **XSS防护**：模板自动转义
3. **CSRF防护**：使用Flask-WTF
4. **文件上传安全**：
   - 限制文件类型
   - 限制文件大小
   - 随机文件名
   - 病毒扫描（生产环境）
5. **认证授权**：添加用户系统和权限控制

## 测试策略

1. **单元测试**：测试服务层业务逻辑
2. **集成测试**：测试API接口
3. **端到端测试**：测试完整用户流程
4. **性能测试**：压力测试和负载测试

## 监控和日志

1. **应用日志**：记录关键操作
2. **错误追踪**：使用Sentry
3. **性能监控**：使用New Relic/DataDog
4. **数据库监控**：慢查询日志
