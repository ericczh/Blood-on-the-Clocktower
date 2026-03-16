"""数据迁移脚本

从旧的JSON文件迁移数据到新的数据库系统
"""
import json
from pathlib import Path
from app_new import create_app
from models import db, Character, Script, Game


def migrate_data():
    """执行数据迁移"""
    app = create_app('development')
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        data_dir = Path(__file__).parent / 'data'
        
        # 迁移角色
        print("正在迁移角色数据...")
        char_file = data_dir / 'characters.json'
        if char_file.exists():
            chars = json.loads(char_file.read_text('utf-8'))
            migrated = 0
            for c in chars:
                # 检查是否已存在
                if not Character.query.filter_by(id=c.get('id')).first():
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
                    migrated += 1
            db.session.commit()
            print(f"✓ 成功迁移 {migrated} 个角色")
        else:
            print("✗ 未找到 characters.json")
        
        # 迁移剧本
        print("\n正在迁移剧本数据...")
        script_file = data_dir / 'scripts.json'
        if script_file.exists():
            scripts = json.loads(script_file.read_text('utf-8'))
            migrated = 0
            for s in scripts:
                if not Script.query.filter_by(id=s.get('id')).first():
                    script = Script(
                        id=s.get('id'),
                        name=s.get('name'),
                        character_ids=json.dumps(s.get('characterIds', [])),
                    )
                    db.session.add(script)
                    migrated += 1
            db.session.commit()
            print(f"✓ 成功迁移 {migrated} 个剧本")
        else:
            print("✗ 未找到 scripts.json")
        
        # 迁移游戏
        print("\n正在迁移游戏数据...")
        game_file = data_dir / 'games.json'
        if game_file.exists():
            games = json.loads(game_file.read_text('utf-8'))
            migrated = 0
            for g in games:
                if not Game.query.filter_by(id=g.get('id')).first():
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
                    migrated += 1
            db.session.commit()
            print(f"✓ 成功迁移 {migrated} 个游戏")
        else:
            print("✗ 未找到 games.json")
        
        # 统计信息
        print("\n" + "="*50)
        print("迁移完成！数据库统计：")
        print(f"  角色总数: {Character.query.count()}")
        print(f"  剧本总数: {Script.query.count()}")
        print(f"  游戏总数: {Game.query.count()}")
        print("="*50)


if __name__ == '__main__':
    migrate_data()
