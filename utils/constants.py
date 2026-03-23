"""常量定义"""

TYPE_LABELS = {
    "townsfolk": "镇民",
    "outsider": "外来者",
    "minion": "爪牙",
    "demon": "恶魔",
    "traveller": "旅行者",
    "fabled": "传奇",
    "fabled2": "奇遇角色",
}

# Wiki 分类页面 URL 片段 → 角色类型键
WIKI_CATEGORIES = {
    "%E9%95%87%E6%B0%91": "townsfolk",          # 镇民
    "%E5%A4%96%E6%9D%A5%E8%80%85": "outsider",  # 外来者
    "%E7%88%AA%E7%89%99": "minion",              # 爪牙
    "%E6%81%B6%E9%AD%94": "demon",               # 恶魔
    "%E6%97%85%E8%A1%8C%E8%80%85": "traveller", # 旅行者
    "%E4%BC%A0%E5%A5%87%E8%A7%92%E8%89%B2": "fabled",  # 传奇角色
}

WIKI_BASE = "https://clocktower-wiki.gstonegames.com"

DISTRIBUTION = {
    5: [3, 0, 1, 1],
    6: [3, 1, 1, 1],
    7: [5, 0, 1, 1],
    8: [5, 1, 1, 1],
    9: [5, 2, 1, 1],
    10: [7, 0, 2, 1],
    11: [7, 1, 2, 1],
    12: [7, 2, 2, 1],
    13: [9, 0, 3, 1],
    14: [9, 1, 3, 1],
    15: [9, 2, 3, 1],
}
