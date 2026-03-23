# 血染钟楼 · 说书人助手（重构版）

## 项目架构

```
botc-assistant-py/
├── app_new.py              # 新版应用入口
├── config.py               # 配置管理
├── models.py               # 数据模型
├── routes/                 # 路由层（按功能分模块）
│   ├── __init__.py
│   ├── main_routes.py      # 主页路由
│   ├── character_routes.py # 角色管理路由
│   ├── script_routes.py    # 剧本管理路由
│   ├── game_routes.py      # 游戏管理路由
│   └── api_routes.py       # API接口路由
├── services/               # 业务逻辑层
│   ├── __init__.py
│   ├── character_service.py
│   ├── script_service.py
│   ├── game_service.py
│   └── file_service.py
├── templates/              # 模板文件
├── static/                 # 静态资源
├── uploads/                # 用户上传文件（不提交到Git）
└── data/                   # 数据库文件（不提交到Git）
```

## 核心改进

### 1. 分层架构
- **路由层（Routes）**：处理HTTP请求和响应
- **服务层（Services）**：封装业务逻辑
- **模型层（Models）**：数据库模型定义

### 2. 数据库支持
- 使用 SQLite（开发）/ PostgreSQL（生产）
- 支持从旧JSON文件自动迁移数据
- 数据持久化到数据库，不再保存在代码目录

### 3. 文件管理
- 上传文件保存到 `uploads/` 目录（独立于代码）
- 文件引用计数管理，自动清理未使用文件
- 支持URL和本地文件两种方式

### 4. 软删除功能
- 所有删除操作默认为软删除（标记 deleted_at）
- 可通过API查看和恢复已删除数据
- 支持硬删除（永久删除）

### 5. 接口分级管理

#### 页面路由（服务端渲染）
- `GET /` - 首页
- `GET /character/` - 角色列表
- `GET /character/new` - 创建角色页面
- `GET /character/<id>/edit` - 编辑角色页面
- `GET /script/` - 剧本列表
- `GET /script/new` - 创建剧本页面
- `GET /script/<id>/edit` - 编辑剧本页面
- `GET /game/<id>` - 游戏详情页

#### 表单提交路由
- `POST /character/new` - 创建角色
- `POST /character/<id>/edit` - 更新角色
- `POST /character/<id>/delete` - 删除角色
- `POST /character/<id>/restore` - 恢复角色
- `POST /script/new` - 创建剧本
- `POST /script/<id>/edit` - 更新剧本
- `POST /script/<id>/delete` - 删除剧本
- `POST /script/<id>/restore` - 恢复剧本
- `POST /game/new` - 创建游戏
- `POST /game/<id>/delete` - 删除游戏
- `POST /game/<id>/restore` - 恢复游戏

#### AJAX API路由
- `POST /game/<id>/update` - 游戏状态更新（统一接口）
- `GET /api/export/characters` - 导出角色
- `GET /api/export/scripts` - 导出剧本
- `GET /api/export/games` - 导出游戏
- `POST /api/import/characters` - 导入角色
- `GET /api/trash/characters` - 查看已删除角色
- `GET /api/trash/scripts` - 查看已删除剧本
- `GET /api/trash/games` - 查看已删除游戏
- `GET /api/images/<filename>` - 获取图片

## 启动方式

### 开发环境
```bash
cd botc-assistant-py
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app_new.py
```

访问 http://localhost:5555

### 生产环境
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
gunicorn app_new:app -b 0.0.0.0:5555
```

## 数据迁移

首次启动时，系统会自动检测 `data/` 目录下的JSON文件并迁移到数据库：
- `characters.json` → `characters` 表
- `scripts.json` → `scripts` 表
- `games.json` → `games` 表

迁移完成后，旧JSON文件可以保留作为备份。

## 软删除与恢复

### 查看已删除数据
```bash
# 查看已删除角色
curl http://localhost:5555/api/trash/characters

# 查看已删除剧本
curl http://localhost:5555/api/trash/scripts

# 查看已删除游戏
curl http://localhost:5555/api/trash/games
```

### 恢复数据
通过POST请求到对应的restore接口：
```bash
# 恢复角色
curl -X POST http://localhost:5555/character/<id>/restore

# 恢复剧本
curl -X POST http://localhost:5555/script/<id>/restore

# 恢复游戏
curl -X POST http://localhost:5555/game/<id>/restore
```

## 文件存储说明

### 多人使用场景
- 上传的图片保存在 `uploads/images/` 目录
- 该目录应该：
  - 在开发环境：本地存储
  - 在生产环境：使用云存储（如AWS S3、阿里云OSS）
- 文件引用计数自动管理，删除角色时自动清理未使用文件

### 云存储配置（推荐）
生产环境建议使用云存储服务：
1. 配置环境变量指向云存储
2. 修改 `FileService` 使用云存储SDK
3. 图片URL直接使用云存储地址

## 部署到Render.com

1. 推送代码到GitHub
2. 在Render创建Web Service
3. 配置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app_new:app`
   - 环境变量：
     - `FLASK_ENV=production`
     - `SECRET_KEY=<随机字符串>`
     - `DATABASE_URL=<PostgreSQL连接字符串>`（可选）

## 环境变量

- `FLASK_ENV`: 环境（development/production）
- `SECRET_KEY`: 密钥（生产环境必须设置）
- `DATABASE_URL`: 数据库连接字符串
- `PORT`: 端口号（默认5555）
- `FLASK_DEBUG`: 调试模式（True/False）

## 技术栈

- Flask 3.0
- Flask-SQLAlchemy 3.1
- SQLite（开发）/ PostgreSQL（生产）
- Gunicorn（生产服务器）
