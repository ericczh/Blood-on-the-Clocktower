"""血染钟楼 · 说书人助手 — Flask 重构版

启动方式：
  cd /Users/wikiglobal/others/botc-assistant-py
  source .venv/bin/activate
  python app_new.py
  # 访问 http://localhost:5555

部署方式（Cloudflare Tunnel）：
  1. brew install cloudflared（仅首次）
  2. python app_new.py                              # 启动 Flask
  3. cloudflared tunnel --url http://localhost:5555  # 新终端启动隧道
  4. 隧道会分配一个 https://xxx.trycloudflare.com 公网地址
  5. 手机（5G/WiFi）直接访问该地址即可
"""
import os
from flask import Flask
from config import config, Config
from models import db
from routes import register_blueprints


def create_app(config_name='default'):
    """应用工厂"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册路由
    register_blueprints(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 导入默认剧本种子数据（仅首次）
        _seed_default_scripts()
    
    # 确保上传目录存在
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    return app


def _seed_default_scripts():
    """首次启动时从 scripts.json 导入默认剧本。"""
    from pathlib import Path
    import json
    from models import Script
    
    data_dir = Path(__file__).parent / 'data'

    script_file = data_dir / 'scripts.json'
    if script_file.exists() and Script.query.count() == 0:
        scripts = json.loads(script_file.read_text('utf-8'))
        for s in scripts:
            script = Script(
                id=s.get('id'),
                name=s.get('name'),
                character_ids=json.dumps(s.get('characterIds', [])),
            )
            db.session.add(script)
        db.session.commit()
        print(f"✓ 导入了 {len(scripts)} 个默认剧本")


if __name__ == "__main__":
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
