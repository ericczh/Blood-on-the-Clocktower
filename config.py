"""应用配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'botc-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "data" / "botc.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 权限配置
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # 文件上传配置
    UPLOAD_FOLDER = BASE_DIR / 'uploads' / 'images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    
    # 调试模式
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5555))


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
