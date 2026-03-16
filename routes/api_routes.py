"""API路由"""
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
