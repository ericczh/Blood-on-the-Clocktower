"""API路由"""
import re
from flask import jsonify, request, send_from_directory
from routes import api_bp
from services.character_service import CharacterService
from services.script_service import ScriptService
from services.game_service import GameService
from config import Config


@api_bp.route("/export/characters")
def export_characters():
    """导出角色数据"""
    characters = CharacterService.get_all()
    return jsonify([c.to_dict() for c in characters])


@api_bp.route("/export/scripts")
def export_scripts():
    """导出剧本数据"""
    scripts = ScriptService.get_all()
    return jsonify([s.to_dict() for s in scripts])


@api_bp.route("/export/games")
def export_games():
    """导出游戏数据"""
    games = GameService.get_all()
    return jsonify([g.to_dict() for g in games])


@api_bp.route("/import/characters", methods=["POST"])
def import_characters():
    """导入角色数据"""
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"error": "invalid data format"}), 400
    
    imported = 0
    for char_data in data:
        if not CharacterService.get_by_id(char_data.get('id', '')):
            CharacterService.create(char_data)
            imported += 1
    
    return jsonify({"ok": True, "imported": imported})


@api_bp.route("/trash/characters")
def list_deleted_characters():
    """查看已删除的角色"""
    characters = CharacterService.get_all(include_deleted=True)
    deleted = [c.to_dict() for c in characters if c.is_deleted]
    return jsonify(deleted)


@api_bp.route("/trash/scripts")
def list_deleted_scripts():
    """查看已删除的剧本"""
    scripts = ScriptService.get_all(include_deleted=True)
    deleted = [s.to_dict() for s in scripts if s.is_deleted]
    return jsonify(deleted)


@api_bp.route("/trash/games")
def list_deleted_games():
    """查看已删除的游戏"""
    games = GameService.get_all(include_deleted=True)
    deleted = [g.to_dict() for g in games if g.is_deleted]
    return jsonify(deleted)


@api_bp.route("/images/<filename>")
def serve_image(filename):
    """提供图片文件"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@api_bp.route("/characters/<cid>")
def get_character(cid):
    """单个角色详情"""
    character = CharacterService.get_by_id(cid)
    if not character:
        return jsonify({"error": "not found"}), 404
    return jsonify(character.to_dict())


@api_bp.route("/sync/wiki", methods=["POST"])
def sync_from_wiki():
    """从 Wiki 同步角色数据

    支持参数：
      force=1  — 也更新已存在的角色
    """
    force = request.args.get("force", "0") == "1"

    try:
        from utils.wiki_scraper import scrape_all_characters
        from models import db, Character

        chars = scrape_all_characters(delay=0.5)
        imported = updated = skipped = 0

        for c in chars:
            # 生成 ID
            name_en = c.get("name_en", "").strip()
            if name_en:
                cid = re.sub(r"[^a-z0-9]", "", name_en.lower())
            else:
                import hashlib
                cid = "cn_" + hashlib.md5(c["name"].encode()).hexdigest()[:8]

            existing = Character.query.filter_by(id=cid).first()
            if existing:
                if force:
                    existing.name = c["name"]
                    existing.name_en = c.get("name_en", existing.name_en)
                    existing.type = c["type"]
                    if c.get("ability"):
                        existing.ability = c["ability"]
                    if c.get("image"):
                        existing.image = c["image"]
                    existing.deleted_at = None
                    db.session.commit()
                    updated += 1
                else:
                    skipped += 1
                continue

            character = Character(
                id=cid,
                name=c["name"],
                name_en=c.get("name_en", ""),
                type=c["type"],
                ability=c.get("ability", ""),
                image=c.get("image", ""),
            )
            db.session.add(character)
            db.session.commit()
            imported += 1

        return jsonify({
            "ok": True,
            "total": len(chars),
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
        })

    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@api_bp.route("/characters/auto-tag", methods=["POST"])
def auto_tag_all():
    """批量对所有角色自动推断标签（从能力描述文字推断）"""
    try:
        count = CharacterService.bulk_auto_tag()
        return jsonify({"ok": True, "processed": count})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@api_bp.route("/characters/filter")
def filter_characters():
    """多条件筛选角色

    Query params:
      types   — 逗号分隔阵营列表，如 townsfolk,outsider
      firstNightInfo, firstNightAct, everyNight, otherNights,
      limited, gainsAbility, passive, deathTrigger, publicTrigger
               — "1" 表示必须为 True，"0" 表示必须为 False，不传 = 不限制
    """
    TAG_KEYS = [
        'firstNightInfo', 'firstNightAct', 'everyNight', 'otherNights',
        'limited', 'gainsAbility', 'passive', 'deathTrigger', 'publicTrigger',
    ]
    types_str = request.args.get("types", "")
    types = [t.strip() for t in types_str.split(",") if t.strip()] or None

    tags = {}
    for key in TAG_KEYS:
        val = request.args.get(key)
        if val == "1":
            tags[key] = True
        elif val == "0":
            tags[key] = False

    grouped = CharacterService.get_filtered(types=types, tags=tags)
    result = {
        type_key: [c.to_dict() for c in chars]
        for type_key, chars in grouped.items()
    }
    return jsonify(result)


@api_bp.route("/export/characters/<char_type>")
def export_characters_by_type(char_type):
    """按阵营类型导出角色 JSON"""
    from models import Character
    chars = Character.query.filter_by(type=char_type, deleted_at=None).order_by(Character.name).all()
    if not chars:
        return jsonify([])
    return jsonify([c.to_dict() for c in chars])
