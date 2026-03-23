"""角色服务"""
import re
import uuid
from models import db, Character

# ── 能力文字模式 → 标签推断规则 ──────────────────────────────────────────
# 所有规则均基于简体中文能力描述文本，未来可扩充

# 首夜得知：首个夜晚唤醒且"得知/知道/获悉"
_PAT_FIRST_NIGHT      = re.compile(r"首个夜晚|首夜")
_PAT_FIRST_NIGHT_INFO = re.compile(r"首(个)?夜晚.{0,40}(得知|知道|获悉|告知|了解|看到|看见)")
_PAT_EVERY_NIGHT      = re.compile(r"每(个|天|晚)(夜晚|的夜晚|夜)")
_PAT_OTHER_NIGHTS     = re.compile(r"(非首夜|每个非首夜|每个(你的)?非首夜夜晚|第二夜起|从第二夜)")
_PAT_LIMITED          = re.compile(r"一次|仅限一次|限制.{0,5}次|只能(.{0,5})一次|每局只")
_PAT_GAINS_ABILITY    = re.compile(r"获得.{0,20}(能力|角色|作为)|变成.{0,20}(镇民|外来者|爪牙|恶魔|传奇)|成为.{0,20}角色")
_PAT_PASSIVE          = re.compile(r"永远|被保护|每当|如果(.{0,20})(不死|不能被|不会|不溺死)|不会被杀|不受.{0,10}影响")
_PAT_DEATH_TRIGGER    = re.compile(r"死亡时|被处决时|死去时|临死|将死|死前|当你死(亡|去)")
_PAT_PUBLIC_TRIGGER   = re.compile(r"白天.{0,30}(公开|宣布|选择|指定|宣称)|公开宣称|公开选择|在白天")


def _infer_tags(ability: str) -> dict:
    """从能力描述文本推断布尔标签"""
    if not ability:
        return {}
    t = {}
    t["tag_first_night_info"] = bool(_PAT_FIRST_NIGHT_INFO.search(ability))
    t["tag_first_night_act"]  = bool(_PAT_FIRST_NIGHT.search(ability))
    t["tag_every_night"]      = bool(_PAT_EVERY_NIGHT.search(ability))
    t["tag_other_nights"]     = bool(_PAT_OTHER_NIGHTS.search(ability))
    t["tag_limited"]          = bool(_PAT_LIMITED.search(ability))
    t["tag_gains_ability"]    = bool(_PAT_GAINS_ABILITY.search(ability))
    t["tag_passive"]          = bool(_PAT_PASSIVE.search(ability))
    t["tag_death_trigger"]    = bool(_PAT_DEATH_TRIGGER.search(ability))
    t["tag_public_trigger"]   = bool(_PAT_PUBLIC_TRIGGER.search(ability))
    return t



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
    def get_filtered(types=None, tags=None, include_deleted=False):
        """多条件筛选角色

        Args:
            types: list[str] — 保留的阵营类型，None 表示全部
            tags:  dict     — {tag_field: True/False}，只包含激活的条件
            include_deleted: 是否包含已删除角色

        Returns:
            按类型分组的字典 {type_key: [Character, …]}
        """
        query = Character.query
        if not include_deleted:
            query = query.filter_by(deleted_at=None)

        # 阵营过滤
        if types:
            query = query.filter(Character.type.in_(types))

        # 布尔标签过滤（AND 逻辑）
        TAG_FIELDS = {
            'firstNightInfo': Character.tag_first_night_info,
            'firstNightAct':  Character.tag_first_night_act,
            'everyNight':     Character.tag_every_night,
            'otherNights':    Character.tag_other_nights,
            'limited':        Character.tag_limited,
            'gainsAbility':   Character.tag_gains_ability,
            'passive':        Character.tag_passive,
            'deathTrigger':   Character.tag_death_trigger,
            'publicTrigger':  Character.tag_public_trigger,
        }
        if tags:
            for tag_key, val in tags.items():
                col = TAG_FIELDS.get(tag_key)
                if col is not None and val is not None:
                    query = query.filter(col == bool(val))

        chars = query.order_by(Character.name).all()
        grouped = {}
        for char in chars:
            grouped.setdefault(char.type, []).append(char)
        return grouped

    @staticmethod
    def auto_tag(char_id) -> bool:
        """对单个角色自动推断并保存标签"""
        character = CharacterService.get_by_id(char_id)
        if not character:
            return False
        tags = _infer_tags(character.ability or "")
        for field, val in tags.items():
            setattr(character, field, val)
        db.session.commit()
        return True

    @staticmethod
    def bulk_auto_tag(include_deleted=False) -> int:
        """批量对所有角色重新推断标签，返回处理数量"""
        chars = CharacterService.get_all(include_deleted)
        for character in chars:
            tags = _infer_tags(character.ability or "")
            for field, val in tags.items():
                setattr(character, field, val)
        db.session.commit()
        return len(chars)

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
