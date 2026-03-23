"""数据模型"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SoftDeleteMixin:
    """软删除混入类"""
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def soft_delete(self):
        """软删除"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复"""
        self.deleted_at = None
    
    @property
    def is_deleted(self):
        """是否已删除"""
        return self.deleted_at is not None


class Character(db.Model, SoftDeleteMixin):
    """角色模型"""
    __tablename__ = 'characters'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    type = db.Column(db.String(20), nullable=False, default='townsfolk')
    ability = db.Column(db.Text)
    image = db.Column(db.String(500))
    first_night = db.Column(db.Integer)
    other_nights = db.Column(db.Integer)
    cause_drunk = db.Column(db.Boolean, default=False)
    cause_poison = db.Column(db.Boolean, default=False)
    # 筛选标签（可由 auto_tag() 自动推断，也可手动设置）
    tag_first_night_info = db.Column(db.Boolean, default=False)  # 首夜得知
    tag_first_night_act  = db.Column(db.Boolean, default=False)  # 首夜行动
    tag_every_night      = db.Column(db.Boolean, default=False)  # 每夜行动（含首夜）
    tag_other_nights     = db.Column(db.Boolean, default=False)  # 从第二夜起每夜
    tag_limited          = db.Column(db.Boolean, default=False)  # 限次能力
    tag_gains_ability    = db.Column(db.Boolean, default=False)  # 获得能力
    tag_passive          = db.Column(db.Boolean, default=False)  # 被动能力
    tag_death_trigger    = db.Column(db.Boolean, default=False)  # 死亡触发
    tag_public_trigger   = db.Column(db.Boolean, default=False)  # 公开触发
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'nameEn': self.name_en,
            'type': self.type,
            'ability': self.ability,
            'image': self.image,
            'firstNight': self.first_night,
            'otherNights': self.other_nights,
            'causeDrunk': self.cause_drunk,
            'causePoison': self.cause_poison,
            'tags': {
                'firstNightInfo': self.tag_first_night_info,
                'firstNightAct':  self.tag_first_night_act,
                'everyNight':     self.tag_every_night,
                'otherNights':    self.tag_other_nights,
                'limited':        self.tag_limited,
                'gainsAbility':   self.tag_gains_ability,
                'passive':        self.tag_passive,
                'deathTrigger':   self.tag_death_trigger,
                'publicTrigger':  self.tag_public_trigger,
            },
        }


class Script(db.Model, SoftDeleteMixin):
    """剧本模型"""
    __tablename__ = 'scripts'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    character_ids = db.Column(db.Text)  # JSON 字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'characterIds': json.loads(self.character_ids) if self.character_ids else [],
        }


class Game(db.Model, SoftDeleteMixin):
    """游戏模型"""
    __tablename__ = 'games'
    
    id = db.Column(db.String(50), primary_key=True)
    script_id = db.Column(db.String(50), nullable=False)
    script_name = db.Column(db.String(200))
    seats = db.Column(db.Text)  # JSON 字符串
    days = db.Column(db.Text)  # JSON 字符串
    status = db.Column(db.String(20), default='active')
    winner = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'scriptId': self.script_id,
            'scriptName': self.script_name,
            'seats': json.loads(self.seats) if self.seats else [],
            'days': json.loads(self.days) if self.days else [],
            'status': self.status,
            'winner': self.winner,
            'createdAt': int(self.created_at.timestamp()),
        }


class FileUpload(db.Model):
    """文件上传记录"""
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    original_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_count = db.Column(db.Integer, default=0)  # 引用计数
    
    def increment_reference(self):
        """增加引用计数"""
        self.reference_count += 1
    
    def decrement_reference(self):
        """减少引用计数"""
        if self.reference_count > 0:
            self.reference_count -= 1
