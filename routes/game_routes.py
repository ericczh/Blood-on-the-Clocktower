"""游戏路由"""
import math
from flask import render_template, request, redirect, url_for, jsonify, flash
from routes import game_bp
from services.game_service import GameService
from services.script_service import ScriptService
from services.character_service import CharacterService
from utils.constants import TYPE_LABELS, DISTRIBUTION


@game_bp.route("/new", methods=["POST"])
def create_game():
    """创建游戏"""
    script_id = request.form.get('script_id')
    player_count = int(request.form.get('player_count', 7))
    
    script = ScriptService.get_by_id(script_id)
    if not script:
        flash('剧本不存在', 'error')
        return redirect(url_for("main.index"))
    
    game = GameService.create(script_id, script.name, player_count)
    return redirect(url_for("game.view_game", gid=game.id))


@game_bp.route("/<gid>")
def view_game(gid):
    """查看游戏"""
    game = GameService.get_by_id(gid)
    if not game:
        flash('游戏不存在', 'error')
        return redirect(url_for("main.index"))
    
    characters = CharacterService.get_all()
    char_map = {c.id: c for c in characters}
    
    script = ScriptService.get_by_id(game.script_id)
    script_chars = []
    if script:
        script_dict = script.to_dict()
        script_chars = [
            char_map[cid] for cid in script_dict['characterIds']
            if cid in char_map
        ]
    
    # 按类型分组
    grouped_chars = {}
    for c in script_chars:
        grouped_chars.setdefault(c.type, []).append(c)
    
    game_dict = game.to_dict()
    dist = DISTRIBUTION.get(len(game_dict['seats']))
    
    return render_template(
        "game.html",
        game=game_dict,
        char_map=char_map,
        grouped_chars=grouped_chars,
        type_labels=TYPE_LABELS,
        dist=dist,
        cos=math.cos,
        sin=math.sin
    )


@game_bp.route("/<gid>/update", methods=["POST"])
def update_game(gid):
    """更新游戏（AJAX接口）"""
    data = request.get_json(force=True)
    action = data.get('action')
    
    if action == 'update_seat':
        game = GameService.update_seat(gid, data['seatId'], data)
    elif action == 'add_day':
        game = GameService.add_day(gid)
    elif action == 'update_day':
        game = GameService.update_day(gid, data.get('dayIndex', 0), data)
    elif action == 'finish':
        game = GameService.finish_game(gid, data.get('winner', ''))
    else:
        return jsonify({"error": "unknown action"}), 400
    
    if not game:
        return jsonify({"error": "game not found"}), 404
    
    return jsonify({"ok": True})


@game_bp.route("/<gid>/delete", methods=["POST"])
def delete_game(gid):
    """软删除游戏"""
    if GameService.soft_delete(gid):
        flash('游戏已删除（可恢复）', 'success')
    else:
        flash('删除失败', 'error')
    return redirect(url_for("main.index"))


@game_bp.route("/<gid>/restore", methods=["POST"])
def restore_game(gid):
    """恢复游戏"""
    if GameService.restore(gid):
        flash('游戏已恢复', 'success')
    else:
        flash('恢复失败', 'error')
    return redirect(url_for("main.index"))
