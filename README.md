# 血染钟楼 · 说书人助手

一个基于 Flask 的 Web 应用，用于辅助血染钟楼（Blood on the Clocktower）游戏的说书人管理游戏进程。

> **🎉 项目已重构！** 新版本支持数据库、软删除、多人使用等功能。
> 
> - **新用户**：直接使用新版本 → [快速开始](#快速开始新版本)
> - **老用户**：查看 [迁移指南](MIGRATION_GUIDE.md)
> - **开发者**：查看 [架构文档](ARCHITECTURE.md)

## 功能特性

### 基础功能
- 📝 **角色管理** - 创建和编辑游戏角色，支持图片上传和 URL
- 📋 **剧本管理** - 组合不同角色创建自定义游戏剧本
- 🎮 **对局管理** - 创建游戏、分配座位、追踪游戏进程
- 🎯 **可视化座位图** - 圆形布局显示玩家位置和状态
- 🌐 **中文界面** - 完整的中文本地化支持

### 新版本特性 ⭐
- 💾 **数据库支持** - 支持多人并发使用，数据更安全
- 🗑️ **软删除** - 误删除可恢复，数据不丢失
- 📁 **文件管理** - 自动管理上传文件，引用计数清理
- 🏗️ **分层架构** - 代码清晰，易于维护和扩展
- 🔌 **RESTful API** - 规范的接口设计
- 📊 **回收站** - 查看和恢复已删除数据

## 快速开始（新版本）

### 方式一：使用启动脚本（推荐）

**macOS/Linux:**
```bash
cd botc-assistant-py
./start.sh
```

**Windows:**
```bash
cd botc-assistant-py
start.bat
```

### 方式二：手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 迁移数据（首次运行）
python migrate.py

# 5. 启动应用
python app_new.py
```

应用将在 http://localhost:5555 启动

### 旧版本启动（不推荐）

```bash
python app.py  # 旧版本，仅支持单人使用
```

## 使用说明

### 1. 角色管理

访问"角色库"页面，可以：
- 添加新角色（支持上传图片或使用图片 URL）
- 编辑现有角色信息
- 按类型（镇民、外来者、爪牙、恶魔）查看角色

**图片 URL 示例：**
```
https://clocktower-wiki.gstonegames.com/images/thumb/4/45/Washerwoman.png/200px-Washerwoman.png
```

### 2. 剧本管理

访问"板子管理"页面，可以：
- 创建新剧本
- 从角色库中选择角色组合
- 编辑或删除现有剧本

### 3. 开始游戏

在首页：
1. 选择一个剧本
2. 设置玩家人数（5-15人）
3. 点击"开始对局"

### 4. 游戏管理

在游戏页面，可以：
- 点击座位分配角色和玩家信息
- 标记玩家状态（存活/死亡、醉/毒）
- 记录每轮游戏备注
- 结束游戏并记录胜负

## 技术栈

- **后端**: Flask 3.0 + Flask-SQLAlchemy 3.1
- **前端**: Tailwind CSS + 原生 JavaScript
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **模板引擎**: Jinja2
- **生产服务器**: Gunicorn

## 项目结构（新版本）

```
botc-assistant-py/
├── app_new.py              # 新版应用入口 ⭐
├── app.py                  # 旧版应用（保留）
├── config.py               # 配置管理
├── models.py               # 数据模型
├── routes/                 # 路由层
│   ├── main_routes.py
│   ├── character_routes.py
│   ├── script_routes.py
│   ├── game_routes.py
│   └── api_routes.py
├── services/               # 业务逻辑层
│   ├── character_service.py
│   ├── script_service.py
│   ├── game_service.py
│   └── file_service.py
├── utils/                  # 工具函数
├── data/                   # 数据目录
│   ├── botc.db            # 数据库文件
│   └── *.json             # 旧数据（备份）
├── uploads/                # 上传文件目录
│   └── images/
├── templates/              # HTML 模板
├── static/                 # 静态资源
└── 文档/
    ├── README_NEW.md
    ├── QUICKSTART.md
    ├── ARCHITECTURE.md
    └── ...
```

## 开发说明

### 关于模板文件的"错误"

如果你在 IDE 中看到 `templates/game.html` 等文件有语法错误提示，这是正常的。这些"错误"是因为 IDE 的语言服务器无法识别 Jinja2 模板语法（如 `{{ variable }}` 和 `{% if %}`）。

这些不是真正的错误，Flask 会在服务器端正确渲染这些模板。应用运行完全正常。

### API 接口

#### 游戏更新接口

```
POST /game/<game_id>/update
Content-Type: application/json

{
  "action": "update_seat",  // 或 "add_day", "update_day", "finish"
  "seatId": 1,
  "playerName": "玩家名",
  // ... 其他数据
}
```

## 数据格式

### 角色数据结构

```json
{
  "id": "washerwoman",
  "name": "洗衣妇",
  "nameEn": "Washerwoman",
  "type": "townsfolk",
  "ability": "你在首个夜晚会得知2名玩家中有1名特定的镇民角色。",
  "firstNight": 1,
  "image": "https://example.com/image.png"
}
```

### 剧本数据结构

```json
{
  "id": "tb",
  "name": "暗流涌动 (Trouble Brewing)",
  "characterIds": ["washerwoman", "librarian", "..."]
}
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 📚 文档导航

- **[快速开始](QUICKSTART.md)** - 5分钟上手指南
- **[新版说明](README_NEW.md)** - 详细的使用文档
- **[迁移指南](MIGRATION_GUIDE.md)** - 从旧版本迁移
- **[新旧对比](COMPARISON.md)** - 功能对比和优势
- **[架构设计](ARCHITECTURE.md)** - 开发者文档
- **[项目总结](PROJECT_SUMMARY.md)** - 重构完成情况
- **[文档索引](INDEX.md)** - 所有文档列表

## 🆕 新版本亮点

### 1. 支持多人使用
- ✅ 数据库事务保证数据一致性
- ✅ 支持并发访问
- ✅ 不再有文件冲突问题

### 2. 软删除与恢复
```bash
# 查看已删除的角色
curl http://localhost:5555/api/trash/characters

# 恢复已删除的角色
curl -X POST http://localhost:5555/character/<id>/restore
```

### 3. 文件管理优化
- 上传文件独立存储在 `uploads/` 目录
- 引用计数自动管理
- 自动清理未使用文件

### 4. 清晰的代码架构
- 路由层：处理HTTP请求
- 服务层：封装业务逻辑
- 模型层：数据库映射
- 易于维护和扩展

## 🔄 版本对比

| 功能 | 旧版本 | 新版本 |
|------|--------|--------|
| 数据存储 | JSON文件 | 数据库 |
| 多人使用 | ❌ | ✅ |
| 软删除 | ❌ | ✅ |
| 文件管理 | 手动 | 自动 |
| 代码结构 | 单文件 | 分层架构 |

## 相关链接

- [血染钟楼官网](https://bloodontheclocktower.com/)
- [血染钟楼 Wiki](https://clocktower-wiki.gstonegames.com/)
- [项目文档](INDEX.md)
