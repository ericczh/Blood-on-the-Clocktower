"""主页路由"""
from flask import render_template
from routes import main_bp
from services.game_service import GameService
from services.script_service import ScriptService
from services.character_service import CharacterService
from utils.constants import TYPE_LABELS


@main_bp.route("/")
def index():
    """首页"""
    active_games = GameService.get_by_status('active')
    finished_games = GameService.get_by_status('finished')
    scripts = ScriptService.get_all()
    grouped = CharacterService.get_grouped()

    return render_template(
        "index.html",
        active=[g.to_dict() for g in active_games],
        finished=[g.to_dict() for g in finished_games],
        scripts=[s.to_dict() for s in scripts],
        grouped=grouped,
        type_labels=TYPE_LABELS,
    )
