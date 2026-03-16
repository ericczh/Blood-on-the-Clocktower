"""路由模块"""
from flask import Blueprint

# 创建蓝图
main_bp = Blueprint('main', __name__)
character_bp = Blueprint('character', __name__, url_prefix='/character')
script_bp = Blueprint('script', __name__, url_prefix='/script')
game_bp = Blueprint('game', __name__, url_prefix='/game')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由
from routes import main_routes, character_routes, script_routes, game_routes, api_routes


def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(main_bp)
    app.register_blueprint(character_bp)
    app.register_blueprint(script_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(api_bp)
