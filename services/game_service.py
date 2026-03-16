"""游戏服务"""
import json
import uuid
import time
from models import db, Game


class GameService:
    """游戏业务逻辑"""
    
    @staticmethod
    def get_all(include_deleted=False):
        """获取所有游戏"""
        query = Game.query
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.order_by(Game.created_at.desc()).all()
    
    @staticmethod
    def get_by_id(game_id, include_deleted=False):
        """根据ID获取游戏"""
        query = Game.query.filter_by(id=game_id)
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.first()
    
    @staticmethod
    def get_by_status(status, include_deleted=False):
        """根据状态获取游戏"""
        query = Game.query.filter_by(status=status)
        if not include_deleted:
            query = query.filter_by(deleted_at=None)
        return query.order_by(Game.created_at.desc()).all()
    
    @staticmethod
    def create(script_id, script_name, player_count):
        """创建游戏"""
        seats = []
        for i in range(1, player_count + 1):
            seats.append({
                "id": i,
                "playerName": "",
                "characterId": "",
                "alive": True,
                "hasVote": True,
                "drunkPoisoned": False,
                "notes": "",
                "claimedRole": "",
            })
        
        days = [{
            "dayNumber": 0,
            "phase": "night",
            "nightActions": [],
            "nominations": [],
            "deaths": [],
            "notes": ""
        }]
        
        game = Game(
            id=uuid.uuid4().hex[:8],
            script_id=script_id,
            script_name=script_name,
            seats=json.dumps(seats),
            days=json.dumps(days),
            status='active',
        )
        
        db.session.add(game)
        db.session.commit()
        return game
    
    @staticmethod
    def update_seat(game_id, seat_id, data):
        """更新座位信息"""
        game = GameService.get_by_id(game_id)
        if not game:
            return None
        
        seats = json.loads(game.seats)
        for seat in seats:
            if seat['id'] == seat_id:
                for key in ('playerName', 'characterId', 'alive', 'hasVote',
                           'drunkPoisoned', 'notes', 'claimedRole'):
                    if key in data:
                        seat[key] = data[key]
                break
        
        game.seats = json.dumps(seats)
        db.session.commit()
        return game
    
    @staticmethod
    def add_day(game_id):
        """添加新的一天"""
        game = GameService.get_by_id(game_id)
        if not game:
            return None
        
        days = json.loads(game.days)
        day_number = len(days)
        days.append({
            "dayNumber": day_number,
            "phase": "night",
            "nightActions": [],
            "nominations": [],
            "deaths": [],
            "notes": ""
        })
        
        game.days = json.dumps(days)
        db.session.commit()
        return game
    
    @staticmethod
    def update_day(game_id, day_index, data):
        """更新天数信息"""
        game = GameService.get_by_id(game_id)
        if not game:
            return None
        
        days = json.loads(game.days)
        if 0 <= day_index < len(days):
            for key in ('nightActions', 'nominations', 'deaths', 'notes'):
                if key in data:
                    days[day_index][key] = data[key]
        
        game.days = json.dumps(days)
        db.session.commit()
        return game
    
    @staticmethod
    def finish_game(game_id, winner):
        """结束游戏"""
        game = GameService.get_by_id(game_id)
        if not game:
            return None
        
        game.status = 'finished'
        game.winner = winner
        db.session.commit()
        return game
    
    @staticmethod
    def soft_delete(game_id):
        """软删除游戏"""
        game = GameService.get_by_id(game_id)
        if game:
            game.soft_delete()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def restore(game_id):
        """恢复游戏"""
        game = GameService.get_by_id(game_id, include_deleted=True)
        if game and game.is_deleted:
            game.restore()
            db.session.commit()
            return True
        return False
