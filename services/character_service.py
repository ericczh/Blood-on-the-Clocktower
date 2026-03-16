"""角色服务"""
import uuid
from models import db, Character


class CharacterService:
    """角色业务逻辑"""
    
    @staticmethod
    def get_all(include_deleted=False):
        """获取所有角色"""
        query = Character.query
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.order_by(Character.created_at.desc()).all()
    
    @staticmethod
    def get_by_id(char_id, include_deleted=False):
        """根据ID获取角色"""
        query = Character.query.filter_by(id=char_id)
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.first()
    
    @staticmethod
    def get_grouped(include_deleted=False):
        """按类型分组获取角色"""
        chars = CharacterService.get_all(include_deleted)
        grouped = {}
        for char in chars:
            grouped.setdefault(char.type, []).append(char)
        return grouped
    
    @staticmethod
    def create(data):
        """创建角色"""
        char_id = data.get('id') or uuid.uuid4().hex[:8]
        
        # 检查ID是否已存在
        if Character.query.filter_by(id=char_id).first():
            char_id = f"{char_id}_{uuid.uuid4().hex[:4]}"
        
        character = Character(
            id=char_id,
            name=data.get('name', ''),
            name_en=data.get('nameEn', ''),
            type=data.get('type', 'townsfolk'),
            ability=data.get('ability', ''),
            image=data.get('image', ''),
            first_night=data.get('firstNight'),
            other_nights=data.get('otherNights'),
            cause_drunk=data.get('causeDrunk', False),
            cause_poison=data.get('causePoison', False),
        )
        
        db.session.add(character)
        db.session.commit()
        return character
    
    @staticmethod
    def update(char_id, data):
        """更新角色"""
        character = CharacterService.get_by_id(char_id)
        if not character:
            return None
        
        character.name = data.get('name', character.name)
        character.name_en = data.get('nameEn', character.name_en)
        character.type = data.get('type', character.type)
        character.ability = data.get('ability', character.ability)
        character.image = data.get('image', character.image)
        character.first_night = data.get('firstNight', character.first_night)
        character.other_nights = data.get('otherNights', character.other_nights)
        character.cause_drunk = data.get('causeDrunk', character.cause_drunk)
        character.cause_poison = data.get('causePoison', character.cause_poison)
        
        db.session.commit()
        return character
    
    @staticmethod
    def soft_delete(char_id):
        """软删除角色"""
        character = CharacterService.get_by_id(char_id)
        if character:
            character.soft_delete()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def restore(char_id):
        """恢复角色"""
        character = CharacterService.get_by_id(char_id, include_deleted=True)
        if character and character.is_deleted:
            character.restore()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def hard_delete(char_id):
        """硬删除角色"""
        character = CharacterService.get_by_id(char_id, include_deleted=True)
        if character:
            db.session.delete(character)
            db.session.commit()
            return True
        return False
