# 迁移指南

## 从旧版本迁移到新版本

### 1. 备份数据

在迁移前，请先备份现有数据：

```bash
cp -r data data_backup
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行迁移脚本

```bash
python migrate.py
```

迁移脚本会：
- 创建新的数据库表结构
- 从 `data/*.json` 文件读取数据
- 将数据导入到SQLite数据库
- 显示迁移统计信息

### 4. 启动新版应用

```bash
python app_new.py
```

### 5. 验证数据

访问 http://localhost:5555 检查：
- 角色列表是否完整
- 剧本列表是否完整
- 游戏记录是否完整

### 6. 测试新功能

#### 软删除测试
1. 删除一个角色/剧本/游戏
2. 访问 `/api/trash/characters` 查看已删除项
3. 使用恢复功能恢复数据

#### 文件上传测试
1. 创建新角色并上传图片
2. 检查 `uploads/images/` 目录
3. 删除角色，确认文件引用计数正常

### 7. 切换到新版本

确认一切正常后：

```bash
# 备份旧版本
mv app.py app_old.py

# 使用新版本
mv app_new.py app.py
```

或者直接使用 `app_new.py` 启动。

## 新旧版本对比

| 功能 | 旧版本 | 新版本 |
|------|--------|--------|
| 数据存储 | JSON文件 | SQLite/PostgreSQL |
| 文件存储 | data/images/ | uploads/images/ |
| 删除方式 | 硬删除 | 软删除（可恢复） |
| 代码结构 | 单文件 | 分层架构 |
| 接口管理 | 混合 | 分级清晰 |
| 多人使用 | 不支持 | 支持（数据库） |
| 文件管理 | 手动 | 引用计数自动管理 |

## 回滚到旧版本

如果需要回滚：

```bash
# 恢复旧版本
mv app_old.py app.py

# 数据已在JSON文件中，无需额外操作
```

## 常见问题

### Q: 迁移后旧的JSON文件还需要吗？
A: 建议保留作为备份，新版本不再使用这些文件。

### Q: 上传的图片需要迁移吗？
A: 不需要，图片路径在数据库中保持不变。

### Q: 如何清理未使用的图片？
A: 使用 `FileService.cleanup_unused_files()` 方法。

### Q: 生产环境如何部署？
A: 参考 README_NEW.md 中的部署章节。

### Q: 如何导出数据？
A: 访问 `/api/export/characters`、`/api/export/scripts`、`/api/export/games`。
