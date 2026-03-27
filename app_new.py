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
        # 迁移旧数据（如果需要）
        _migrate_old_data()
    
    # 确保上传目录存在
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    return app


def _migrate_old_data():
    """从JSON文件迁移数据到数据库"""
    from pathlib import Path
    import json
    from models import Character, Script, Game
    
    data_dir = Path(__file__).parent / 'data'
    
    # 迁移角色
    char_file = data_dir / 'characters.json'
    if char_file.exists() and Character.query.count() == 0:
        chars = json.loads(char_file.read_text('utf-8'))
        for c in chars:
            character = Character(
                id=c.get('id'),
                name=c.get('name'),
                name_en=c.get('nameEn'),
                type=c.get('type', 'townsfolk'),
                ability=c.get('ability'),
                image=c.get('image'),
                first_night=c.get('firstNight'),
                other_nights=c.get('otherNights'),
                cause_drunk=c.get('causeDrunk', False),
                cause_poison=c.get('causePoison', False),
            )
            db.session.add(character)
        db.session.commit()
        print(f"✓ 迁移了 {len(chars)} 个角色")
    
    # 迁移剧本
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
        print(f"✓ 迁移了 {len(scripts)} 个剧本")
    
    # 迁移游戏
    game_file = data_dir / 'games.json'
    if game_file.exists() and Game.query.count() == 0:
        games = json.loads(game_file.read_text('utf-8'))
        for g in games:
            game = Game(
                id=g.get('id'),
                script_id=g.get('scriptId'),
                script_name=g.get('scriptName'),
                seats=json.dumps(g.get('seats', [])),
                days=json.dumps(g.get('days', [])),
                status=g.get('status', 'active'),
                winner=g.get('winner'),
            )
            db.session.add(game)
        db.session.commit()
        print(f"✓ 迁移了 {len(games)} 个游戏")


if __name__ == "__main__":
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
