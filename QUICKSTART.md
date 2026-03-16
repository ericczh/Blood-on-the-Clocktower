# 快速开始指南

## 🚀 5分钟上手新版本

### 方式一：使用启动脚本（推荐）

#### macOS/Linux
```bash
cd botc-assistant-py
./start.sh
```

#### Windows
```bash
cd botc-assistant-py
start.bat
```

启动脚本会自动：
1. 创建虚拟环境
2. 安装依赖
3. 迁移数据（首次运行）
4. 启动应用

### 方式二：手动启动

```bash
# 1. 进入项目目录
cd botc-assistant-py

# 2. 创建虚拟环境（首次）
python3 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 4. 安装依赖
pip install -r requirements.txt

# 5. 迁移数据（首次运行）
python migrate.py

# 6. 启动应用
python app_new.py
```

### 访问应用

打开浏览器访问：http://localhost:5555

## 📋 功能测试清单

### 1. 角色管理
- [ ] 查看角色列表
- [ ] 创建新角色（上传图片）
- [ ] 编辑角色
- [ ] 删除角色
- [ ] 恢复已删除角色（访问 `/api/trash/characters`）

### 2. 剧本管理
- [ ] 查看剧本列表
- [ ] 创建新剧本
- [ ] 编辑剧本
- [ ] 删除剧本
- [ ] 恢复已删除剧本

### 3. 游戏管理
- [ ] 创建新游戏
- [ ] 查看游戏详情
- [ ] 更新座位信息
- [ ] 添加新的一天
- [ ] 结束游戏
- [ ] 删除游戏
- [ ] 恢复已删除游戏

### 4. API测试
```bash
# 运行API测试脚本
python test_api.py
```

## 🔍 验证数据迁移

### 检查数据库
```bash
# 查看数据库文件
ls -lh data/botc.db

# 使用SQLite命令行（可选）
sqlite3 data/botc.db
> .tables
> SELECT COUNT(*) FROM characters;
> SELECT COUNT(*) FROM scripts;
> SELECT COUNT(*) FROM games;
> .quit
```

### 检查API
```bash
# 导出角色数据
curl http://localhost:5555/api/export/characters | python -m json.tool

# 导出剧本数据
curl http://localhost:5555/api/export/scripts | python -m json.tool

# 导出游戏数据
curl http://localhost:5555/api/export/games | python -m json.tool
```

## 🗑️ 测试软删除功能

### 1. 删除一个角色
在浏览器中删除任意角色

### 2. 查看回收站
```bash
curl http://localhost:5555/api/trash/characters | python -m json.tool
```

### 3. 恢复角色
```bash
# 替换 <id> 为实际的角色ID
curl -X POST http://localhost:5555/character/<id>/restore
```

## 📁 文件结构说明

```
botc-assistant-py/
├── app_new.py              # 新版应用入口 ⭐
├── config.py               # 配置文件
├── models.py               # 数据模型
├── routes/                 # 路由层
│   ├── main_routes.py      # 主页
│   ├── character_routes.py # 角色管理
│   ├── script_routes.py    # 剧本管理
│   ├── game_routes.py      # 游戏管理
│   └── api_routes.py       # API接口
├── services/               # 业务逻辑层
│   ├── character_service.py
│   ├── script_service.py
│   ├── game_service.py
│   └── file_service.py
├── utils/                  # 工具函数
│   └── constants.py
├── data/                   # 数据目录
│   ├── botc.db            # 数据库文件（自动生成）
│   ├── characters.json    # 旧数据（备份）
│   ├── scripts.json       # 旧数据（备份）
│   └── games.json         # 旧数据（备份）
├── uploads/               # 上传文件目录（自动生成）
│   └── images/
├── templates/             # HTML模板
├── static/                # 静态资源
├── migrate.py             # 数据迁移脚本
├── test_api.py            # API测试脚本
├── cleanup.py             # 清理脚本
├── start.sh               # 启动脚本（macOS/Linux）
├── start.bat              # 启动脚本（Windows）
└── 文档/
    ├── README_NEW.md           # 使用说明
    ├── ARCHITECTURE.md         # 架构设计
    ├── MIGRATION_GUIDE.md      # 迁移指南
    ├── COMPARISON.md           # 新旧对比
    ├── REFACTORING_SUMMARY.md  # 重构总结
    └── QUICKSTART.md           # 本文件
```

## ⚠️ 常见问题

### Q1: 启动失败，提示模块未找到
```bash
# 确保激活了虚拟环境
source .venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: 数据库文件在哪里？
```bash
# 数据库文件位置
data/botc.db

# 如果不存在，运行迁移脚本
python migrate.py
```

### Q3: 旧数据会丢失吗？
不会！旧的JSON文件会保留在 `data/` 目录作为备份。

### Q4: 如何切换回旧版本？
```bash
# 使用旧版本
python app.py

# 旧数据文件仍然存在，可以直接使用
```

### Q5: 上传的图片在哪里？
```bash
# 新版本图片位置
uploads/images/

# 旧版本图片位置（仍然可用）
data/images/
```

### Q6: 如何清理缓存文件？
```bash
python cleanup.py
```

## 🎯 下一步

### 基础使用
1. ✅ 完成快速开始
2. ✅ 测试所有功能
3. ✅ 验证数据完整性

### 进阶配置
1. 配置生产环境数据库
2. 集成云存储
3. 添加用户认证
4. 部署到云平台

### 开发扩展
1. 阅读架构文档
2. 了解分层设计
3. 添加自定义功能
4. 编写单元测试

## 📚 文档导航

- **新手**：先看本文件（QUICKSTART.md）
- **使用**：查看 README_NEW.md
- **迁移**：查看 MIGRATION_GUIDE.md
- **对比**：查看 COMPARISON.md
- **开发**：查看 ARCHITECTURE.md
- **总结**：查看 REFACTORING_SUMMARY.md

## 💡 提示

- 首次运行会自动迁移数据，请耐心等待
- 建议在测试环境先验证功能
- 生产环境请配置环境变量
- 定期备份数据库文件

## 🆘 获取帮助

如遇问题：
1. 查看文档中的常见问题
2. 检查日志输出
3. 查看代码注释
4. 提交Issue

---

**祝使用愉快！** 🎉
