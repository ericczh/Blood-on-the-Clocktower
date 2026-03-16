"""API测试脚本"""
import requests
import json

BASE_URL = "http://localhost:5555"


def test_export_apis():
    """测试导出API"""
    print("测试导出API...")
    
    # 导出角色
    resp = requests.get(f"{BASE_URL}/api/export/characters")
    print(f"✓ 导出角色: {len(resp.json())} 个")
    
    # 导出剧本
    resp = requests.get(f"{BASE_URL}/api/export/scripts")
    print(f"✓ 导出剧本: {len(resp.json())} 个")
    
    # 导出游戏
    resp = requests.get(f"{BASE_URL}/api/export/games")
    print(f"✓ 导出游戏: {len(resp.json())} 个")


def test_trash_apis():
    """测试回收站API"""
    print("\n测试回收站API...")
    
    # 查看已删除角色
    resp = requests.get(f"{BASE_URL}/api/trash/characters")
    print(f"✓ 已删除角色: {len(resp.json())} 个")
    
    # 查看已删除剧本
    resp = requests.get(f"{BASE_URL}/api/trash/scripts")
    print(f"✓ 已删除剧本: {len(resp.json())} 个")
    
    # 查看已删除游戏
    resp = requests.get(f"{BASE_URL}/api/trash/games")
    print(f"✓ 已删除游戏: {len(resp.json())} 个")


def test_soft_delete():
    """测试软删除功能"""
    print("\n测试软删除功能...")
    
    # 创建测试角色
    test_char = {
        "id": "test_char",
        "name": "测试角色",
        "type": "townsfolk",
        "ability": "测试能力"
    }
    
    # 注意：这里需要通过表单提交，实际测试时需要使用浏览器或模拟表单
    print("提示：软删除测试需要通过Web界面进行")


if __name__ == '__main__':
    try:
        test_export_apis()
        test_trash_apis()
        print("\n✓ 所有API测试通过！")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
