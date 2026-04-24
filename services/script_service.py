"""剧本服务"""
import json
import uuid
from models import db, Script


class ScriptService:
    """剧本业务逻辑"""
    
    @staticmethod
    def get_all(include_deleted=False):
        """获取所有剧本"""
        query = Script.query
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.order_by(Script.created_at.desc()).all()

    @staticmethod
    def filter_by_character_ids(character_ids, include_deleted=False, match="all"):
        """按角色筛选剧本。"""
        scripts = ScriptService.get_all(include_deleted=include_deleted)
        wanted = [cid for cid in character_ids if cid]
        if not wanted:
            return scripts

        result = []
        for script in scripts:
            script_ids = set(script.to_dict().get("characterIds", []))
            if match == "any":
                ok = any(cid in script_ids for cid in wanted)
            else:
                ok = all(cid in script_ids for cid in wanted)
            if ok:
                result.append(script)
        return result
    
    @staticmethod
    def get_by_id(script_id, include_deleted=False):
        """根据ID获取剧本"""
        query = Script.query.filter_by(id=script_id)
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.first()
    
    @staticmethod
    def create(name, character_ids):
        """创建剧本"""
        script = Script(
            id=uuid.uuid4().hex[:8],
            name=name,
            character_ids=json.dumps(character_ids),
        )
        db.session.add(script)
        db.session.commit()
        return script
    
    @staticmethod
    def update(script_id, name=None, character_ids=None):
        """更新剧本"""
        script = ScriptService.get_by_id(script_id)
        if not script:
            return None
        
        if name is not None:
            script.name = name
        if character_ids is not None:
            script.character_ids = json.dumps(character_ids)
        
        db.session.commit()
        return script
    
    @staticmethod
    def soft_delete(script_id):
        """软删除剧本"""
        script = ScriptService.get_by_id(script_id)
        if script:
            script.soft_delete()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def restore(script_id):
        """恢复剧本"""
        script = ScriptService.get_by_id(script_id, include_deleted=True)
        if script and script.is_deleted:
            script.restore()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def hard_delete(script_id):
        """硬删除剧本"""
        script = ScriptService.get_by_id(script_id, include_deleted=True)
        if script:
            db.session.delete(script)
            db.session.commit()
            return True
        return False
